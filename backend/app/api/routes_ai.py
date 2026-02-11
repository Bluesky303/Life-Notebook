from datetime import datetime
from decimal import InvalidOperation
from uuid import uuid4

from fastapi import APIRouter

from app.schemas.ai import AIChatRequest, AIChatResponse, AIParseRecordRequest, AIParseRecordResponse

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/chat", response_model=AIChatResponse)
def chat(payload: AIChatRequest) -> AIChatResponse:
    session_id = payload.session_id or str(uuid4())
    reply = (
        "[stub] AI gateway received your input. "
        "Next step: connect provider clients and structured parsers for tasks/assets/knowledge."
    )
    return AIChatResponse(provider=payload.provider, session_id=session_id, reply=reply)


def _extract_amount(text: str) -> str | None:
    tokens = text.replace("¥", " ").replace("元", " ").split()
    for token in tokens:
        try:
            amount = float(token)
            if amount > 0:
                return f"{amount:.2f}"
        except (ValueError, InvalidOperation):
            continue
    return None


@router.post("/parse-record", response_model=AIParseRecordResponse)
def parse_record(payload: AIParseRecordRequest) -> AIParseRecordResponse:
    text = payload.text.strip()
    lower_text = text.lower()

    detected_type = "feed"
    suggested_category = "其他"
    extracted_amount = _extract_amount(text)
    extracted_time: str | None = None

    if any(keyword in text for keyword in ["买", "花", "支出", "消费", "吃饭"]) or "expense" in lower_text:
        detected_type = "transaction"
        suggested_category = "消费记录"
    elif any(keyword in text for keyword in ["收入", "工资", "到账"]) or "income" in lower_text:
        detected_type = "transaction"
        suggested_category = "收入"
    elif any(keyword in text for keyword in ["任务", "提醒", "明天", "今天", "周", "点"]):
        detected_type = "task"
        suggested_category = "任务"
    elif any(keyword in text for keyword in ["芯片", "知识", "记录", "词条", "博客"]):
        detected_type = "knowledge"
        suggested_category = "知识"

    if "明天" in text:
        extracted_time = "tomorrow"
    elif "今天" in text:
        extracted_time = datetime.now().date().isoformat()

    return AIParseRecordResponse(
        detected_type=detected_type,
        suggested_category=suggested_category,
        normalized_text=text,
        extracted_amount=extracted_amount,
        extracted_time=extracted_time,
    )
