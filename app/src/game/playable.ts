import { DodgerCore, type GameState, type Action } from "@shared/core";
import { createRenderObjects, renderState } from "./renderer";
import type { Application, Ticker } from "pixi.js";

function setupKeyboard(): Record<string, boolean> {
  const keys: Record<string, boolean> = {};
  window.addEventListener("keydown", (e) => (keys[e.code] = true));
  window.addEventListener("keyup", (e) => (keys[e.code] = false));
  return keys;
}

export function startPlayable(app: Application) {
  const core = new DodgerCore(app.screen.width, app.screen.height);
  const render = createRenderObjects(app);
  const keys = setupKeyboard();

  const update = (ticker: Ticker) => {
    const dt = ticker.deltaMS / 1000;

    let action: Action = "NONE";
    if (keys["ArrowLeft"]) action = "LEFT";
    if (keys["ArrowRight"]) action = "RIGHT";
    if (keys["Space"]) action = "RESTART";

    core.step(action, dt);

    const state: GameState = core.getState();
    renderState(app, render, state);
  };

  app.ticker.add(update);

  return () => {
    app.ticker.remove(update);
  };
}
