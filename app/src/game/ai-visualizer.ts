import type { Application } from "pixi.js";
import { createRenderObjects, renderState } from "./renderer";
import type { GameState } from "@shared/core";

export function startVisualizer(app: Application) {
  const render = createRenderObjects(app);
  const ws = new WebSocket("ws://localhost:8080");

  let lastState: GameState | null = null;

  ws.onopen = () => {
    ws.send(JSON.stringify({ type: "watch" }));
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "state") {
      const state: GameState = data.state;
      lastState = state;
      renderState(app, render, state);
    } else if (data.type === "error") {
      console.error("Visualizer error:", data.message);
    }
  };

  // Spacebar restart only works if this client is the owner
  window.addEventListener("keydown", (e) => {
    if (e.code === "Space" && lastState?.gameOver) {
      ws.send(JSON.stringify({ type: "restart" }));
    }
  });
}
