import os
import time
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import openai

app = FastAPI(title="Business Three-Persona Chatbot API")

API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if API_KEY:
    client = openai.OpenAI(api_key=API_KEY)
else:
    client = None

PERSONAS = {
    "sales": {
        "name": "销售顾问",
        "system": (
            "你是一个商业销售顾问。重点关注客户价值、业务需求、目标场景和成交路径。"
            "输出时要专业且有策略性，优先突出客户痛点、产品价值和下一步行动建议。"
            "语气：专业、主动、信任感强。"
            "如果用户是客户或业务方，帮助其识别购买动机并给出可落地的合作建议。"
        ),
    },
    "support": {
        "name": "客服经理",
        "system": (
            "你是一名客户支持与服务经理。重点关注用户体验、问题解决、客户留存和服务效率。"
            "回答时要温和、务实、清晰地拆解问题，优先给出解决步骤、沟通话术和风险提醒。"
            "语气：耐心、贴近客户、解决导向。"
            "对投诉、延迟、服务问题优先给稳妥处理建议。"
        ),
    },
    "ops": {
        "name": "运营总监",
        "system": (
            "你是一名运营总监，负责业务运营、流程优化、团队协作和增长策略。"
            "输出时要强调业务目标、效率指标、流程执行和风险控制。"
            "语气：务实、理性、结果导向。"
            "如果用户在讨论业务规划、流程优化或团队协作，优先给出执行路径和落地方案。"
        ),
    },
}

SESSIONS: Dict[str, List[Dict]] = {}


class ChatRequest(BaseModel):
    session_id: str
    persona: str
    user: str
    message: str
    business_context: Optional[str] = None
    company: Optional[str] = None
    industry: Optional[str] = None
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
    business_context: Optional[str],
    company: Optional[str],
    industry: Optional[str],
    history_limit: int,
) -> List[Dict]:
    persona = PERSONAS[persona_key]
    messages = [{"role": "system", "content": persona["system"]}]

    context_text = []
    if company:
        context_text.append(f"公司：{company}")
    if industry:
        context_text.append(f"行业：{industry}")
    if business_context:
        context_text.append(f"业务背景：{business_context}")

    if context_text:
        messages.append({"role": "system", "content": "\n".join(context_text)})

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
        max_tokens=700,
        temperature=0.7,
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
                req.business_context,
                req.company,
                req.industry,
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
            req.business_context,
            req.company,
            req.industry,
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
