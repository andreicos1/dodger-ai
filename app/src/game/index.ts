import { Text, Graphics } from "pixi.js";
import { createApp } from "./renderer";
import { startPlayable } from "./playable";
import { startVisualizer } from "./ai-visualizer";

(async () => {
  const app = await createApp();

  // Menu background
  const bg = new Graphics()
    .rect(0, 0, app.screen.width, app.screen.height)
    .fill("#001524");
  app.stage.addChild(bg);

  // Title
  const title = new Text({
    text: "Dodger Game",
    style: { fill: "#FFECD1", fontSize: 48, align: "center" },
  });
  title.anchor.set(0.5);
  title.x = app.screen.width / 2;
  title.y = app.screen.height / 3;
  app.stage.addChild(title);

  // Play button
  const playBtn = new Text({
    text: "▶ Play Game",
    style: { fill: "#00ff00", fontSize: 32 },
  });
  playBtn.anchor.set(0.5);
  playBtn.x = app.screen.width / 2;
  playBtn.y = app.screen.height / 2;
  playBtn.eventMode = "static";
  playBtn.cursor = "pointer";
  app.stage.addChild(playBtn);

  // AI Visualizer button
  const aiBtn = new Text({
    text: "🤖 AI Visualizer",
    style: { fill: "#00aaff", fontSize: 32 },
  });
  aiBtn.anchor.set(0.5);
  aiBtn.x = app.screen.width / 2;
  aiBtn.y = app.screen.height / 2 + 60;
  aiBtn.eventMode = "static";
  aiBtn.cursor = "pointer";
  app.stage.addChild(aiBtn);

  // Button handlers
  playBtn.on("pointerdown", () => {
    app.stage.removeChildren();
    startPlayable(app);
  });

  aiBtn.on("pointerdown", () => {
    app.stage.removeChildren();
    startVisualizer(app);
  });
})();
