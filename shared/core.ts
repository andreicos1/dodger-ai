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
const PLAYER_SPEED_PPS = 300; // 5 pixels/frame * 60 fps = 300
const BLOCK_SPEED_PPS = 180; // 3 pixels/frame * 60 fps = 180
const BLOCK_SIZE = 30;
const BLOCKS_PER_SECOND = 2;
const SPAWN_INTERVAL_SECONDS = 1 / BLOCKS_PER_SECOND;

export class DodgerCore {
  private width: number;
  private height: number;

  private playerX: number;
  private playerY: number;
  private blocks: { x: number; y: number }[] = [];
  private score = 0;
  private gameOver = false;
  private startTime = 0;
  private timeUntilNextBlock: number = SPAWN_INTERVAL_SECONDS;

  constructor(width: number, height: number) {
    this.width = width;
    this.height = height;
    this.playerX = width / 2 - PLAYER_WIDTH / 2;
    this.playerY = height - PLAYER_HEIGHT - 10;
    this.startTime = Date.now();
  }

  public step(action: Action, dt: number): GameState {
    if (this.gameOver && action === "RESTART") {
      this.reset();
    } else if (!this.gameOver) {
      if (action === "LEFT" && this.playerX > 0) {
        this.playerX -= PLAYER_SPEED_PPS * dt;
      }
      if (action === "RIGHT" && this.playerX < this.width - PLAYER_WIDTH) {
        this.playerX += PLAYER_SPEED_PPS * dt;
      }
    }

    this.update(dt);
    return this.getState();
  }

  private update(dt: number) {
    if (this.gameOver) return;

    this.timeUntilNextBlock -= dt;
    if (this.timeUntilNextBlock <= 0) {
      this.spawnBlock();
      // Add the interval back, accounting for any overshoot
      this.timeUntilNextBlock += SPAWN_INTERVAL_SECONDS;
    }

    this.moveBlocks(dt);

    const now = Date.now();
    this.score = Math.floor((now - this.startTime) / 1000);
  }

  private spawnBlock() {
    const x = Math.random() * (this.width - BLOCK_SIZE);
    this.blocks.push({ x, y: -BLOCK_SIZE });
  }

  private moveBlocks(dt: number) {
    for (let i = this.blocks.length - 1; i >= 0; i--) {
      const block = this.blocks[i];
      block.y += BLOCK_SPEED_PPS * dt;
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
    this.startTime = Date.now();
    this.playerX = this.width / 2 - PLAYER_WIDTH / 2;
    this.playerY = this.height - PLAYER_HEIGHT - 10;
    this.timeUntilNextBlock = SPAWN_INTERVAL_SECONDS;
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
