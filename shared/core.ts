export type Action = "LEFT" | "RIGHT" | "NONE" | "RESTART";

export interface GameState {
  playerX: number;
  playerY: number;
  blocks: { x: number; y: number }[];
  score: number;
  gameOver: boolean;
}

const FPS = 60;
const PLAYER_WIDTH = 60;
const PLAYER_HEIGHT = 20;
const PLAYER_Y_OFFSET = 10;
const PLAYER_SPEED_PIXELS_PER_FRAME = 5;
const BLOCK_SPEED_PIXELS_PER_FRAME = 4;
const BLOCK_SIZE = 30;

const PLAYER_SPEED_PPS = PLAYER_SPEED_PIXELS_PER_FRAME * FPS;
const BLOCK_SPEED_PPS = BLOCK_SPEED_PIXELS_PER_FRAME * FPS;

function calculateBlocksPerSecond(width: number): number {
  return 2 + Math.max(0, Math.floor((width - 400) / 200));
}

export class DodgerCore {
  private width: number;
  private height: number;

  private playerX: number;
  private playerY: number;
  private blocks: { x: number; y: number }[] = [];
  private score = 0;
  private gameOver = false;
  private startTime = 0;
  private pausedTime = 0;
  private lastPauseTime = 0;
  private isPaused = false;
  private blocksPerSecond: number;
  private timeUntilNextBlock: number;

  constructor(width: number, height: number) {
    this.width = width;
    this.height = height;
    this.playerX = width / 2 - PLAYER_WIDTH / 2;
    this.playerY = height - PLAYER_HEIGHT - PLAYER_Y_OFFSET;
    this.startTime = Date.now();
    this.blocksPerSecond = calculateBlocksPerSecond(width);
    this.timeUntilNextBlock = 1 / this.blocksPerSecond;
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
      this.timeUntilNextBlock += 1 / this.blocksPerSecond;
    }

    this.moveBlocks(dt);

    const now = Date.now();
    const elapsed = now - this.startTime - this.pausedTime;
    this.score = Math.floor(elapsed / 1000);
  }

  private spawnBlock() {
    const spawnY = -BLOCK_SIZE;
    const spawnRangeY = BLOCK_SIZE * 3;
    const maxAttempts = 50;

    for (let i = 0; i < maxAttempts; i++) {
      const x = Math.random() * (this.width - BLOCK_SIZE);

      if (!this.isOverlappingWithBlocks(x, spawnY, spawnRangeY)) {
        this.blocks.push({ x, y: spawnY });
        return;
      }
    }

    this.blocks.push({
      x: Math.random() * (this.width - BLOCK_SIZE),
      y: spawnY,
    });
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

  private isOverlappingWithBlocks(
    x: number,
    y: number,
    rangeY: number
  ): boolean {
    return this.blocks.some((block) => {
      if (Math.abs(block.y - y) > rangeY) return false;
      return !(x + BLOCK_SIZE < block.x || x > block.x + BLOCK_SIZE);
    });
  }

  private reset() {
    this.blocks = [];
    this.score = 0;
    this.gameOver = false;
    this.startTime = Date.now();
    this.pausedTime = 0;
    this.lastPauseTime = 0;
    this.isPaused = false;
    this.playerX = this.width / 2 - PLAYER_WIDTH / 2;
    this.playerY = this.height - PLAYER_HEIGHT - PLAYER_Y_OFFSET;
    this.timeUntilNextBlock = 1 / this.blocksPerSecond;
  }

  public pause() {
    if (!this.isPaused) {
      this.isPaused = true;
      this.lastPauseTime = Date.now();
    }
  }

  public resume() {
    if (this.isPaused) {
      this.isPaused = false;
      this.pausedTime += Date.now() - this.lastPauseTime;
    }
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
