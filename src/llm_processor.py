"""
Интеграция с LLM для анализа текста заявок.
Поддерживает OpenRouter и OpenAI API.
"""

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from openai import APIConnectionError, APIError, OpenAI, RateLimitError

from config import config


@dataclass
class LLMAnalysis:
    """Результат анализа LLM."""

    priority: str  # "high", "medium", "low"
    summary: str
    recommendation: str
    raw_response: str
    processing_time: float  # Время обработки в секундах

    @property
    def priority_emoji(self) -> str:
        """Возвращает эмодзи для приоритета."""
        emoji_map = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        return emoji_map.get(self.priority.lower(), "⚪")

    @property
    def priority_text(self) -> str:
        """Возвращает текст приоритета на русском."""
        text_map = {"high": "ВЫСОКИЙ", "medium": "СРЕДНИЙ", "low": "НИЗКИЙ"}
        return text_map.get(self.priority.lower(), "НЕИЗВЕСТНО")


class LLMProcessor:
    """Процессор для работы с LLM."""

    def __init__(self):
        if config is None:
            raise ValueError("Конфигурация не загружена")

        self.config = config.llm

        if not self.config.enabled:
            self.client = None
            self._enabled = False
            return

        self._enabled = True

        try:
            self.client = OpenAI(
                base_url=self.config.base_url,
                api_key=self.config.api_key,
                timeout=30.0,
                max_retries=2,
            )
        except Exception as e:
            print(f"⚠️  Ошибка инициализации LLM клиента: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Доступен ли LLM для использования."""
        return self._enabled and self.client is not None

    def analyze_request(
        self, description: str, category: str = ""
    ) -> Optional[LLMAnalysis]:
        """
        Анализирует описание заявки с помощью LLM.

        Args:
            description: Текст заявки
            category: Категория заявки

        Returns:
            LLMAnalysis или None в случае ошибки
        """
        if not self.is_available():
            return None

        if not description or len(description.strip()) < 5:
            return None

        start_time = time.time()

        try:
            # Системный промпт для анализа заявок
            system_prompt = """Ты — опытный специалист технической поддержки. 
            Анализируй описание проблемы пользователя и предоставляй структурированный анализ.

            Шаги анализа:
            1. Определи приоритет заявки (high/medium/low) на основе:
               - HIGH: критические проблемы (система не работает, потеря данных, угрозы безопасности)
               - MEDIUM: важные проблемы с временным решением, вопросы по функционалу, ошибки в некритичных компонентах
               - LOW: информационные запросы, вопросы по документации, предложения по улучшению
            
            2. Сформулируй краткую суть проблемы (1-2 предложения)
            3. Предложи рекомендацию по решению или следующий шаг
            
            Формат ответа - строго JSON:
            {
                "priority": "high|medium|low",
                "summary": "краткая суть проблемы на русском языке",
                "recommendation": "конкретная рекомендация по решению на русском языке"
            }
            
            Будь конкретным в рекомендациях. Если проблема требует срочного решения, укажи это."""

            user_prompt = f"""Заявка пользователя:
            
            Категория: {category if category else 'Не указана'}
            
            Описание проблемы:
            {description}
            
            Проанализируй эту заявку согласно инструкциям выше."""

            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"},
            )

            # Парсим JSON-ответ
            content = response.choices[0].message.content
            result = json.loads(content)

            processing_time = time.time() - start_time

            return LLMAnalysis(
                priority=result.get("priority", "medium").lower(),
                summary=result.get("summary", ""),
                recommendation=result.get("recommendation", ""),
                raw_response=content,
                processing_time=processing_time,
            )

        except json.JSONDecodeError as e:
            print(f"❌ LLM вернул невалидный JSON: {e}")
            if config and config.debug:
                print(f"   Ответ LLM: {content[:200]}...")
            return None
        except RateLimitError:
            print("⚠️  Превышен лимит запросов к LLM API")
            return None
        except APIConnectionError:
            print("⚠️  Ошибка подключения к LLM API")
            return None
        except APIError as e:
            print(f"⚠️  Ошибка LLM API: {e}")
            return None
        except Exception as e:
            print(f"⚠️  Неожиданная ошибка при анализе LLM: {e}")
            return None

    def analyze_multiple_requests(
        self, requests: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Анализирует несколько заявок с ограничением скорости.

        Args:
            requests: Список заявок для анализа

        Returns:
            Список заявок с результатами анализа
        """
        if not self.is_available():
            print("ℹ️  LLM анализ отключен (нет API ключа)")
            return []

        if not requests:
            return []

        analyzed_requests = []
        total_requests = len(requests)

        print(f"🤖 Начинаю анализ {total_requests} заявок через LLM...")

        for i, request in enumerate(requests, 1):
            print(f"   Анализ заявки {i}/{total_requests}...", end="\r")

            analysis = self.analyze_request(
                description=request.get("description", ""),
                category=request.get("category", ""),
            )

            if analysis:
                request["llm_analysis"] = analysis
                analyzed_requests.append(request)

                # Небольшая задержка между запросами для избежания rate limits
                if i < total_requests:
                    time.sleep(0.5)
            else:
                request["llm_analysis"] = None

        print(
            f"✅ Проанализировано {len(analyzed_requests)} из {total_requests} заявок"
        )

        return analyzed_requests

    def test_connection(self) -> bool:
        """Проверяет подключение к LLM API."""
        if not self._enabled:
            print("ℹ️  LLM отключен (нет API ключа в конфигурации)")
            return False

        if not self.client:
            print("❌ LLM клиент не инициализирован")
            return False

        try:
            # Простой запрос для проверки подключения
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {
                        "role": "user",
                        "content": "Ответь одним словом: 'Работаю'",
                    }
                ],
                max_tokens=10,
                timeout=10.0,
            )

            result = response.choices[0].message.content.strip()
            print(f"✅ Подключение к LLM успешно ({self.config.model})")
            print(f"   Ответ: {result}")
            return True

        except RateLimitError:
            print("❌ Превышен лимит запросов к LLM API")
            return False
        except APIConnectionError:
            print("❌ Ошибка подключения к LLM API. Проверьте сеть и API ключ")
            return False
        except APIError as e:
            print(f"❌ Ошибка LLM API: {e}")
            return False
        except Exception as e:
            print(f"❌ Неожиданная ошибка при проверке LLM: {e}")
            return False
