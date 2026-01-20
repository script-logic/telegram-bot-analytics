"""
LLM integration for text request analysis.
Supports OpenRouter and OpenAI API.
"""

import json
import time
from dataclasses import dataclass
from typing import Any

from openai import (
    APIConnectionError,
    APIError,
    OpenAI,
    RateLimitError,
)

from config import config


@dataclass
class LLMAnalysis:
    """LLM analysis result."""

    priority: str
    summary: str
    recommendation: str
    raw_response: str | None
    processing_time: float

    @property
    def priority_emoji(self) -> str:
        """Returns emoji for priority."""
        emoji_map = {
            "high": "🔴",
            "medium": "🟡",
            "low": "🟢",
        }
        return emoji_map.get(self.priority.lower(), "⚪")

    @property
    def priority_text(self) -> str:
        """Returns priority text."""
        text_map = {
            "high": "HIGH",
            "medium": "MEDIUM",
            "low": "LOW",
        }
        return text_map.get(self.priority.lower(), "UNKNOWN")


class LLMProcessor:
    """Processor for working with LLM."""

    def __init__(self):
        if config is None:
            raise ValueError("Configuration not loaded")

        self.config = config

        if not self.config.is_llm_enabled:
            self.client = None
            self._enabled = False
            return

        self._enabled = True

        try:
            self.client = OpenAI(
                base_url=self.config.openrouter_base_url,
                api_key=self.config.openrouter_api_key.get_secret_value(),
                timeout=30.0,
                max_retries=2,
            )
        except Exception as e:
            print(f"⚠️  LLM client initialization error: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Is LLM available for use?"""
        return self._enabled and self.client is not None

    def analyze_request(
        self,
        choice: str,
        category: str = "",
    ) -> LLMAnalysis | None:
        """
        Analyzes request description using LLM.

        Args:
            choice: Request text
            category: Request category

        Returns:
            LLMAnalysis or None in case of error
        """
        if not self.is_available():
            return None

        if not choice or len(choice.strip()) < 5:
            return None

        start_time = time.time()

        try:
            # System prompt for request analysis.
            # Hardcoded for now, can be made dynamic in the future
            system_prompt = """
You are an experienced technical support specialist.
Analyze user's problem description and provide structured analysis.

Analysis steps:
1. Determine request priority (high/medium/low) based on:
    - HIGH: critical problems (system down, data loss, security threats)
    - MEDIUM: important issues with temporary workarounds, functionality
      questions, errors in non-critical components
    - LOW: informational requests, documentation questions, improvement
      suggestions
2. Formulate brief summary of the problem (1-2 sentences)
3. Provide solution recommendation or next step

Response format - strictly JSON:
{
    "priority": "high|medium|low",
    "summary": "brief problem summary in English",
    "recommendation": "specific solution recommendation in English"
}

Be specific in recommendations. If problem requires urgent solution, mention
it."""

            user_prompt = f"""
User request:

[
Category:
{category if category else "Not specified"}

Problem description:
{choice}
]

Analyze this request according to instructions above."""

            if self.client:
                response = self.client.chat.completions.create(
                    model=self.config.openrouter_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.3,
                    max_tokens=500,
                    response_format={"type": "json_object"},
                )

            content = response.choices[0].message.content

            if not content:
                raise Exception("LLM returned empty response")

            result = json.loads(content)

            processing_time = time.time() - start_time
            print("Analyzing next request...")

            return LLMAnalysis(
                priority=result.get("priority", "medium").lower(),
                summary=result.get("summary", ""),
                recommendation=result.get("recommendation", ""),
                raw_response=content,
                processing_time=processing_time,
            )

        except json.JSONDecodeError as e:
            print(f"❌ LLM returned invalid JSON: {e}")
            if config and config.debug:
                print(f"   LLM response: {content}")
            return None
        except RateLimitError:
            print("⚠️  LLM API rate limit exceeded")
            return None
        except APIConnectionError:
            print("⚠️  LLM API connection error")
            return None
        except APIError as e:
            print(f"⚠️  LLM API error: {e}")
            return None
        except Exception as e:
            print(f"⚠️  Unexpected error in LLM analysis: {e}")
            return None

    def analyze_multiple_requests(
        self,
        requests: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Analyzes multiple requests with rate limiting.

        Args:
            requests: List of requests for analysis

        Returns:
            List of requests with analysis results
        """
        if not self.is_available():
            print("❌  LLM analysis disabled (no API key)")
            return []

        if not requests:
            return []

        analyzed_requests = []
        total_requests = len(requests)

        print(f"🤖 Starting analysis of {total_requests} requests via LLM...")

        for i, request in enumerate(requests, 1):
            print(f"   Analyzing request {i}/{total_requests}...", end="\r")

            analysis = self.analyze_request(
                choice=request.get("choice", ""),
                category=request.get("category", ""),
            )

            if analysis:
                request["llm_analysis"] = analysis
                analyzed_requests.append(request)

                # Small delay between requests to avoid rate limits
                if i < total_requests:
                    time.sleep(0.5)
            else:
                request["llm_analysis"] = None

        print(
            f"✅ Analyzed {len(analyzed_requests)} out of {total_requests}"
            " requests"
        )

        return analyzed_requests

    def test_connection(self) -> bool:
        """Tests connection to LLM API."""
        if not self._enabled:
            print("❌  LLM disabled (no API key in configuration)")
            return False

        if not self.client:
            print("❌ LLM client not initialized")
            return False

        try:
            # Simple request to test connection
            response = self.client.chat.completions.create(
                model=self.config.openrouter_model,
                messages=[
                    {
                        "role": "user",
                        "content": "Reply with one word: 'Working'",
                    }
                ],
                max_tokens=10,
                timeout=10.0,
            )

            result = response.choices[0].message.content
            print(
                f"✅ LLM connection successful: {self.config.openrouter_model}"
            )
            print(f"   Response: {result}")
            return True

        except RateLimitError:
            print("❌ LLM API rate limit exceeded")
            return False
        except APIConnectionError:
            print("❌ LLM API connection error. Check network and API key")
            return False
        except APIError as e:
            print(f"❌ LLM API error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error testing LLM: {e}")
            return False
