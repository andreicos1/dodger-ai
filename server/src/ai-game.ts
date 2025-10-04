import { DodgerCore, Action } from "../../shared/core";
import { WebSocketServer, WebSocket } from "ws";

const WIDTH = 800;
const HEIGHT = 600;

const LOGICAL_FRAME_RATE = 60;
const FIXED_DT = 1 / LOGICAL_FRAME_RATE;

const wss = new WebSocketServer({ port: 8080 });
console.log("AI WebSocket server running on ws://localhost:8080");
console.log(
  `Simulating at a fixed timestep of ${FIXED_DT.toFixed(
    5
  )}s (${LOGICAL_FRAME_RATE} FPS)`
);

const games = new Map<WebSocket, DodgerCore>();

wss.on("connection", (ws) => {
  console.log("Client connected");

  let game = new DodgerCore(WIDTH, HEIGHT);
  games.set(ws, game);

  ws.on("message", (msg) => {
    try {
      const data = JSON.parse(msg.toString());

      if (data.type === "step") {
        const state = game.step(data.action as Action, FIXED_DT);
        ws.send(JSON.stringify({ type: "state", state }));
      } else if (data.type === "restart") {
        game = new DodgerCore(WIDTH, HEIGHT);
        games.set(ws, game);

        const state = game.step("RESTART", FIXED_DT);
        ws.send(JSON.stringify({ type: "state", state }));
      } else {
        console.warn("Unknown message type:", data.type);
      }
    } catch (err) {
      console.error("Invalid message", err);
    }
  });

  ws.on("close", () => {
    console.log("Client disconnected");
    games.delete(ws);
  });
});
