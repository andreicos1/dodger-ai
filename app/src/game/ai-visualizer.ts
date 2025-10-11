import * as ort from "onnxruntime-web";
import { Application } from "pixi.js";
import { createRenderObjects, renderState } from "./renderer";
import { DodgerCore, type Action, type GameState } from "@shared/core";

const N_STACK = 4;
const MAX_BLOCKS = 10;
const ACTIONS: Action[] = ["LEFT", "RIGHT", "NONE"];
const FIXED_DT = 1 / 60;

let session: ort.InferenceSession | null = null;

ort.env.wasm.wasmPaths = "https://cdn.jsdelivr.net/npm/onnxruntime-web/dist/";

async function initModel() {
  if (session) return;
  session = await ort.InferenceSession.create("/dodger_model.onnx");
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
  const obsSize = 1 + 3 * MAX_BLOCKS;
  const obs = new Float32Array(obsSize);

  obs[0] = state.playerX / (width / 2) - 1.0;

  const playerY = height - 20 - 10;
  const sortedBlocks = [...state.blocks].sort(
    (a, b) => Math.abs(a.y - playerY) - Math.abs(b.y - playerY)
  );

  for (let i = 0; i < Math.min(MAX_BLOCKS, sortedBlocks.length); i++) {
    const block = sortedBlocks[i];
    const dx = (block.x - state.playerX) / width;
    const dy = (playerY - block.y) / height;
    const blockXNorm = block.x / (width / 2) - 1.0;

    obs[1 + 3 * i] = dx;
    obs[1 + 3 * i + 1] = dy;
    obs[1 + 3 * i + 2] = blockXNorm;
  }

  return obs;
}

async function predict(stackedObs: Float32Array): Promise<number> {
  if (!session) throw new Error("Model not loaded");

  const tensor = new ort.Tensor("float32", stackedObs, [1, 124]);
  const feeds = { observation: tensor };
  const results = await session.run(feeds);

  const logits = Array.from(results.action_logits.data as Float32Array);

  console.log("Action logits:", logits);

  if (logits.some(isNaN)) {
    console.error("NaN detected in logits, returning default action.");
    return 2; // Default to "NONE" action
  }

  return logits.indexOf(Math.max(...logits));
}

export async function startVisualizer(app: Application) {
  await initModel();

  const width = app.screen.width;
  const height = app.screen.height;
  const game = new DodgerCore(width, height);
  const render = createRenderObjects(app);

  let obsStack: Float32Array[] = [];
  const initialObs = processState(game.getState(), width, height);
  obsStack = [initialObs, initialObs, initialObs, initialObs];

  let isRunning = true;
  let isProcessing = false;

  app.ticker.maxFPS = 60;

  const tickerFn = async () => {
    if (!isRunning || isProcessing) return;
    isProcessing = true;

    const stacked = new Float32Array(124);
    for (let i = 0; i < N_STACK; i++) {
      stacked.set(obsStack[i], i * 31);
    }

    const actionIdx = await predict(stacked);
    const action = ACTIONS[actionIdx];

    game.step(action, FIXED_DT);
    const state = game.getState();
    renderState(app, render, state);

    const newObs = processState(state, width, height);
    obsStack.shift();
    obsStack.push(newObs);

    if (state.gameOver) {
      game.step("RESTART", FIXED_DT);
      const resetObs = processState(game.getState(), width, height);
      obsStack = [resetObs, resetObs, resetObs, resetObs];
    }

    isProcessing = false;
  };

  app.ticker.add(tickerFn);

  return () => {
    isRunning = false;
    app.ticker.remove(tickerFn);
  };
}
