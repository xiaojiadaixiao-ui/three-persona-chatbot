# three-persona-chatbot
A demo FastAPI chatbot with three selectable personas (friendly, analyst, and playful).

## Overview
This project exposes a simple API for generating responses with three different personas:

- friendly
- analyst
- playful

It also supports a `multi_reply` mode to compare how each persona would answer the same message.

## Tech stack
- Python
- FastAPI
- OpenAI Python SDK

## Setup

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the example environment file:

```bash
cp .env.example .env
```

4. Add your OpenAI key in `.env`:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

5. Start the app:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## Health check

```bash
curl http://127.0.0.1:8000/health
```

## Example request: single persona

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-1",
    "persona": "friendly",
    "user": "Alice",
    "message": "我想提升沟通表达，能给我一些建议吗？",
    "multi_reply": false
  }'
```

## Example request: all three personas

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo-1",
    "persona": "friendly",
    "user": "Bob",
    "message": "我在准备面试，需要快速提升表达能力。",
    "multi_reply": true
  }'
```

## Notes
- Chat history is stored in memory for demo purposes.
- For production, replace the in-memory storage with Redis or a database.
- You can adjust the default OpenAI model through `OPENAI_MODEL`.
