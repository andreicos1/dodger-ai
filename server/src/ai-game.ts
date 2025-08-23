import { DodgerCore, Action, GameState } from "../../shared/core";
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

  let game: DodgerCore | null = null;
  let isSpectator = false;

  ws.on("message", (msg) => {
    try {
      const data = JSON.parse(msg.toString());

      if (data.type === "watch") {
        isSpectator = true;
        console.log("Client is a spectator");
        if (sharedGame) {
          ws.send(
            JSON.stringify({ type: "state", state: sharedGame.getState() })
          );
        } else {
          ws.send(
            JSON.stringify({
              type: "error",
              message: "No active game to watch",
            })
          );
        }
        return;
      }

      if (data.type === "step") {
        if (!game) {
          game = new DodgerCore(WIDTH, HEIGHT);
          games.set(ws, game);

          if (!sharedGame) {
            sharedGame = game;
            sharedGameOwner = ws;
          }
        }

        const state = game.step(data.action as Action, FIXED_DT);

        ws.send(JSON.stringify({ type: "state", state }));

        if (game === sharedGame) {
          for (const client of wss.clients) {
            if (client !== ws && client.readyState === WebSocket.OPEN) {
              if (client !== sharedGameOwner) {
                client.send(JSON.stringify({ type: "state", state }));
              }
            }
          }
        }
      } else if (data.type === "restart") {
        if (!game) {
          game = new DodgerCore(WIDTH, HEIGHT);
          games.set(ws, game);

          if (!sharedGame) {
            sharedGame = game;
            sharedGameOwner = ws;
          }
        }

        const state = game.step("RESTART", FIXED_DT);
        ws.send(JSON.stringify({ type: "state", state }));

        if (game === sharedGame) {
          for (const client of wss.clients) {
            if (client !== ws && client.readyState === WebSocket.OPEN) {
              if (client !== sharedGameOwner) {
                client.send(JSON.stringify({ type: "state", state }));
              }
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

    if (game) {
      games.delete(ws);
      if (game === sharedGame) {
        sharedGame = null;
        sharedGameOwner = null;
        console.log("Shared game owner disconnected, clearing shared game");
      }
    }
  });
});
