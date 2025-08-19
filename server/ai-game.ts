import { DodgerCore } from "../shared/core";
import { WebSocketServer } from "ws";

const WIDTH = 800;
const HEIGHT = 600;

const game = new DodgerCore(WIDTH, HEIGHT);

const wss = new WebSocketServer({ port: 8080 });
console.log("AI WebSocket server running on ws://localhost:8080");

function broadcast(state: any) {
  for (const client of wss.clients) {
    if (client.readyState === 1) {
      client.send(JSON.stringify({ type: "state", state }));
    }
  }
}

setInterval(() => {
  // Advance game with last action (default NONE)
  game.step("NONE");
  broadcast(game.getState());
}, 1000 / 60); // 60fps tick

wss.on("connection", (ws) => {
  console.log("Client connected");

  ws.on("message", (msg) => {
    try {
      const data = JSON.parse(msg.toString());
      if (data.type === "step") {
        const state = game.step(data.action);
        broadcast(state);
      } else if (data.type === "restart") {
        game.step("RESTART");
        broadcast(game.getState());
      }
    } catch (err) {
      console.error("Invalid message", err);
    }
  });
});
