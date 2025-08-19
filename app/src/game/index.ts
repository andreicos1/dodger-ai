import { Application, Graphics, Sprite, Texture, Text, Ticker } from "pixi.js";

const BACKGROUND_COLOR = "#001524";
const PLAYER_WIDTH = 60;
const PLAYER_HEIGHT = 20;
const PLAYER_SPEED = 5;
const BLOCK_SIZE = 30;
const BLOCK_SPEED = 3;
const BLOCK_SPAWN_INTERVAL = 1000;
const PLAYER_COLOR = "#00ff00";
const BLOCK_COLOR = "#ff0000";
const SCORE_TEXT_COLOR = "#FFECD1";
const GAME_OVER_TEXT_COLOR = "#ff0000";

class DodgerGame {
  private app: Application;
  private player!: Graphics;
  private blocks: Sprite[] = [];
  private keys: Record<string, boolean> = {};
  private blockTexture!: Texture;
  private gameOver = false;
  private score = 0;
  private scoreText!: Text;
  private gameOverText!: Text;
  private elapsedTime = 0;
  private blockIntervalId?: number;

  constructor(app: Application) {
    this.app = app;
    this.init();
  }

  private init() {
    this.reset();
    this.player = this.createPlayer();
    this.blockTexture = this.createBlockTexture();
    this.scoreText = this.createScoreText();
    this.gameOverText = this.createGameOverText();
    this.setupControls();
    this.blockIntervalId = window.setInterval(
      () => this.spawnBlock(),
      BLOCK_SPAWN_INTERVAL
    );
    this.app.ticker.add((delta: Ticker) => this.update(delta));
  }

  private reset() {
    this.blocks.forEach((b) => this.app.stage.removeChild(b));
    this.blocks = [];
    this.score = 0;
    this.gameOver = false;
    if (this.blockIntervalId) clearInterval(this.blockIntervalId);
    if (this.scoreText) this.app.stage.removeChild(this.scoreText);
    if (this.gameOverText) this.app.stage.removeChild(this.gameOverText);
    if (this.player) this.app.stage.removeChild(this.player); // FIX: remove old player
  }

  private createPlayer(): Graphics {
    const g = new Graphics();
    g.rect(0, 0, PLAYER_WIDTH, PLAYER_HEIGHT).fill(PLAYER_COLOR);
    g.x = this.app.screen.width / 2 - PLAYER_WIDTH / 2;
    g.y = this.app.screen.height - PLAYER_HEIGHT - 10;
    this.app.stage.addChild(g);
    return g;
  }

  private createBlockTexture(): Texture {
    const g = new Graphics();
    g.rect(0, 0, BLOCK_SIZE, BLOCK_SIZE).fill(BLOCK_COLOR);
    return this.app.renderer.generateTexture(g);
  }

  private createScoreText(): Text {
    const text = new Text({
      text: "Score: 0",
      style: { fill: SCORE_TEXT_COLOR, fontSize: 24 },
    });
    text.x = 10;
    text.y = 10;
    this.app.stage.addChild(text);
    return text;
  }

  private createGameOverText(): Text {
    const text = new Text({
      text: "",
      style: { fill: GAME_OVER_TEXT_COLOR, fontSize: 36, align: "center" },
    });
    text.anchor.set(0.5);
    text.x = this.app.screen.width / 2;
    text.y = this.app.screen.height / 2;
    this.app.stage.addChild(text);
    return text;
  }

  private setupControls() {
    window.addEventListener("keydown", (e: KeyboardEvent) => {
      this.keys[e.code] = true;
      if (this.gameOver && e.code === "Space") {
        this.restart();
      }
    });
    window.addEventListener("keyup", (e: KeyboardEvent) => {
      this.keys[e.code] = false;
    });
  }

  private spawnBlock() {
    if (this.gameOver) return;
    const block = new Sprite(this.blockTexture);
    block.x = Math.random() * (this.app.screen.width - BLOCK_SIZE);
    block.y = -BLOCK_SIZE;
    this.app.stage.addChild(block);
    this.blocks.push(block);
  }

  private moveBlocks() {
    for (let i = this.blocks.length - 1; i >= 0; i--) {
      const block = this.blocks[i];
      block.y += BLOCK_SPEED;
      if (block.y > this.app.screen.height) {
        this.app.stage.removeChild(block);
        this.blocks.splice(i, 1);
        continue;
      }
      if (this.isColliding(this.player, block)) {
        this.endGame();
        return;
      }
    }
  }

  private update(delta: Ticker) {
    if (this.gameOver) return;

    // Player movement
    if (this.keys["ArrowLeft"] && this.player.x > 0) {
      this.player.x -= PLAYER_SPEED;
    }
    if (
      this.keys["ArrowRight"] &&
      this.player.x < this.app.screen.width - PLAYER_WIDTH
    ) {
      this.player.x += PLAYER_SPEED;
    }

    this.moveBlocks();

    // Update score (delta is in "frames at 60fps")
    this.elapsedTime += delta.deltaTime / 60; // convert to seconds
    this.score = Math.floor(this.elapsedTime);
    this.scoreText.text = `Score: ${this.score}`;
  }

  private isColliding(a: Graphics | Sprite, b: Sprite): boolean {
    const ab = a.getBounds();
    const bb = b.getBounds();
    return (
      ab.x < bb.x + bb.width &&
      ab.x + ab.width > bb.x &&
      ab.y < bb.y + bb.height &&
      ab.y + ab.height > bb.y
    );
  }

  private endGame() {
    this.gameOver = true;
    if (this.blockIntervalId) clearInterval(this.blockIntervalId);
    this.gameOverText.text = `Game Over!\nScore: ${this.score}\nPress SPACE to restart`;
  }

  private restart() {
    this.reset();
    this.player = this.createPlayer();
    this.blockTexture = this.createBlockTexture();
    this.scoreText = this.createScoreText();
    this.gameOverText = this.createGameOverText();
    this.elapsedTime = 0; // reset timer
    this.blockIntervalId = window.setInterval(() => this.spawnBlock(), 1500);
  }
}

(async () => {
  const app = new Application();
  await app.init({ background: BACKGROUND_COLOR, resizeTo: window });
  document.body.appendChild(app.canvas);
  new DodgerGame(app);
})();
