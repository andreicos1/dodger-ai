import type { Application } from "pixi.js";
import { createRenderObjects, renderState } from "./renderer";
import { DodgerCore, type Action, type GameState } from "@shared/core";

const LOGICAL_FRAME_RATE = 60;
const FIXED_DT = 1 / LOGICAL_FRAME_RATE;
const SERVER_URL = import.meta.env.VITE_SERVER_URL;

interface GameData {
  type: "step" | "restart";
  step?: number;
  action?: Action;
  reward?: number;
  message?: string;
}

export function startVisualizer(app: Application) {
  const width = app.screen.width;
  const height = app.screen.height;
  let game = new DodgerCore(width, height);
  const render = createRenderObjects(app);
  const ws = new WebSocket(SERVER_URL);

  ws.onopen = () => {
    console.log("Visualizer connected to server");
    ws.send(JSON.stringify({ type: "init", width: width, height: height }));
  };

  ws.onmessage = (event) => {
    const data: GameData = JSON.parse(event.data);
    if (data.type === "step") {
      game.step(data.action as Action, FIXED_DT);
      const state: GameState = game.getState();
      renderState(app, render, state);
      ws.send(JSON.stringify({ type: "state", state }));
    } else if (data.type === "restart") {
      game.step("RESTART", FIXED_DT);
      const state: GameState = game.getState();
      renderState(app, render, state);
      ws.send(JSON.stringify({ type: "state", state }));
    } else if (data.type === "error") {
      console.error("Visualizer error:", data.message);
    }
  };
}
