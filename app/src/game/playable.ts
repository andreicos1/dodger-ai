import { DodgerCore, type GameState } from "@shared/core";
import { createRenderObjects, renderState } from "./renderer";
import type { Application } from "pixi.js";

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

  app.ticker.add(() => {
    let action: "LEFT" | "RIGHT" | "NONE" | "RESTART" = "NONE";
    if (keys["ArrowLeft"]) action = "LEFT";
    if (keys["ArrowRight"]) action = "RIGHT";
    if (keys["Space"]) action = "RESTART";

    core.step(action);
    const state: GameState = core.getState();
    renderState(app, render, state);
  });
}
