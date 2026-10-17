# three-persona-chatbot
Business-oriented multi-persona chatbot for customer conversations and internal business support.

## Overview
This project exposes a lightweight FastAPI API for business-facing chat interactions with three role-based personas:

- sales
- support
- ops

Each persona has a different business focus:
- Sales: customer value, deal strategy, stakeholder alignment
- Support: customer experience, issue handling, retention
- Ops: execution, process design, efficiency and metrics

It also supports a `multi_reply` mode to compare how each persona would respond to the same business scenario.

## Tech stack
- Python
- FastAPI
- OpenAI SDK

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

## Example request: sales persona

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "biz-demo-1",
    "persona": "sales",
    "user": "Alice",
    "company": "Apex Digital",
    "industry": "SaaS",
    "business_context": "我们希望提升客户留存并扩展企业客户渠道。",
    "message": "我们想更好地卖给企业客户，应该怎么做？",
    "multi_reply": false
  }'
```

## Example request: compare all three personas

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "biz-demo-2",
    "persona": "sales",
    "user": "Bob",
    "company": "NovaWorks",
    "industry": "制造业",
    "business_context": "团队在做新产品落地，客户反馈慢，流程不清晰。",
    "message": "我们现在要做业务优化，应该先处理什么？",
    "multi_reply": true
  }'
```

## Business use cases

- Sales pitch and customer discovery
- Customer support response strategies
- Internal business process optimization
- Cross-functional team communication
- Operational risk and service improvement planning

## Notes
- Chat history is stored in memory for demo purposes.
- For production, replace the in-memory storage with Redis or a database.
- You can adjust the default model in `.env` using `OPENAI_MODEL`.
