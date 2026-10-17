import os
import time
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import openai

app = FastAPI(title="Three-Persona Chatbot API")

API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if API_KEY:
    client = openai.OpenAI(api_key=API_KEY)
else:
    client = None

PERSONAS = {
    "friendly": {
        "name": "友好助理",
        "system": (
            "你是一个友好且耐心的助理。回答时语气温暖、鼓励，语言简洁易懂，尽量用中文。"
            "当有人发言时，以理解对方为先，给出实际建议或下一步可执行操作。"
            "示例风格：'没问题，我可以帮你……'。"
        ),
    },
    "analyst": {
        "name": "冷静分析家",
        "system": (
            "你是一个冷静的分析型专家。回答逻辑严密、逐点列出原因与建议，必要时说明利弊。"
            "语气正式、中性，适合做问题分析与方案比较。"
        ),
    },
    "playful": {
        "name": "戏谑专家",
        "system": (
            "你是一个幽默、略带戏谑但不冒犯人的角色。回答可以带些俏皮话或比喻，让对话更轻松。"
            "注意不触碰敏感话题与人身攻击。"
        ),
    },
}

SESSIONS: Dict[str, List[Dict]] = {}


class ChatRequest(BaseModel):
    session_id: str
    persona: str
    user: str
    message: str
    multi_reply: bool = False
    history_limit: int = 12
    model: Optional[str] = None


class ChatResponse(BaseModel):
    replies: List[Dict]


def build_messages_for_persona(
    session_history: List[Dict],
    persona_key: str,
    user_name: str,
    incoming_message: str,
    history_limit: int,
) -> List[Dict]:
    persona = PERSONAS[persona_key]
    messages = [{"role": "system", "content": persona["system"]}]

    recent_history = session_history[-history_limit:] if session_history else []
    for msg in recent_history:
        role = msg["role"]
        text = f"[{msg['who']}] {msg['text']}"
        messages.append({"role": role, "content": text})

    messages.append({"role": "user", "content": f"[{user_name}] {incoming_message}"})
    return messages


def call_openai(messages: List[Dict], model_name: str):
    if client is None:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured.")

    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        max_tokens=600,
        temperature=0.8,
    )
    content = response.choices[0].message.content or ""
    usage = getattr(response, "usage", None)
    return content, usage


@app.get("/health")
def health():
    return {"status": "ok", "persona_count": len(PERSONAS)}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if req.persona not in PERSONAS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown persona: {req.persona}. Use one of {list(PERSONAS.keys())}.",
        )

    if req.history_limit <= 0:
        req.history_limit = 1

    session = SESSIONS.setdefault(req.session_id, [])
    model_name = req.model or DEFAULT_MODEL
    replies: List[Dict] = []

    if req.multi_reply:
        for persona_key in PERSONAS:
            messages = build_messages_for_persona(
                session,
                persona_key,
                req.user,
                req.message,
                req.history_limit,
            )
            reply_text, usage = call_openai(messages, model_name)
            session.append({
                "role": "assistant",
                "who": PERSONAS[persona_key]["name"],
                "text": reply_text,
                "timestamp": time.time(),
            })
            replies.append({
                "persona": persona_key,
                "name": PERSONAS[persona_key]["name"],
                "reply": reply_text,
                "usage": usage.model_dump() if usage is not None else {},
            })
    else:
        messages = build_messages_for_persona(
            session,
            req.persona,
            req.user,
            req.message,
            req.history_limit,
        )
        reply_text, usage = call_openai(messages, model_name)
        session.append({
            "role": "assistant",
            "who": PERSONAS[req.persona]["name"],
            "text": reply_text,
            "timestamp": time.time(),
        })
        replies.append({
            "persona": req.persona,
            "name": PERSONAS[req.persona]["name"],
            "reply": reply_text,
            "usage": usage.model_dump() if usage is not None else {},
        })

    session.append({
        "role": "user",
        "who": req.user,
        "text": req.message,
        "timestamp": time.time(),
    })

    if len(session) > 400:
        del session[:-200]

    return {"replies": replies}


@app.post("/switch_persona")
def switch_persona(session_id: str, new_persona: str):
    if new_persona not in PERSONAS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown persona: {new_persona}. Use one of {list(PERSONAS.keys())}.",
        )
    return {"ok": True, "session_id": session_id, "persona": new_persona}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
