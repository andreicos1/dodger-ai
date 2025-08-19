import { Text, Graphics, Application, Container } from "pixi.js";
import { createApp } from "./renderer";
import { startPlayable } from "./playable";
import { startVisualizer } from "./ai-visualizer";

function createTitle(app: Application) {
  const title = new Text({
    text: "Dodger Game",
    style: { fill: "#FFECD1", fontSize: 48, align: "center" },
  });
  title.anchor.set(0.5);
  title.x = app.screen.width / 2;
  title.y = app.screen.height / 3;
  return title;
}

function createPlayButton(app: Application) {
  const playBtn = new Text({
    text: "▶ Play Game",
    style: { fill: "#00ff00", fontSize: 32 },
  });
  playBtn.anchor.set(0.5);
  playBtn.x = app.screen.width / 2;
  playBtn.y = app.screen.height / 2;
  playBtn.eventMode = "static";
  playBtn.cursor = "pointer";
  return playBtn;
}

function createAIBtn(app: Application) {
  const aiBtn = new Text({
    text: "🤖 AI Visualizer",
    style: { fill: "#00aaff", fontSize: 32 },
  });
  aiBtn.anchor.set(0.5);
  aiBtn.x = app.screen.width / 2;
  aiBtn.y = app.screen.height / 2 + 60;
  aiBtn.eventMode = "static";
  aiBtn.cursor = "pointer";
  return aiBtn;
}

function createExitButton(app: Application) {
  const exitBtn = new Text({
    text: "X",
    style: { fill: "#ff0000", fontSize: 32 },
  });
  exitBtn.anchor.set(1, 0);
  exitBtn.x = app.screen.width - 16;
  exitBtn.y = 16;
  exitBtn.eventMode = "static";
  exitBtn.cursor = "pointer";
  return exitBtn;
}

let cleanupCurrentMode: (() => void) | null = null;
function createMenu(app: Application) {
  const menuContainer = new Container();

  const title = createTitle(app);
  const playBtn = createPlayButton(app);
  const aiBtn = createAIBtn(app);

  menuContainer.addChild(title, playBtn, aiBtn);

  playBtn.on("pointerdown", () => {
    app.stage.removeChild(menuContainer);
    cleanupCurrentMode = startPlayable(app);
    addExitButton(app);
  });

  aiBtn.on("pointerdown", () => {
    app.stage.removeChild(menuContainer);
    startVisualizer(app);
    addExitButton(app);
  });

  return menuContainer;
}

function resetToMainMenu(app: Application) {
  if (cleanupCurrentMode) {
    cleanupCurrentMode(); // stop ticker + destroy objects
    cleanupCurrentMode = null;
  }

  app.stage.removeChildren().forEach((c) => c.destroy());

  const bg = new Graphics()
    .rect(0, 0, app.screen.width, app.screen.height)
    .fill("#001524");
  app.stage.addChild(bg);

  const menuContainer = createMenu(app);
  app.stage.addChild(menuContainer);
}

function createPauseMenu(app: Application) {
  const overlay = new Container();

  // Semi-transparent background
  const bg = new Graphics()
    .rect(0, 0, app.screen.width, app.screen.height)
    .fill({ color: 0x000000, alpha: 0.6 });
  overlay.addChild(bg);

  // Resume button
  const resumeBtn = new Text({
    text: "▶ Resume",
    style: { fill: "#00ff00", fontSize: 36 },
  });
  resumeBtn.anchor.set(0.5);
  resumeBtn.x = app.screen.width / 2;
  resumeBtn.y = app.screen.height / 2 - 30;
  resumeBtn.eventMode = "static";
  resumeBtn.cursor = "pointer";
  overlay.addChild(resumeBtn);

  // Main Menu button
  const mainMenuBtn = new Text({
    text: "🏠 Main Menu",
    style: { fill: "#ffaa00", fontSize: 36 },
  });
  mainMenuBtn.anchor.set(0.5);
  mainMenuBtn.x = app.screen.width / 2;
  mainMenuBtn.y = app.screen.height / 2 + 30;
  mainMenuBtn.eventMode = "static";
  mainMenuBtn.cursor = "pointer";
  overlay.addChild(mainMenuBtn);

  resumeBtn.on("pointerdown", () => {
    app.stage.removeChild(overlay);
  });

  mainMenuBtn.on("pointerdown", () => resetToMainMenu(app));

  return overlay;
}

function onExitButtonClick(app: Application) {
  const pauseMenu = createPauseMenu(app);
  app.stage.addChild(pauseMenu);
}

function addExitButton(app: Application) {
  const exitBtn = createExitButton(app);
  app.stage.addChild(exitBtn);
  exitBtn.on("pointerdown", () => onExitButtonClick(app));
}

(async () => {
  const app = await createApp();

  // Background
  const bg = new Graphics()
    .rect(0, 0, app.screen.width, app.screen.height)
    .fill("#001524");
  app.stage.addChild(bg);

  // Main menu (no exit button here)
  const menuContainer = createMenu(app);
  app.stage.addChild(menuContainer);
})();
