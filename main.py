"""
Main script for Google Sheets data analysis.
Integrates Google Sheets, data analysis, and LLM.
"""

import argparse
import sys
from contextlib import contextmanager
from pathlib import Path

from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
)

from google_sheets_llm_analyzer_package.config import (
    AppConfig,
    config,
)
from google_sheets_llm_analyzer_package.console_printer import ConsolePrinter
from google_sheets_llm_analyzer_package.data_analyzer import (
    DataAnalyzer,
)
from google_sheets_llm_analyzer_package.google_sheets_client import (
    CSVReader,
    GoogleSheetsClient,
    GoogleSheetsError,
)
from google_sheets_llm_analyzer_package.llm_processor import LLMProcessor

EPILOG = "\n".join(
    [
        "Usage examples:",
        "  %(prog)s --api                # Google Sheets API analysis",
        "  %(prog)s --api --llm          # API + LLM analysis",
        "  %(prog)s --csv data.csv       # CSV file analysis",
        "  %(prog)s --api --llm --test   # Connection test only",
        "  %(prog)s --api --llm --debug  # With debugging",
    ]
)


def validate_config(
    current_config: AppConfig,
    printer: ConsolePrinter,
) -> None:
    """If config is None -> sys.exit(1)."""
    if current_config is None:
        printer.print_error(
            "Configuration not loaded\n"
            "Check .env file existence and correctness",
        )
        sys.exit(1)


@contextmanager
def show_progress(
    description: str,
    printer: ConsolePrinter,
):
    """Show progress"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=printer.console,
        transient=True,
    ) as progress:
        task = progress.add_task(
            description,
            total=None,
            start=True,
        )
        try:
            progress.refresh()
            yield progress, task
            progress.update(
                task,
                completed=100,
                description=f"✅ {description}",
            )
        except Exception:
            progress.update(
                task,
                description=f"❌ {description} failed",
            )
            raise


def main():
    """Main application function."""
    printer = ConsolePrinter()
    validate_config(config, printer)

    printer.print_banner()
    printer.print_config_summary(config)

    parser = argparse.ArgumentParser(
        description="Google Sheets data analysis with LLM integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG,
    )

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--api",
        action="store_true",
        help="Use Google Sheets API",
    )
    source_group.add_argument(
        "--csv",
        type=str,
        metavar="FILE",
        help="Use CSV file",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Enable LLM analysis",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Connection test only",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug mode",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Show raw data (only with --debug)",
    )

    args = parser.parse_args()

    # API connections test only mode
    if args.test:
        printer.print_info("Connection test...")

        if args.api:
            printer.print_info("Testing Google Sheets...")
            try:
                client = GoogleSheetsClient()
                if client.test_connection():
                    printer.print_success("Google Sheets: OK")
                else:
                    printer.print_error("Google Sheets: FAILED")

            except Exception as e:
                printer.print_error(f"Google Sheets: {e}")

        if args.llm:
            printer.print_info("Testing LLM...")
            try:
                llm_processor = LLMProcessor()
                if llm_processor.test_connection():
                    printer.print_success("LLM: OK")

            except Exception as e:
                printer.print_error(f"LLM: {e}")

        printer.print_success("Testing completed")
        return

    # Main mode
    try:
        with show_progress(
            "Loading data...",
            printer,
        ) as (
            progress,
            task,
        ):
            if args.api:
                # Use table via API
                try:
                    client = GoogleSheetsClient()
                    data = client.fetch_data()
                except GoogleSheetsError as e:
                    printer.print_error(f"Google Sheets error: {e}")
                    if args.debug:
                        printer.print_error("", show_exception=True)
                    sys.exit(1)
            else:
                # Use CSV file
                if not Path(args.csv).exists():
                    printer.print_error(f"File not found: {args.csv}")
                    sys.exit(1)

                try:
                    data = CSVReader.read_data(args.csv)
                except Exception as e:
                    printer.print_error(f"CSV reading error: {e}")
                    sys.exit(1)

            progress.update(
                task,
                completed=100,
                description="✅ Data loaded",
            )

        if args.raw and args.debug and data:
            printer.print_info("Raw Data")
            for i, row in enumerate(data):
                printer.print_info(f"{i}: {row}")

        # Analyze data statistics
        analyzer = DataAnalyzer(category_column=config.category_column)
        result = analyzer.analyze(data)

        # LLM Analysis
        llm_results = None
        if args.llm and config.is_llm_enabled:
            with show_progress(
                "Running LLM analysis...",
                printer,
            ) as (progress, task):
                try:
                    llm_processor = LLMProcessor()
                    requests_for_llm = analyzer.get_requests_for_llm(data)
                    llm_results = llm_processor.analyze_multiple_requests(
                        requests_for_llm,
                    )
                    progress.update(
                        task,
                        completed=100,
                        description="✅ LLM analysis complete",
                    )
                except Exception as e:
                    printer.print_warning(f"LLM analysis error: {e}")
                    if args.debug:
                        printer.print_error("", show_exception=True)

        printer.print_statistics(
            result,
            llm_results,
        )

        # Summary
        printer.print_completion_summary(
            success=True,
            total_requests=result.total_requests,
            llm_enabled=args.llm and config.is_llm_enabled,
            llm_analyzed=len(llm_results) if llm_results else 0,
        )

    except KeyboardInterrupt:
        printer.print_warning("Interrupted by user")
        sys.exit(130)

    except Exception as e:
        printer.print_error(f"Critical error: {e}")
        if args.debug:
            printer.print_error("", show_exception=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
