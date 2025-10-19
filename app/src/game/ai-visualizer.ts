import * as ort from "onnxruntime-web";
import { Application } from "pixi.js";
import { createRenderObjects, renderState } from "./renderer";
import { DodgerCore, type Action, type GameState } from "@shared/core";

const MAX_BLOCKS = 28;
const ACTIONS: Action[] = ["LEFT", "RIGHT", "NONE"];
const FIXED_DT = 1 / 60;

const MIN_WIDTH = 360;
const MAX_WIDTH = 2400;
const MIN_HEIGHT = 500;
const MAX_HEIGHT = 1200;

let session: ort.InferenceSession | null = null;

ort.env.wasm.wasmPaths = "https://cdn.jsdelivr.net/npm/onnxruntime-web/dist/";

async function initModel() {
  if (session) return;
  session = await ort.InferenceSession.create("/dodger_model_test.onnx");
  console.log(
    "Model loaded. Inputs:",
    session.inputNames,
    "Outputs:",
    session.outputNames
  );
}

function processState(
  state: GameState,
  width: number,
  height: number
): Float32Array {
  const obsSize = 3 + 2 * MAX_BLOCKS;
  const obs = new Float32Array(obsSize);

  obs[0] = state.playerX / MAX_WIDTH;
  obs[1] = (height - MIN_HEIGHT) / (MAX_HEIGHT - MIN_HEIGHT);
  obs[2] = (width - MIN_WIDTH) / (MAX_WIDTH - MIN_WIDTH);

  const playerY = height - 20 - 10;
  const sortedBlocks = [...state.blocks].sort(
    (a, b) => Math.abs(a.y - playerY) - Math.abs(b.y - playerY)
  );

  for (let i = 0; i < Math.min(MAX_BLOCKS, sortedBlocks.length); i++) {
    const block = sortedBlocks[i];
    const dx = (block.x - state.playerX) / MAX_WIDTH + 0.5;
    const dy = Math.abs(playerY - block.y) / MAX_HEIGHT;

    obs[3 + 2 * i] = dx;
    obs[3 + 2 * i + 1] = dy;
  }

  return obs;
}

async function predict(obs: Float32Array): Promise<number> {
  if (!session) throw new Error("Model not loaded");

  const tensor = new ort.Tensor("float32", obs, [1, 59]);
  const feeds = { observation: tensor };
  const results = await session.run(feeds);

  const logits = Array.from(results.action_logits.data as Float32Array);

  console.log("Action logits:", logits);

  if (logits.some(isNaN)) {
    console.error("NaN detected in logits, returning default action.");
    return 2;
  }

  return logits.indexOf(Math.max(...logits));
}

export async function startVisualizer(app: Application) {
  await initModel();

  const width = app.screen.width;
  const height = app.screen.height;
  const game = new DodgerCore(width, height);
  const render = createRenderObjects(app);

  let isPaused = false;
  let isProcessing = false;

  app.ticker.maxFPS = 60;

  const tickerFn = async () => {
    if (isPaused || isProcessing) return;
    isProcessing = true;

    const state = game.getState();
    const obs = processState(state, width, height);

    const actionIdx = await predict(obs);
    const action = ACTIONS[actionIdx];

    game.step(action, FIXED_DT);
    const newState = game.getState();
    renderState(app, render, newState);

    if (newState.gameOver) {
      game.step("RESTART", FIXED_DT);
    }

    isProcessing = false;
  };

  app.ticker.add(tickerFn);

  return {
    cleanup: () => {
      app.ticker.remove(tickerFn);
    },
    pause: () => {
      isPaused = true;
      game.pause();
    },
    resume: () => {
      isPaused = false;
      game.resume();
    },
  };
}
