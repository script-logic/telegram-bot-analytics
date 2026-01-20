"""
Main script for Google Sheets data analysis.
Integrates Google Sheets, data analysis, and LLM.
"""

import argparse
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
)
from rich.table import Table

from config import (
    AppConfig,
    config,
)
from src.data_analyzer import (
    AnalysisResult,
    DataAnalyzer,
)
from src.google_sheets_client import (
    CSVReader,
    GoogleSheetsClient,
    GoogleSheetsError,
)
from src.llm_processor import LLMProcessor

console = Console()


PRIORITY_STYLES = {
    "high": (
        "🔴",
        "bold red",
    ),
    "medium": (
        "🟡",
        "bold yellow",
    ),
    "low": (
        "🟢",
        "bold green",
    ),
}

EPILOG = "\n".join(
    [
        "Usage examples:",
        "  %(prog)s --api                # Google Sheets API analysis",
        "  %(prog)s --api --llm          # API + LLM analysis",
        "  %(prog)s --csv data.csv       # CSV file analysis",
        "  %(prog)s --api --test         # Connection test only",
        "  %(prog)s --api --llm --debug  # With debugging",
    ]
)

BANNER = "\n".join(
    [
        "🤖 Google Sheets LLM Analyzer",
        "📊 Statistical Data Analysis",
    ],
)


def _create_config_info_table(current_config: AppConfig) -> Table:
    """Forms config info table"""
    table = Table(
        show_header=False,
        box=None,
    )
    table.add_column(
        "Parameter",
        style="cyan",
    )
    table.add_column(
        "Value",
        style="green",
    )

    table.add_row(
        "Google Sheet",
        current_config.spreadsheet_id,
    )
    table.add_row(
        "Sheet",
        current_config.sheet_name,
    )
    table.add_row(
        "Category Column",
        f"Column {current_config.category_column}",
    )
    table.add_row(
        "LLM Key",
        "Provided" if current_config.is_llm_enabled else "Not provided",
    )
    table.add_row(
        "Debug Mode",
        "Yes" if current_config.debug else "No",
    )
    return table


def _create_main_stats_table(result: AnalysisResult) -> Table:
    """Forms main stats table"""
    total = result.total_requests

    table = Table(
        show_header=True,
        box=ROUNDED,
    )

    table.add_column(
        "Category",
        style="cyan",
        no_wrap=True,
    )
    table.add_column(
        "Count",
        justify="right",
        style="green",
    )
    table.add_column(
        "Percentage",
        justify="right",
        style="yellow",
    )

    for category, count in result.categories_sorted:
        percent = format_percentage(
            count,
            total,
        )
        table.add_row(
            category,
            str(count),
            f"{percent}%",
        )

    return table


def _create_summary_table(result: AnalysisResult) -> Table:
    """Forms summary table"""
    total = result.total_requests

    table = Table(
        show_header=False,
        box=None,
        expand=False,
    )

    table.add_column(
        "Metric",
        style="cyan",
    )
    table.add_column(
        "Value",
        style="green",
    )

    table.add_row(
        "Total Requests",
        str(result.total_requests),
    )
    table.add_row(
        "Unique Categories",
        str(len(result.category_counts)),
    )

    if result.most_common_category:
        percent = format_percentage(
            result.most_common_count,
            total,
        )
        table.add_row(
            "Most Popular Category",
            f"[bold]{result.most_common_category}[/bold] "
            f"({result.most_common_count} requests, "
            f"{percent}%)",
        )

    return table


def _create_details_table(
    request: dict[str, Any],
    analysis: Any,
    style: str,
) -> Table:
    """Forms details table"""
    table = Table(
        show_header=False,
        box=None,
        padding=(
            0,
            2,
        ),
        expand=False,
    )

    table.add_column(
        "Field",
        style="dim",
    )
    table.add_column(
        "Value",
        style="white",
    )

    table.add_row(
        "Category",
        request.get(
            "category",
            "Not specified",
        ),
    )
    table.add_row(
        "Date",
        request.get(
            "date",
            "Not specified",
        ),
    )
    table.add_row(
        "Choice",
        request.get(
            "choice",
            "Not specified",
        ),
    )
    table.add_row(
        "Priority",
        f"[{style}]{analysis.priority_text}[/{style}]",
    )
    table.add_row(
        "Analysis Time",
        f"{analysis.processing_time:.2f} sec",
    )

    return table


def print_banner():
    """Display application banner."""
    console.print(
        Panel(
            "",
            subtitle=BANNER,
            expand=True,
            style="bold blue",
        ),
        justify="full",
    )


def validate_config(current_config: AppConfig) -> None:
    """If config is None -> sys.exit(1)."""
    if current_config is None:
        console.print(
            "[red]❌ Error: Configuration not loaded[/red]\n"
            "Check .env file existence and correctness",
        )
        sys.exit(1)


def format_percentage(
    count: int,
    total: int,
) -> str:
    """Format percentage with one decimal place."""
    if total == 0:
        return "0.0%"
    return f"{(count / total) * 100:.1f}%"


def print_config_summary():
    """Display configuration summary."""
    if not config:
        console.print("[red]❌ Configuration not loaded[/red]")
        return

    console.print(
        Panel.fit(
            "[bold]System Configuration[/bold]",
            border_style="cyan",
        ),
    )

    info_table = _create_config_info_table(config)

    console.print(
        info_table,
        end="\n\n",
    )


