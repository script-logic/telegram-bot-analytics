"""
Клиент для работы с Google Sheets API.
"""

import json
from typing import Any, List, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import config


class GoogleSheetsError(Exception):
    """Базовое исключение для ошибок Google Sheets."""

    pass


class GoogleSheetsClient:
    """Клиент для работы с Google Sheets API."""

    def __init__(self):
        if config is None:
            raise GoogleSheetsError(
                "Конфигурация не загружена. Проверьте .env файл."
            )

        self.config = config.google_sheets
        self._service = None

        try:
            self.credentials = config.google_credentials.get_credentials()
        except Exception as e:
            raise GoogleSheetsError(f"Ошибка загрузки credentials: {e}")

    def _get_service(self):
        """Создает и возвращает сервис Google Sheets."""
        if self._service is None:
            try:
                self._service = build(
                    "sheets",
                    "v4",
                    credentials=self.credentials,
                    cache_discovery=False,
                )
            except Exception as e:
                raise GoogleSheetsError(
                    f"Ошибка создания сервиса Google Sheets: {e}"
                )

        return self._service

    def fetch_data(self) -> List[List[Any]]:
        """
        Получает данные из Google Таблицы.

        Returns:
            Список строк таблицы (первая строка - заголовки)

        Raises:
            GoogleSheetsError: При ошибке подключения или чтения
        """
        try:
            service = self._get_service()
            sheet = service.spreadsheets()

            # Определяем диапазон для чтения
            range_name = f"{self.config.sheet_name}!A:Z"

            # Выполняем запрос
            result = (
                sheet.values()
                .get(
                    spreadsheetId=self.config.spreadsheet_id,
                    range=range_name,
                    valueRenderOption="FORMATTED_VALUE",
                    dateTimeRenderOption="FORMATTED_STRING",
                )
                .execute()
            )

            values = result.get("values", [])

            if not values:
                print("📭 Таблица пуста или не содержит данных.")
                return []

            print(f"✅ Загружено {len(values)} строк из Google Таблицы")
            return values

        except HttpError as e:
            error_details = json.loads(e.content.decode("utf-8"))
            error_msg = error_details.get("error", {}).get("message", str(e))

            if e.resp.status == 404:
                raise GoogleSheetsError(
                    f"Таблица не найдена. Проверьте SPREADSHEET_ID: {error_msg}"
                )
            elif e.resp.status == 403:
                raise GoogleSheetsError(
                    f"Нет доступа к таблице. Убедитесь, что "
                    f"'{config.google_credentials.get_client_email()}' "
                    f"имеет доступ к таблице. Ошибка: {error_msg}"
                )
            else:
                raise GoogleSheetsError(
                    f"Ошибка Google Sheets API ({e.resp.status}): {error_msg}"
                )
        except Exception as e:
            raise GoogleSheetsError(f"Ошибка при чтении данных: {e}")

    def test_connection(self) -> bool:
        """
        Проверяет подключение к Google Sheets.

        Returns:
            bool: True если подключение успешно
        """
        try:
            service = self._get_service()
            sheet = service.spreadsheets()

            # Получаем метаданные таблицы
            result = sheet.get(
                spreadsheetId=self.config.spreadsheet_id
            ).execute()

            title = result.get("properties", {}).get("title", "Неизвестно")
            sheets = result.get("sheets", [])
            sheet_names = [
                sheet.get("properties", {}).get("title", "Без имени")
                for sheet in sheets
            ]

            print(f"✅ Подключение успешно!")
            print(f"   Таблица: '{title}'")
            print(f"   Доступные листы: {', '.join(sheet_names)}")
            print(f"   Ищем лист: '{self.config.sheet_name}'")

            # Проверяем существование указанного листа
            target_sheet_exists = any(
                sheet.get("properties", {}).get("title")
                == self.config.sheet_name
                for sheet in sheets
            )

            if not target_sheet_exists:
                print(
                    f"⚠️  Лист '{self.config.sheet_name}' не найден в таблице"
                )
                print(f"   Используйте один из: {', '.join(sheet_names)}")

            return True

        except HttpError as e:
            if e.resp.status == 404:
                print(f"❌ Таблица не найдена. Проверьте SPREADSHEET_ID")
            elif e.resp.status == 403:
                print(f"❌ Нет доступа к таблице")
                print(
                    f"   Предоставьте доступ для: {config.google_credentials.get_client_email()}"
                )
            else:
                print(f"❌ Ошибка подключения: {e}")
            return False
        except Exception as e:
            print(f"❌ Ошибка подключения: {e}")
            return False


class CSVReader:
    """Альтернативный источник данных из CSV-файла."""

    @staticmethod
    def read_data(filepath: str) -> List[List[str]]:
        """
        Читает данные из CSV-файла.

        Args:
            filepath: Путь к CSV-файлу

        Returns:
            Список строк таблицы

        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: При ошибке чтения CSV
        """
        import csv

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                data = list(reader)

            if not data:
                print("📭 CSV-файл пуст.")
                return []

            print(f"✅ Загружено {len(data)} строк из CSV-файла")
            return data

        except FileNotFoundError:
            raise FileNotFoundError(f"Файл не найден: {filepath}")
        except UnicodeDecodeError:
            # Пробуем другие кодировки
            try:
                with open(filepath, "r", encoding="cp1251") as file:
                    reader = csv.reader(file)
                    data = list(reader)
                print(
                    f"✅ Загружено {len(data)} строк из CSV-файла (кодировка cp1251)"
                )
                return data
            except:
                raise ValueError(
                    f"Не удалось прочитать файл {filepath}. "
                    "Проверьте кодировку файла."
                )
        except Exception as e:
            raise ValueError(f"Ошибка чтения CSV: {e}")
