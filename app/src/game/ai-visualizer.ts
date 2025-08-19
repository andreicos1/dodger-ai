import type { Application } from "pixi.js";
import { createRenderObjects, renderState } from "./renderer";
import type { GameState } from "@shared/core";

export function startVisualizer(app: Application) {
  const render = createRenderObjects(app);
  const ws = new WebSocket("ws://localhost:8080");

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "state") {
      const state: GameState = data.state;
      renderState(app, render, state);
    }
  };
}
