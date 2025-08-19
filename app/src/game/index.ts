import { Text, Graphics, Application } from "pixi.js";
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

function createMenu(app: Application) {
  const menuContainer = new Graphics();
  menuContainer.eventMode = "static";

  const title = createTitle(app);
  const playBtn = createPlayButton(app);
  const aiBtn = createAIBtn(app);

  menuContainer.addChild(title, playBtn, aiBtn);

  playBtn.on("pointerdown", () => {
    app.stage.removeChild(menuContainer);
    startPlayable(app);
  });

  aiBtn.on("pointerdown", () => {
    app.stage.removeChild(menuContainer);
    startVisualizer(app);
  });

  return menuContainer;
}

function onExitButtonClick(app: Application) {
  console.log("Exit button clicked!");
}

(async () => {
  const app = await createApp();

  const bg = new Graphics()
    .rect(0, 0, app.screen.width, app.screen.height)
    .fill("#001524");
  app.stage.addChild(bg);

  const menuContainer = createMenu(app);
  app.stage.addChild(menuContainer);

  const exitBtn = createExitButton(app);
  app.stage.addChild(exitBtn);

  exitBtn.on("pointerdown", () => onExitButtonClick(app));
})();
