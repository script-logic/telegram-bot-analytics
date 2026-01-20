"""
Data analysis from Google Sheets.
Statistics calculation, data preparation for LLM.
"""

from collections import Counter
from dataclasses import dataclass
from typing import Any


@dataclass
class AnalysisResult:
    """Data analysis results."""

    total_requests: int
    total_rows: int
    category_counts: dict[str, int]
    most_common_category: str
    most_common_count: int
    raw_data: list[list[Any]]

    @property
    def has_data(self) -> bool:
        """Is there data for analysis?"""
        return self.total_requests > 0

    @property
    def categories_sorted(self) -> list[tuple[str, int]]:
        """Categories sorted by count (descending)."""
        return sorted(
            self.category_counts.items(), key=lambda x: x[1], reverse=True
        )


class DataAnalyzer:
    """Statistical data analyzer for spreadsheet data."""

    def __init__(
        self,
        category_column: int = 3,
    ):
        self.category_column = category_column

    def analyze(
        self,
        data: list[list[Any]],
    ) -> AnalysisResult:
        """
        Analyzes table data.

        Args:
            data: List of table rows (first row - headers)

        Returns:
            AnalysisResult with analysis results
        """
        if len(data) <= 1:
            return AnalysisResult(
                total_requests=0,
                total_rows=len(data),
                category_counts={},
                most_common_category="",
                most_common_count=0,
                raw_data=data,
            )

        categories = []
        skipped_rows = []

        for i, row in enumerate(data[1:], start=2):
            if len(row) >= self.category_column:
                category = row[self.category_column - 1]
                if isinstance(category, str):
                    category = category.strip()
                else:
                    category = str(category).strip() if category else ""

                if category:
                    categories.append(category)
                else:
                    skipped_rows.append(i)
            else:
                skipped_rows.append(i)

        if len(skipped_rows):
            print(f"⚠️  Skipped {len(skipped_rows)} rows without category")

        if not categories:
            return AnalysisResult(
                total_requests=0,
                total_rows=len(data),
                category_counts={},
                most_common_category="",
                most_common_count=0,
                raw_data=data,
            )

        category_counts = Counter(categories)

        if category_counts:
            most_common_category, most_common_count = (
                category_counts.most_common(1)[0]
            )
        else:
            most_common_category, most_common_count = "", 0

        return AnalysisResult(
            total_requests=len(categories),
            total_rows=len(data),
            category_counts=dict(category_counts),
            most_common_category=most_common_category,
            most_common_count=most_common_count,
            raw_data=data,
        )

    def get_requests_for_llm(
        self,
        data: list[list[Any]],
    ) -> list[dict[str, Any]]:
        """
        Prepares data for LLM analysis.

        Args:
            data: Raw table data

        Returns:
            List of dictionaries with request data
        """
        requests: list = []

        if len(data) <= 1:
            return requests

        # Table structure:
        # A: Number, B: Date, C: Category, D: Choice
        for i, row in enumerate(data[1:], start=2):
            request_data = {
                "row_number": i,
                "id": row[0] if len(row) > 0 and row[0] else str(i),
                "date": row[1] if len(row) > 1 else "",
                "category": row[2] if len(row) > 2 else "",
                "choice": row[3] if len(row) > 3 else "",
            }

            # Clean string values
            for key in request_data:
                str_clean = request_data[key]
                if isinstance(str_clean, str):
                    request_data[key] = str_clean.strip()
                elif request_data[key] is None:
                    request_data[key] = ""

            # Add only if there's a description
            if request_data["choice"]:
                requests.append(request_data)

        if requests:
            print(
                f"✅ Found {len(requests)} requests with description for"
                " LLM analysis"
            )
        else:
            print("❌  No requests with description found for LLM analysis")

        return requests
