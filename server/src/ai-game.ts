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
let sharedGame: DodgerCore | null = null;
let sharedGameOwner: WebSocket | null = null;

wss.on("connection", (ws) => {
  console.log("Client connected");

  let game = new DodgerCore(WIDTH, HEIGHT);
  games.set(ws, game);
  let isSpectator = false;

  ws.on("message", (msg) => {
    try {
      const data = JSON.parse(msg.toString());

      if (data.type === "watch") {
        isSpectator = true;
        if (sharedGame) {
          ws.send(
            JSON.stringify({ type: "state", state: sharedGame.getState() })
          );
        } else {
          ws.send(
            JSON.stringify({
              type: "error",
              message: "No active shared game to watch",
            })
          );
        }
        return;
      }

      if (data.type === "become_shared_owner") {
        // This client’s game becomes the shared game
        sharedGame = game;
        sharedGameOwner = ws;
        console.log("Client became shared game owner");
        return;
      }

      if (data.type === "step") {
        const state = game.step(data.action as Action, FIXED_DT);
        ws.send(JSON.stringify({ type: "state", state }));

        // If this client is the shared owner, broadcast to spectators
        if (game === sharedGame) {
          for (const client of wss.clients) {
            if (
              client !== ws &&
              client.readyState === WebSocket.OPEN &&
              client !== sharedGameOwner
            ) {
              client.send(JSON.stringify({ type: "state", state }));
            }
          }
        }
      } else if (data.type === "restart") {
        game = new DodgerCore(WIDTH, HEIGHT);
        games.set(ws, game);

        if (ws === sharedGameOwner) {
          sharedGame = game;
          console.log("Shared game restarted");
        }

        const state = game.step("RESTART", FIXED_DT);
        ws.send(JSON.stringify({ type: "state", state }));

        // Broadcast to spectators if this is the shared game
        if (ws === sharedGameOwner) {
          for (const client of wss.clients) {
            if (client !== ws && client.readyState === WebSocket.OPEN) {
              client.send(JSON.stringify({ type: "state", state }));
            }
          }
        }
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

    if (game === sharedGame) {
      sharedGame = null;
      sharedGameOwner = null;
      console.log("Shared game owner disconnected, clearing shared game");
    }
  });
});
