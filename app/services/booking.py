

import json
import re
from datetime import date, time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import InterviewBooking
from app.schemas.schemas import BookingResponse
from groq import AsyncGroq

_EXTRACTION_SYSTEM_PROMPT = """\
You are an assistant that extracts interview booking information from user messages.

If the message contains a request to book/schedule an interview with ALL of the following:
  - name
  - email
  - date (in any format)
  - time (in any format)

then respond ONLY with a valid JSON object:
{
  "has_booking": true,
  "name": "<full name>",
  "email": "<email address>",
  "date": "<YYYY-MM-DD>",
  "time": "<HH:MM>",
  "notes": "<any additional notes or null>"
}

If the message is a booking request but is missing required fields, respond:
{
  "has_booking": false,
  "missing_fields": ["<field1>", "<field2>"]
}

If the message is NOT a booking request, respond:
{"has_booking": false}

Do not include any other text. Return only the JSON object.
"""


async def detect_and_save_booking(
    *,
    session_id: str,
    user_message: str,
    db: AsyncSession,
) -> tuple[BookingResponse | None, str | None]:
   
    client = AsyncGroq(api_key=settings.GROQ_API_KEY)

    response = await client.chat.completions.create(
    model=settings.GROQ_CHAT_MODEL,
    temperature=0,
    messages=[
        {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ],
)

    raw = response.choices[0].message.content or "{}"
    try:
        data: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError:
        return None, None

    if not data.get("has_booking"):
        missing = data.get("missing_fields")
        if missing:
            prompt = (
                f"To complete your interview booking I still need: "
                f"{', '.join(missing)}. Could you provide those?"
            )
            return None, prompt
        return None, None

    # Parse and validate date/time
    try:
        interview_date = date.fromisoformat(data["date"])
        interview_time = time.fromisoformat(data["time"])
    except (KeyError, ValueError) as exc:
        return None, f"I could not parse the date or time from your message ({exc}). Please use YYYY-MM-DD and HH:MM format."

    booking = InterviewBooking(
        session_id=session_id,
        name=data["name"],
        email=data["email"],
        interview_date=interview_date,
        interview_time=interview_time,
        notes=data.get("notes"),
    )
    db.add(booking)
    await db.flush()

    return BookingResponse.model_validate(booking), None
