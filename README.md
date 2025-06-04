# AiGentsy AME Runtime — MetaUpgrade24

This repo powers AiGentsy’s Autonomous Market Engine (AME) backend, enabling runtime logic for agent minting and behavior.

## 🌐 API Endpoint

After deployment, POST requests can be sent to:
```
/api/trigger
```
Payload:
```json
{
  "input": "Minting agent with trait: Autonomous Mapper..."
}
```
Response:
```json
{
  "output": "[Autonomous Output Triggered] Role action initiated: Minting agent..."
}
```

## 🚀 Deployment Steps (Railway)

1. Fork this repo to your GitHub
2. Sign up at [https://railway.app](https://railway.app)
3. Click "New Project" > "Deploy from GitHub"
4. Link your forked repo
5. Add environment variable:
   - `OPENAI_API_KEY` → your real key
6. Click Deploy

## 🔐 Required Environment Variables
```
OPENAI_API_KEY=sk-xxx...
```

## 🧠 Powered By
- FastAPI
- LangGraph
- OpenAI
- AiGentsy MetaUpgrade24
