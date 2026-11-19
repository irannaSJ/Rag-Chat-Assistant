"""Groq-backed LLM client with true token streaming and fallback support."""

import os
import re
from typing import Generator
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

SYSTEM_PROMPT = (
    "You are a precise, helpful document assistant. "
    "Answer strictly from the provided context in clean Markdown. "
    "Never invent facts outside the context."
)


class LLMClient:
    def __init__(
        self,
        model_name: str | None = None,
        api_key: str | None = None,
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. Add it to your .env file before querying."
            )

        self.model_name = model_name or os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.fallback_model = os.getenv("GROQ_FALLBACK_MODEL", "llama-3.1-8b-instant")
        self.client = Groq(api_key=self.api_key)

    def _clean_response(self, text: str) -> str:
        cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
        return cleaned.strip()

    def generate(self, prompt: str) -> str:
        try:
            answer = self._complete_once(self.model_name, prompt)
            if answer:
                return answer
        except Exception:
            pass

        if self.model_name != self.fallback_model:
            try:
                answer = self._complete_once(self.fallback_model, prompt)
                if answer:
                    return answer
            except Exception as e:
                return f"LLM Error: {str(e)}"

        return "I couldn't find enough information in your uploaded sources to answer that."

    def _complete_once(self, model_name: str, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=1024,
        )
        raw = response.choices[0].message.content or ""
        return self._clean_response(raw)

    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        """Yield tokens in real time from Groq, falling back cleanly on failure."""
        models_to_try = [self.model_name]
        if self.fallback_model and self.fallback_model != self.model_name:
            models_to_try.append(self.fallback_model)

        last_error = None
        for model in models_to_try:
            try:
                stream = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=1024,
                    stream=True,
                )

                yielded_any = False
                for chunk in stream:
                    delta = chunk.choices[0].delta.content if chunk.choices else None
                    if delta:
                        yielded_any = True
                        yield delta

                if yielded_any:
                    return
            except Exception as exc:
                last_error = exc
                continue

        if last_error:
            yield f"\n\n*(Error generating response: {str(last_error)})*"
        else:
            yield "I couldn't find enough information in your uploaded sources to answer that."