"""
Конфигурация приложения с Pydantic Settings.
Загружает .env автоматически, валидирует все настройки.
"""

import base64
import json
from typing import Any, Dict

from google.oauth2.service_account import Credentials
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GoogleSheetsConfig(BaseModel):
    """Конфигурация Google Sheets."""

    spreadsheet_id: str = Field(
        ...,
        description="ID Google Таблицы (из URL: /d/ID/edit)",
        min_length=10,
    )

    sheet_name: str = Field(
        "Заявки из Telegram Bot", description="Имя листа в таблице"
    )

    category_column: int = Field(
        3,
        ge=1,
        le=26,
        description="Номер столбца с категориями (A=1, B=2, ...)",
    )

    @field_validator("spreadsheet_id")
    @classmethod
    def validate_spreadsheet_id(cls, v: str) -> str:
        if not v or "ваш_id" in v:
            raise ValueError(
                "SPREADSHEET_ID должен быть указан. "
                "Получите из URL таблицы: /d/ВАШ_ID/edit"
            )
        return v.strip()


class LLMConfig(BaseModel):
    """Конфигурация LLM (OpenRouter/OpenAI)."""

    api_key: str = Field("", description="API ключ для OpenRouter или OpenAI")

    base_url: str = Field(
        "https://openrouter.ai/api/v1", description="Базовый URL API"
    )

    model: str = Field(
        "openai/gpt-3.5-turbo", description="Модель для использования"
    )

    @property
    def enabled(self) -> bool:
        """Включен ли LLM анализ."""
        return bool(self.api_key and "ваш_api_ключ" not in self.api_key)

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v:
            return v
        if "ваш_api_ключ" in v:
            raise ValueError(
                "OPENROUTER_API_KEY имеет значение по умолчанию. "
                "Получите ключ на https://openrouter.ai/"
            )
        return v.strip()


class GoogleCredentials(BaseModel):
    """Google Service Account credentials в Base64 формате."""

    credentials_base64: str = Field(
        ...,
        description="Base64 encoded JSON сервисного аккаунта",
        min_length=100,
    )

    @field_validator("credentials_base64")
    @classmethod
    def validate_and_decode_base64(cls, v: str) -> str:
        """Валидирует Base64 строку и декодирует JSON."""
        if not v or "ваш_base64" in v:
            raise ValueError(
                "GOOGLE_CREDENTIALS_BASE64 должен быть указан. "
                "Используйте: python scripts/encode_credentials.py service-account.json"
            )

        try:
            # Декодируем Base64
            decoded_bytes = base64.b64decode(v, validate=True)
            decoded_str = decoded_bytes.decode("utf-8")

            # Парсим JSON
            json_data = json.loads(decoded_str)

            # Проверяем обязательные поля сервисного аккаунта
            required_fields = [
                "type",
                "project_id",
                "private_key_id",
                "private_key",
                "client_email",
                "client_id",
            ]

            missing_fields = [
                field for field in required_fields if field not in json_data
            ]

            if missing_fields:
                raise ValueError(
                    f"Отсутствуют обязательные поля в JSON: {', '.join(missing_fields)}"
                )

            if json_data.get("type") != "service_account":
                raise ValueError("JSON не является сервисным аккаунтом Google")

            return v

        except base64.binascii.Error:
            raise ValueError("Некорректный формат Base64")
        except UnicodeDecodeError:
            raise ValueError("Не удалось декодировать Base64 как UTF-8")
        except json.JSONDecodeError as e:
            raise ValueError(f"Некорректный JSON формат: {e}")

    def get_credentials(self) -> Credentials:
        """Создает объект Google Credentials из Base64 строки."""
        decoded_bytes = base64.b64decode(self.credentials_base64)
        service_account_info = json.loads(decoded_bytes.decode("utf-8"))

        return Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )

    def get_client_email(self) -> str:
        """Возвращает email сервисного аккаунта."""
        decoded_bytes = base64.b64decode(self.credentials_base64)
        service_account_info = json.loads(decoded_bytes.decode("utf-8"))
        return service_account_info.get("client_email", "unknown")

    model_config = ConfigDict(frozen=True)


class AppConfig(BaseSettings):
    """Основная конфигурация приложения."""

    # Вложенные конфигурации
    google_sheets: GoogleSheetsConfig
    google_credentials: GoogleCredentials
    llm: LLMConfig

    # Общие настройки
    debug: bool = Field(False, description="Режим отладки")

    # Конфигурация Pydantic Settings
    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_prefix="",  # Без префикса для переменных
        validate_assignment=True,
    )

    @classmethod
    def load(cls) -> "AppConfig":
        """Загружает и валидирует конфигурацию."""
        try:
            config = cls()
            print("✅ Конфигурация успешно загружена")

            if config.debug:
                print(f"   Spreadsheet: {config.google_sheets.spreadsheet_id}")
                print(
                    f"   Service Account: {config.google_credentials.get_client_email()}"
                )
                print(f"   LLM enabled: {config.llm.enabled}")

            return config

        except Exception as e:
            print(f"❌ Ошибка загрузки конфигурации: {e}")
            print("\nПроверьте ваш .env файл:")
            print("1. Все ли обязательные поля заполнены?")
            print("2. Корректны ли Base64 credentials?")
            print("3. Указан ли правильный SPREADSHEET_ID?")
            raise


# Глобальный экземпляр конфигурации
try:
    config = AppConfig.load()
except Exception:
    # В случае ошибки создаем "пустой" конфиг для импорта
    # Реальная ошибка будет при попытке использования
    config = None
