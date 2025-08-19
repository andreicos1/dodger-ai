import type { GameState } from "@shared/core";
import { Application, Graphics, Text, Sprite, Texture } from "pixi.js";

const BACKGROUND_COLOR = "#001524";
const PLAYER_COLOR = "#00ff00";
const BLOCK_COLOR = "#ff0000";
const SCORE_TEXT_COLOR = "#FFECD1";
const GAME_OVER_TEXT_COLOR = "#ff0000";

const PLAYER_WIDTH = 60;
const PLAYER_HEIGHT = 20;
const BLOCK_SIZE = 30;

export interface RenderObjects {
  player: Graphics;
  blocks: Sprite[];
  scoreText: Text;
  gameOverText: Text;
  blockTexture: Texture;
}

export async function createApp(): Promise<Application> {
  const app = new Application();
  await app.init({ background: BACKGROUND_COLOR, resizeTo: window });
  document.body.appendChild(app.canvas);
  return app;
}

export function createRenderObjects(app: Application): RenderObjects {
  const player = new Graphics()
    .rect(0, 0, PLAYER_WIDTH, PLAYER_HEIGHT)
    .fill(PLAYER_COLOR);

  const g = new Graphics().rect(0, 0, BLOCK_SIZE, BLOCK_SIZE).fill(BLOCK_COLOR);
  const blockTexture = app.renderer.generateTexture(g);

  const scoreText = new Text({
    text: "Score: 0",
    style: { fill: SCORE_TEXT_COLOR, fontSize: 24 },
  });
  scoreText.x = 10;
  scoreText.y = 10;

  const gameOverText = new Text({
    text: "",
    style: { fill: GAME_OVER_TEXT_COLOR, fontSize: 36, align: "center" },
  });
  gameOverText.anchor.set(0.5);
  gameOverText.x = app.screen.width / 2;
  gameOverText.y = app.screen.height / 2;

  app.stage.addChild(player);
  app.stage.addChild(scoreText);
  app.stage.addChild(gameOverText);

  return {
    player,
    blocks: [],
    scoreText,
    gameOverText,
    blockTexture,
  };
}

export function renderState(
  app: Application,
  render: RenderObjects,
  state: GameState
) {
  render.player.x = state.playerX;
  render.player.y = state.playerY;

  render.blocks.forEach((b) => app.stage.removeChild(b));
  render.blocks.length = 0;

  for (const b of state.blocks) {
    const sprite = new Sprite(render.blockTexture);
    sprite.x = b.x;
    sprite.y = b.y;
    app.stage.addChild(sprite);
    render.blocks.push(sprite);
  }

  render.scoreText.text = `Score: ${state.score}`;
  render.gameOverText.text = state.gameOver
    ? `Game Over!\nScore: ${state.score}\nPress Space to Restart`
    : "";
}
