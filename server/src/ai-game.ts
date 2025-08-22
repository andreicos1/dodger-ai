import { DodgerCore, Action, GameState } from "../../shared/core";
import { WebSocketServer, WebSocket } from "ws";

const WIDTH = 800;
const HEIGHT = 600;

const LOGICAL_FRAME_RATE = 60;
const FIXED_DT = 1 / LOGICAL_FRAME_RATE; // This will be approx. 0.01667 seconds

const wss = new WebSocketServer({ port: 8080 });
console.log("AI WebSocket server running on ws://localhost:8080");
console.log(
  `Simulating at a fixed timestep of ${FIXED_DT.toFixed(
    5
  )}s (${LOGICAL_FRAME_RATE} FPS)`
);

// Create a single, shared game instance
const game = new DodgerCore(WIDTH, HEIGHT);

function broadcast(state: GameState) {
  const message = JSON.stringify({ type: "state", state });
  for (const client of wss.clients) {
    if (client.readyState === WebSocket.OPEN) {
      client.send(message);
    }
  }
}

wss.on("connection", (ws) => {
  console.log("Client connected");

  // Send the current state of the single game to the new client
  ws.send(JSON.stringify({ type: "state", state: game.getState() }));

  ws.on("message", (msg) => {
    try {
      const data = JSON.parse(msg.toString());

      let state: GameState;
      if (data.type === "step") {
        state = game.step(data.action as Action, FIXED_DT);
        broadcast(state);
      } else if (data.type === "restart") {
        state = game.step("RESTART", FIXED_DT);
        broadcast(state);
      }
    } catch (err) {
      console.error("Invalid message", err);
    }
  });

  ws.on("close", () => {
    console.log("Client disconnected");
  });
});
