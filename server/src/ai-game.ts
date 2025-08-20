import { DodgerCore } from "../../shared/core";
import { WebSocketServer } from "ws";

const WIDTH = 800;
const HEIGHT = 600;

const wss = new WebSocketServer({ port: 8080 });
console.log("AI WebSocket server running on ws://localhost:8080");

function broadcast(state: any) {
  for (const client of wss.clients) {
    if (client.readyState === 1) {
      client.send(JSON.stringify({ type: "state", state }));
    }
  }
}

wss.on("connection", (ws) => {
  console.log("Client connected");

  const game = new DodgerCore(WIDTH, HEIGHT);

  // Send initial state to new client
  ws.send(JSON.stringify({ type: "state", state: game.getState() }));

  ws.on("message", (msg) => {
    try {
      const data = JSON.parse(msg.toString());

      if (data.type === "step") {
        const state = game.step(data.action);
        broadcast(state); // <-- send to ALL clients
      } else if (data.type === "restart") {
        const state = game.step("RESTART");
        broadcast(state); // <-- send to ALL clients
      }
    } catch (err) {
      console.error("Invalid message", err);
    }
  });
});