def print_statistics(
    result: AnalysisResult,
    llm_results: list[dict[str, Any]] | None = None,
):
    """
    Display statistics in a formatted way.

    Args:
        result: DataAnalyzer result
        llm_results: LLM analysis results
    """
    if not result.has_data:
        console.print(
            Panel(
                "[yellow]📭 No data for analysis[/yellow]",
                border_style="yellow",
            ),
            end="\n\n",
        )
        return

    console.print(
        Panel(
            "[bold]📈 Request Statistics[/bold]",
            expand=False,
            border_style="magenta",
        ),
        end="\n\n",
    )

    stats_table = _create_main_stats_table(result)

    console.print(
        stats_table,
        end="\n\n",
    )

    summary_table = _create_summary_table(result)

    console.print(
        Panel(
            summary_table,
            border_style="green",
            expand=False,
        ),
        end="\n\n",
    )

    # LLM Analysis
    if llm_results:
        console.print(
            Panel(
                "[bold]🤖 LLM Analysis[/bold]",
                border_style="blue",
                expand=False,
            ),
            end="\n\n",
        )

        for request in llm_results:
            if request.get("llm_analysis"):
                analysis = request["llm_analysis"]

                emoji, style = PRIORITY_STYLES.get(
                    analysis.priority,
                    (
                        "⚪",
                        "bold white",
                    ),
                )

                console.print(
                    f"{emoji} [bold]Request #{request['row_number']}[/bold] "
                    f"(ID: {request['id']})",
                    end="\n\n",
                )

                details = _create_details_table(
                    request,
                    analysis,
                    style,
                )

                console.print(
                    details,
                    end="\n\n",
                )

                if analysis.summary:
                    console.print(
                        "   [dim]📝 Summary:[/dim]"
                        f" [italic]{analysis.summary}[/italic]",
                        end="\n\n",
                    )

                if analysis.recommendation:
                    console.print(
                        "   [dim]💡 Recommendation:[/dim]"
                        f" {analysis.recommendation}",
                        end="\n\n",
                    )

        console.print(
            f"[dim]Total analyzed requests: {len(llm_results)}[/dim]",
            end="\n\n",
        )


@contextmanager
def show_progress(description: str):
    """Show progress"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(
            description,
            total=None,
        )
        try:
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
    validate_config(config)

    print_banner()
    print_config_summary()

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

    if args.test:
        console.print(
            Panel(
                "[bold]🔧 Connection test...[/bold]",
                border_style="yellow",
                expand=False,
            ),
            end="\n\n",
        )

        if args.api:
            console.print("[bold]Testing Google Sheets...[/bold]")
            try:
                client = GoogleSheetsClient()
                if client.test_connection():
                    console.print("[green]✅ Google Sheets: OK[/green]")
                else:
                    console.print("[red]❌ Google Sheets: FAILED[/red]")
            except Exception as e:
                console.print(f"[red]❌ Google Sheets: {e}[/red]")

        console.print("\n[bold]Testing LLM...[/bold]")
        try:
            llm_processor = LLMProcessor()
            if llm_processor.test_connection():
                console.print("[green]✅ LLM: OK[/green]")
        except Exception as e:
            console.print(f"[red]❌ LLM: {e}[/red]")

        console.print("\n[green]✅ Testing completed[/green]")
        return

    # Main mode
    try:
        with show_progress("Loading data...") as (
            progress,
            task,
        ):
            if args.api:
                try:
                    client = GoogleSheetsClient()
                    data = client.fetch_data()
                except GoogleSheetsError as e:
                    console.print(f"[red]❌ Google Sheets error: {e}[/red]")
                    if args.debug:
                        console.print_exception()
                    sys.exit(1)
            else:
                # Use CSV file
                if not Path(args.csv).exists():
                    console.print(f"[red]❌ File not found: {args.csv}[/red]")
                    sys.exit(1)

                try:
                    data = CSVReader.read_data(args.csv)
                except Exception as e:
                    console.print(f"[red]❌ CSV reading error: {e}[/red]")
                    sys.exit(1)

            progress.update(
                task,
                completed=100,
                description="✅ Data loaded",
            )

        if args.raw and args.debug and data:
            console.print(
                Panel(
                    "[bold]📄 Raw Data[/bold]",
                    border_style="dim",
                )
            )
            for i, row in enumerate(data):
                console.print(f"[dim]{i}:[/dim] {row}")

            console.print()

        # Analyze data statistics
        analyzer = DataAnalyzer(category_column=config.category_column)
        result = analyzer.analyze(data)

        # LLM Analysis
        llm_results = None
        if args.llm and config.is_llm_enabled:
            with console.status("[bold green]LLM analysis...[/bold green]"):
                try:
                    llm_processor = LLMProcessor()
                    requests_for_llm = analyzer.get_requests_for_llm(data)
                    llm_results = llm_processor.analyze_multiple_requests(
                        requests_for_llm,
                    )
                except Exception as e:
                    console.print(
                        f"[yellow]⚠️  LLM analysis error: {e}[/yellow]",
                    )
                    if args.debug:
                        console.print_exception()

        # Display results
        console.print()
        print_statistics(
            result,
            llm_results,
        )

        # Summary
        if args.llm and llm_results:
            llm_status = "✅ Enabled"
        else:
            llm_status = "❌ Disabled\nEnable LLM: --llm"

        console.print(
            Panel.fit(
                f"[green]✅ Analysis completed successfully![/green]\n"
                f"Processed requests: {result.total_requests}\n"
                f"LLM analysis: {llm_status}",
                border_style="green",
            ),
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]❌ Critical error: {e}[/red]")
        if args.debug:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
