export type Action = "LEFT" | "RIGHT" | "NONE" | "RESTART";

export interface GameState {
  playerX: number;
  playerY: number;
  blocks: { x: number; y: number }[];
  score: number;
  gameOver: boolean;
}

const PLAYER_WIDTH = 60;
const PLAYER_HEIGHT = 20;
const PLAYER_SPEED = 5;
const BLOCK_SIZE = 30;
const BLOCK_SPEED = 3;
const BLOCK_SPAWN_INTERVAL = 60; // frames (1s at 60fps)

export class DodgerCore {
  private width: number;
  private height: number;

  private playerX: number;
  private playerY: number;
  private blocks: { x: number; y: number }[] = [];
  private score = 0;
  private gameOver = false;
  private frameCounter = 0;
  private elapsedTime = 0;

  constructor(width: number, height: number) {
    this.width = width;
    this.height = height;
    this.playerX = width / 2 - PLAYER_WIDTH / 2;
    this.playerY = height - PLAYER_HEIGHT - 10;
  }

  public step(action: Action): GameState {
    if (this.gameOver && action === "RESTART") {
      this.reset();
    } else if (!this.gameOver) {
      if (action === "LEFT" && this.playerX > 0) {
        this.playerX -= PLAYER_SPEED;
      }
      if (action === "RIGHT" && this.playerX < this.width - PLAYER_WIDTH) {
        this.playerX += PLAYER_SPEED;
      }
    }

    this.update();
    return this.getState();
  }

  private update() {
    if (this.gameOver) return;

    this.frameCounter++;
    if (this.frameCounter % BLOCK_SPAWN_INTERVAL === 0) {
      this.spawnBlock();
    }

    this.moveBlocks();

    this.elapsedTime += 1 / 60; // assume 60fps
    this.score = Math.floor(this.elapsedTime);
  }

  private spawnBlock() {
    const x = Math.random() * (this.width - BLOCK_SIZE);
    this.blocks.push({ x, y: -BLOCK_SIZE });
  }

  private moveBlocks() {
    for (let i = this.blocks.length - 1; i >= 0; i--) {
      const block = this.blocks[i];
      block.y += BLOCK_SPEED;
      if (block.y > this.height) {
        this.blocks.splice(i, 1);
        continue;
      }
      if (this.isColliding(block)) {
        this.gameOver = true;
        return;
      }
    }
  }

  private isColliding(block: { x: number; y: number }): boolean {
    return !(
      this.playerX + PLAYER_WIDTH < block.x ||
      this.playerX > block.x + BLOCK_SIZE ||
      this.playerY + PLAYER_HEIGHT < block.y ||
      this.playerY > block.y + BLOCK_SIZE
    );
  }

  private reset() {
    this.blocks = [];
    this.score = 0;
    this.gameOver = false;
    this.frameCounter = 0;
    this.elapsedTime = 0;
    this.playerX = this.width / 2 - PLAYER_WIDTH / 2;
    this.playerY = this.height - PLAYER_HEIGHT - 10;
  }

  public getState(): GameState {
    return {
      playerX: this.playerX,
      playerY: this.playerY,
      blocks: [...this.blocks],
      score: this.score,
      gameOver: this.gameOver,
    };
  }
}
