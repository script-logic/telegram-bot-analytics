"""
Configuration management for Google Sheets LLM Analyzer.
Handles environment variables, validation, and Google credentials.
"""

import base64
import json
from functools import lru_cache

from google.oauth2.service_account import Credentials
from pydantic import (
    Field,
    SecretStr,
    field_validator,
)
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class AppConfig(BaseSettings):
    """
    Unified configuration class.
    Reads .env file and validates data.
    """

    # --- GOOGLE SHEETS SETTINGS ---
    spreadsheet_id: str = Field(
        ...,
        validation_alias="SPREADSHEET_ID",
        description="Google Sheet ID",
        min_length=10,
    )

    sheet_name: str = Field(
        "Sheet1",
        validation_alias="SHEET_NAME",
    )

    category_column: int = Field(
        3,
        validation_alias="CATEGORY_COLUMN",
        ge=1,
        le=26,
    )

    # --- GOOGLE CREDENTIALS ---
    google_credentials_base64: SecretStr = Field(
        ...,
        validation_alias="GOOGLE_CREDENTIALS_BASE64",
        min_length=50,
    )

    # --- OPENROUTER ---
    openrouter_api_key: SecretStr = Field(
        SecretStr(""),
        validation_alias="OPENROUTER_API_KEY",
    )

    openrouter_base_url: str = Field(
        "https://openrouter.ai/api/v1",
        validation_alias="OPENROUTER_BASE_URL",
    )

    openrouter_model: str = Field(
        "mistralai/devstral-2512:free",
        validation_alias="OPENROUTER_MODEL",
    )

    # --- APP SETTINGS ---
    debug: bool = Field(
        False,
        validation_alias="DEBUG",
    )

    # --- PYDANTIC ---
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- VALIDATORS ---
    @field_validator("spreadsheet_id")
    @classmethod
    def validate_spreadsheet_id(
        cls,
        v: str,
    ) -> str:
        if "your" in v:
            raise ValueError("SPREADSHEET_ID not set in .env file")
        return v.strip()

    @field_validator("google_credentials_base64")
    @classmethod
    def validate_creds(
        cls,
        v: SecretStr,
    ) -> SecretStr:
        val = v.get_secret_value()
        if not val or "your" in val:
            raise ValueError("GOOGLE_CREDENTIALS_BASE64 not set")

        # Validate Base64 and JSON
        try:
            decoded = base64.b64decode(
                val,
                validate=True,
            )
            data = json.loads(decoded)

            required = [
                "type",
                "project_id",
                "private_key",
                "client_email",
            ]
            if any(f not in data for f in required):
                raise ValueError(
                    f"JSON key missing required fields: {required}",
                )

        except Exception as e:
            raise ValueError(f"Error decoding Base64 key: {e}") from e

        return v

    # --- UTILITY METHODS ---
    @property
    def is_llm_enabled(self) -> bool:
        """Is AI enabled?"""
        key = self.openrouter_api_key.get_secret_value()
        return bool(key and "your" not in key)

    def get_google_credentials(self) -> Credentials:
        """Returns ready Google authentication object."""
        json_data = json.loads(
            base64.b64decode(
                self.google_credentials_base64.get_secret_value(),
            ),
        )
        return Credentials.from_service_account_info(
            json_data,
            scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
        )

    def get_service_email(self) -> str:
        """Get service account email for logs."""
        try:
            creds = json.loads(
                base64.b64decode(
                    self.google_credentials_base64.get_secret_value(),
                ),
            )
            return creds.get(
                "client_email",
                "unknown",
            )
        except Exception:
            return "error"


@lru_cache
def get_settings() -> AppConfig:
    """
    Creates configuration once and caches it (Singleton).
    """
    try:
        config = AppConfig()  # type: ignore

        if config.debug:
            print(
                "✅ Config loaded from .env\n"
                f"   Spreadsheet: {config.spreadsheet_id}\n"
                f"   Service Email: {config.get_service_email()}",
            )

        return config
    except Exception as e:
        print(f"❌ Error loading .env configuration: {e}")
        raise


config = get_settings()
