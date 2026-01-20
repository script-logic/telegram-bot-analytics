"""
Client for working with Google Sheets API.
"""

import json
from typing import Any

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import config


class GoogleSheetsError(Exception):
    """Base exception for Google Sheets errors."""

    pass


class GoogleSheetsClient:
    """Client for working with Google Sheets API."""

    def __init__(self):
        if config is None:
            raise GoogleSheetsError(
                "Configuration not loaded. Check .env file."
            )

        self.config = config
        self._service = None

        try:
            self.credentials = config.get_google_credentials()
        except Exception as e:
            raise GoogleSheetsError(f"Error loading credentials: {e}") from e

    def _get_service(self):
        """Creates and returns Google Sheets service."""
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
                    f"Error creating Google Sheets service: {e}"
                ) from e

        return self._service

    def fetch_data(self) -> list[list[Any]]:
        """
        Retrieves data from Google Sheet.

        Returns:
            List of table rows (first row - headers)

        Raises:
            GoogleSheetsError: On connection or reading error
        """
        try:
            service = self._get_service()
            sheet = service.spreadsheets()

            range_name = f"{self.config.sheet_name}!A:Z"

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
                print("📭 Sheet is empty or contains no data.")
                return []

            print(f"✅ Loaded {len(values)} rows from Google Sheet")

            return values

        except HttpError as e:
            error_details = json.loads(e.content.decode("utf-8"))
            error_msg = error_details.get("error", {}).get("message", str(e))

            if e.resp.status == 404:
                raise GoogleSheetsError(
                    f"Sheet not found. Check SPREADSHEET_ID: {error_msg}"
                ) from e
            elif e.resp.status == 403:
                raise GoogleSheetsError(
                    "No access to sheet. Ensure that "
                    f"'{config.get_service_email()}' "
                    f"has access to the sheet. Error: {error_msg}"
                ) from e
            else:
                raise GoogleSheetsError(
                    f"Google Sheets API error ({e.resp.status}): {error_msg}"
                ) from e
        except Exception as e:
            raise GoogleSheetsError(f"Error reading data: {e}") from e

    def test_connection(self) -> bool:
        """
        Tests connection to Google Sheets.

        Returns:
            bool: True if connection successful
        """
        try:
            service = self._get_service()
            sheet = service.spreadsheets()

            # Get spreadsheet metadata
            result = sheet.get(
                spreadsheetId=self.config.spreadsheet_id,
            ).execute()

            title = result.get("properties", {}).get("title", "Unknown")
            sheets = result.get("sheets", [])
            sheet_names = [
                sheet.get("properties", {}).get("title", "Unnamed")
                for sheet in sheets
            ]

            print(
                "✅ Connection successful!\n"
                f"   Spreadsheet: '{title}'\n"
                f"   Available sheets: {', '.join(sheet_names)}\n"
                f"   Looking for sheet: '{self.config.sheet_name}'\n"
            )

            # Check if specified sheet exists
            target_sheet_exists = any(
                sheet.get("properties", {}).get("title")
                == self.config.sheet_name
                for sheet in sheets
            )

            if not target_sheet_exists:
                print(
                    f"⚠️  Sheet '{self.config.sheet_name}' not found in"
                    " spreadsheet"
                )
                print(f"   Use one of: {', '.join(sheet_names)}")

            return True

        except HttpError as e:
            if e.resp.status == 404:
                print("❌ Spreadsheet not found. Check SPREADSHEET_ID")
            elif e.resp.status == 403:
                print("❌ No access to spreadsheet")
                print(f"   Grant access to: {config.get_service_email()}")
            else:
                print(f"❌ Connection error: {e}")
            return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False


class CSVReader:
    """Alternative data source from CSV file."""

    @staticmethod
    def read_data(filepath: str) -> list[list[str]]:
        """
        Reads data from CSV file.

        Args:
            filepath: Path to CSV file

        Returns:
            List of table rows

        Raises:
            FileNotFoundError: If file not found
            ValueError: On CSV reading error
        """
        import csv

        try:
            with open(
                filepath,
                encoding="utf-8",
            ) as file:
                reader = csv.reader(file)
                data = list(reader)

            if not data:
                print("📭 CSV file is empty.")
                return []

            print(f"✅ Loaded {len(data)} rows from CSV file")
            return data

        except FileNotFoundError as e:
            raise FileNotFoundError(f"File not found: {filepath}") from e
        except UnicodeDecodeError:
            # Try other encodings
            try:
                with open(
                    filepath,
                    encoding="cp1251",
                ) as file:
                    reader = csv.reader(file)
                    data = list(reader)
                print(
                    f"✅ Loaded {len(data)} rows from CSV file (encoding"
                    " cp1251)"
                )
                return data
            except ValueError as e:
                raise ValueError(
                    f"Could not read file {filepath}. Check file encoding."
                ) from e
        except Exception as e:
            raise ValueError(f"CSV reading error: {e}") from e
