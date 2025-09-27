Pixi JS Dodger App.

With RL training

1. Start frontend:

```
cd app
npm run dev
```

2. Start listener ws server

```
cd server
npx ts-node ./src/ai-game.ts
```

3. Start evaluation ws server

```
cd ai-training
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```
