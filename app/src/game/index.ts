import { Application, Graphics, Sprite, Texture } from "pixi.js";

const BACKGROUND_COLOR = "#001524";
const PLAYER_WIDTH = 60;
const PLAYER_HEIGHT = 20;
const PLAYER_SPEED = 5;
const BLOCK_SIZE = 30;
const BLOCK_SPEED = 3;

class DodgerGame {
  private app: Application;
  private player: Graphics;
  private blocks: Sprite[] = [];
  private keys: Record<string, boolean> = {};
  private blockTexture: Texture;

  constructor(app: Application) {
    this.app = app;
    this.player = this.createPlayer();
    this.blockTexture = this.createBlockTexture();
    this.setupControls();
    setInterval(() => this.spawnBlock(), 1500);
    this.app.ticker.add(() => this.update());
  }

  private createPlayer(): Graphics {
    const g = new Graphics();
    g.rect(0, 0, PLAYER_WIDTH, PLAYER_HEIGHT).fill(0x00ff00);
    g.x = this.app.screen.width / 2 - PLAYER_WIDTH / 2;
    g.y = this.app.screen.height - PLAYER_HEIGHT - 10;
    this.app.stage.addChild(g);
    return g;
  }

  private createBlockTexture(): Texture {
    const g = new Graphics();
    g.rect(0, 0, BLOCK_SIZE, BLOCK_SIZE).fill(0xff0000);
    return this.app.renderer.generateTexture(g);
  }

  private setupControls() {
    window.addEventListener("keydown", (e: KeyboardEvent) => {
      this.keys[e.code] = true;
    });
    window.addEventListener("keyup", (e: KeyboardEvent) => {
      this.keys[e.code] = false;
    });
  }

  private spawnBlock() {
    const block = new Sprite(this.blockTexture);
    block.x = Math.random() * (this.app.screen.width - BLOCK_SIZE);
    block.y = -BLOCK_SIZE;
    this.app.stage.addChild(block);
    this.blocks.push(block);
  }

  private update() {
    if (this.keys["ArrowLeft"] && this.player.x > 0) {
      this.player.x -= PLAYER_SPEED;
    }
    if (
      this.keys["ArrowRight"] &&
      this.player.x < this.app.screen.width - PLAYER_WIDTH
    ) {
      this.player.x += PLAYER_SPEED;
    }

    for (let i = this.blocks.length - 1; i >= 0; i--) {
      const block = this.blocks[i];
      block.y += BLOCK_SPEED;
      if (block.y > this.app.screen.height) {
        this.app.stage.removeChild(block);
        this.blocks.splice(i, 1);
      }
    }
  }
}

(async () => {
  const app = new Application();
  await app.init({ background: BACKGROUND_COLOR, resizeTo: window });
  document.body.appendChild(app.canvas);
  new DodgerGame(app);
})();
