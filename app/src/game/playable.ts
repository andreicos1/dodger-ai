import { DodgerCore, type GameState, type Action } from "@shared/core";
import { createRenderObjects, renderState } from "./renderer";
import type { Application, Ticker } from "pixi.js";

function setupKeyboard(): Record<string, boolean> {
  const keys: Record<string, boolean> = {};
  window.addEventListener("keydown", (e) => (keys[e.code] = true));
  window.addEventListener("keyup", (e) => (keys[e.code] = false));
  return keys;
}

function setupTouch(width: number): {
  isLeft: () => boolean;
  isRight: () => boolean;
  isTap: () => boolean;
} {
  let touchLeft = false;
  let touchRight = false;
  let tapped = false;

  const handleTouchStart = (e: TouchEvent) => {
    e.preventDefault();
    for (let i = 0; i < e.touches.length; i++) {
      const touch = e.touches[i];
      if (touch.clientX < width / 2) {
        touchLeft = true;
      } else {
        touchRight = true;
      }
    }
  };

  const handleTouchEnd = (e: TouchEvent) => {
    e.preventDefault();
    touchLeft = false;
    touchRight = false;
    tapped = true;
    setTimeout(() => (tapped = false), 100);
  };

  const handleTouchMove = (e: TouchEvent) => {
    e.preventDefault();
    touchLeft = false;
    touchRight = false;
    for (let i = 0; i < e.touches.length; i++) {
      const touch = e.touches[i];
      if (touch.clientX < width / 2) {
        touchLeft = true;
      } else {
        touchRight = true;
      }
    }
  };

  window.addEventListener("touchstart", handleTouchStart, { passive: false });
  window.addEventListener("touchend", handleTouchEnd, { passive: false });
  window.addEventListener("touchmove", handleTouchMove, { passive: false });

  return {
    isLeft: () => touchLeft,
    isRight: () => touchRight,
    isTap: () => tapped,
  };
}

export function startPlayable(app: Application) {
  const core = new DodgerCore(app.screen.width, app.screen.height);
  const render = createRenderObjects(app);
  const keys = setupKeyboard();
  const touch = setupTouch(app.screen.width);

  let isPaused = false;

  const update = (ticker: Ticker) => {
    if (isPaused) return;

    const dt = ticker.deltaMS / 1000;

    let action: Action = "NONE";
    if (keys["ArrowLeft"] || touch.isLeft()) action = "LEFT";
    if (keys["ArrowRight"] || touch.isRight()) action = "RIGHT";
    if (keys["Space"] || touch.isTap()) action = "RESTART";

    core.step(action, dt);

    const state: GameState = core.getState();
    renderState(app, render, state);
  };

  app.ticker.add(update);

  return {
    cleanup: () => {
      app.ticker.remove(update);
    },
    pause: () => {
      isPaused = true;
      core.pause();
    },
    resume: () => {
      isPaused = false;
      core.resume();
    },
  };
}
