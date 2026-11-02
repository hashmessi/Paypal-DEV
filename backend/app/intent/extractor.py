"""Multi-tier Intent Extractor with caching and deadline resolution."""

from datetime import timedelta
import json
import logging
from typing import Literal, Optional, cast
from sqlalchemy import select
from sqlalchemy.orm import Session

try:
    import httpx
except ImportError:
    import httpx2 as httpx

from app.core.canon import sha256_hex
from app.core.clock import Clock, SystemClock
from app.core.config import settings
from app.core.models import ExtractionCache
from app.intent.fallback import extract_fallback_constraints
from app.intent.models import ExtractedIntent, IntentConstraints

logger = logging.getLogger(__name__)

INTENT_EXTRACTION_SYSTEM_PROMPT = """You are an expert purchase intent parser.
Extract the buyer's purchase instruction into strict JSON format matching this schema:
{
  "product_type": "string",
  "condition": "new" | "refurbished" | "any",
  "color": "string" | null,
  "max_total_cents": integer (total dollars converted to cents, e.g. $100 -> 10000),
  "currency": "USD",
  "deliver_within_days": integer (default 5 if unspecified),
  "substitutions_allowed": boolean (default false)
}
Return only pure JSON without markdown code fences or conversational text.
"""


class IntentExtractor:
    """Extracts typed constraints with LLM tiering, caching, and deterministic fallback."""

    def __init__(self, db: Optional[Session] = None, clock: Optional[Clock] = None) -> None:
        self.db = db
        self.clock = clock or SystemClock()

    def _hash_instruction(self, instruction: str) -> str:
        norm = " ".join(instruction.lower().strip().split())
        return sha256_hex(norm)

    async def _try_gemini(self, instruction: str) -> Optional[IntentConstraints]:
        if not settings.GEMINI_API_KEY:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": INTENT_EXTRACTION_SYSTEM_PROMPT},
                        {"text": f"Instruction: {instruction}"},
                    ]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.0,
            },
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                text_content = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text_content)
                return IntentConstraints(**parsed)
        except Exception as err:
            logger.warning("Gemini intent extraction failed, falling back: %s", err)

        return None

    async def _try_openrouter(self, instruction: str) -> Optional[IntentConstraints]:
        if not settings.OPENROUTER_API_KEY:
            return None

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "meta-llama/llama-3.3-70b-instruct:free",
            "messages": [
                {"role": "system", "content": INTENT_EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": instruction},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=headers, json=payload, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                return IntentConstraints(**parsed)
        except Exception as err:
            logger.warning("OpenRouter intent extraction failed, falling back: %s", err)

        return None

    async def extract(self, instruction: str) -> ExtractedIntent:
        """Extract constraints with cache lookup -> AI -> deterministic fallback."""
        instruction_hash = self._hash_instruction(instruction)

        # 1. Check extraction cache
        if self.db:
            stmt = select(ExtractionCache).where(ExtractionCache.instruction_hash == instruction_hash).limit(1)
            cached = self.db.execute(stmt).scalars().first()
            if cached:
                logger.info("Intent extraction cache hit: %s", instruction_hash[:8])
                constraints = IntentConstraints(**json.loads(cached.constraints_json))
                resolved_deadline = self.clock.today() + timedelta(days=constraints.deliver_within_days)
                return ExtractedIntent(
                    constraints=constraints,
                    source=cast(Literal["ai", "fallback"], cached.source),
                    instruction=instruction,
                    resolved_deadline=resolved_deadline,
                    instruction_hash=instruction_hash,
                )

        # 2. Try Primary AI (Gemini)
        constraints = await self._try_gemini(instruction)
        source = "ai"

        # 3. Try Secondary AI (OpenRouter)
        if not constraints:
            constraints = await self._try_openrouter(instruction)

        # 4. Fallback: Deterministic Regex Extractor
        if not constraints:
            constraints = extract_fallback_constraints(instruction)
            source = "fallback"

        # 5. Resolve relative deadline in code (INTENT-02)
        resolved_deadline = self.clock.today() + timedelta(days=constraints.deliver_within_days)

        # 6. Save to extraction cache
        if self.db:
            try:
                cache_entry = ExtractionCache(
                    instruction_hash=instruction_hash,
                    instruction_text=instruction,
                    constraints_json=constraints.model_dump_json(),
                    source=source,
                )
                self.db.add(cache_entry)
                self.db.commit()
            except Exception as err:
                logger.debug("Failed saving extraction cache entry: %s", err)
                self.db.rollback()

        return ExtractedIntent(
            constraints=constraints,
            source=source,
            instruction=instruction,
            resolved_deadline=resolved_deadline,
            instruction_hash=instruction_hash,
        )
