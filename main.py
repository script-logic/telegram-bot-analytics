"""
Основной скрипт анализа заявок Telegram-бота.
Интегрирует Google Sheets, анализ данных и LLM.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

from config import config
from src.data_analyzer import DataAnalyzer
from src.google_sheets_client import (
    CSVReader,
    GoogleSheetsClient,
    GoogleSheetsError,
)
from src.llm_processor import LLMProcessor

console = Console()


def print_banner():
    """Выводит баннер приложения."""
    banner = """
    🤖 Telegram Bot Analytics v1.0
    📊 Анализ заявок · Google Sheets · AI Анализ
    """
    console.print(Panel(banner, style="bold blue"))


def print_config_summary():
    """Выводит сводку конфигурации."""
    if not config:
        console.print("[red]❌ Конфигурация не загружена[/red]")
        return

    console.print(
        Panel.fit("[bold]Конфигурация системы[/bold]", border_style="cyan")
    )

    info_table = Table(show_header=False, box=None)
    info_table.add_column("Параметр", style="cyan")
    info_table.add_column("Значение", style="green")

    info_table.add_row(
        "Google Таблица", config.google_sheets.spreadsheet_id[:30] + "..."
    )
    info_table.add_row("Лист", config.google_sheets.sheet_name)
    info_table.add_row(
        "Столбец категорий", f"Столбец {config.google_sheets.category_column}"
    )
    info_table.add_row("LLM", "Включен" if config.llm.enabled else "Выключен")
    info_table.add_row("Режим отладки", "Да" if config.debug else "Нет")

    console.print(info_table)
    console.print()


def print_statistics(result, llm_results: Optional[list] = None):
    """
    Выводит статистику в красивом формате.

    Args:
        result: Результат анализа DataAnalyzer
        llm_results: Результаты анализа LLM
    """
    if not result.has_data:
        console.print(
            Panel(
                "[yellow]📭 Нет данных для анализа[/yellow]",
                border_style="yellow",
            )
        )
        return

    # Основная статистика
    console.print(
        Panel("[bold]📈 Статистика заявок[/bold]", border_style="magenta")
    )

    stats_table = Table(show_header=True, header_style="bold")
    stats_table.add_column("Категория", style="cyan", no_wrap=True)
    stats_table.add_column("Количество", justify="right", style="green")
    stats_table.add_column("Процент", justify="right", style="yellow")

    total = result.total_requests

    for category, count in result.categories_sorted:
        percentage = (count / total) * 100 if total > 0 else 0
        stats_table.add_row(category, str(count), f"{percentage:.1f}%")

    console.print(stats_table)

    # Итоговая информация
    console.print()
    summary_table = Table(show_header=False, box=None)
    summary_table.add_column("Метрика", style="cyan")
    summary_table.add_column("Значение", style="green")

    summary_table.add_row("Всего заявок", str(result.total_requests))
    summary_table.add_row("Всего строк в таблице", str(result.total_rows))
    summary_table.add_row(
        "Уникальных категорий", str(len(result.category_counts))
    )

    if result.most_common_category:
        percentage = (result.most_common_count / total) * 100
        summary_table.add_row(
            "Самая популярная категория",
            f"[bold]{result.most_common_category}[/bold] "
            f"({result.most_common_count} заявок, {percentage:.1f}%)",
        )

    console.print(Panel(summary_table, border_style="green"))

    # Анализ LLM
    if llm_results:
        console.print()
        console.print(Panel("[bold]🤖 Анализ LLM[/bold]", border_style="blue"))

        for request in llm_results:
            if "llm_analysis" in request and request["llm_analysis"]:
                analysis = request["llm_analysis"]

                # Определяем стиль по приоритету
                priority_styles = {
                    "high": ("🔴", "bold red"),
                    "medium": ("🟡", "bold yellow"),
                    "low": ("🟢", "bold green"),
                }

                emoji, style = priority_styles.get(
                    analysis.priority, ("⚪", "bold white")
                )

                # Заголовок заявки
                console.print(
                    f"{emoji} [bold]Заявка #{request['row_number']}[/bold] "
                    f"(ID: {request['id']})"
                )

                # Детали
                details = Table(show_header=False, box=None, padding=(0, 2))
                details.add_column("Поле", style="dim")
                details.add_column("Значение", style="white")

                details.add_row(
                    "Категория", request.get("category", "Не указана")
                )
                details.add_row("Дата", request.get("date", "Не указана"))
                details.add_row("Выбор", request.get("choice", "Не указан"))
                details.add_row(
                    "Приоритет", f"[{style}]{analysis.priority_text}[/{style}]"
                )
                details.add_row(
                    "Время анализа", f"{analysis.processing_time:.2f} сек"
                )

                console.print(details)

                # Описание и рекомендация
                if analysis.summary:
                    console.print(
                        f"   [dim]📝 Суть:[/dim] [italic]{analysis.summary}[/italic]"
                    )

                if analysis.recommendation:
                    console.print(
                        f"   [dim]💡 Рекомендация:[/dim] {analysis.recommendation}"
                    )

                console.print()  # Пустая строка между заявками

        console.print(
            f"[dim]Всего проанализировано заявок: {len(llm_results)}[/dim]"
        )


def main():
    """Основная функция приложения."""
    parser = argparse.ArgumentParser(
        description="Анализ заявок из Telegram-бота с Google Sheets и LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  %(prog)s --api                    # Анализ через Google Sheets API
  %(prog)s --api --llm              # Анализ через API + LLM
  %(prog)s --csv data.csv           # Анализ из CSV файла
  %(prog)s --api --test             # Только тест подключения
  %(prog)s --api --llm --debug      # С отладкой
        """,
    )

    # Источник данных
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--api", action="store_true", help="Использовать Google Sheets API"
    )
    source_group.add_argument(
        "--csv", type=str, metavar="ФАЙЛ", help="Использовать CSV-файл"
    )

    # Дополнительные опции
    parser.add_argument(
        "--llm", action="store_true", help="Включить анализ LLM"
    )
    parser.add_argument(
        "--test", action="store_true", help="Только тест подключения"
    )
    parser.add_argument("--debug", action="store_true", help="Режим отладки")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Показать сырые данные (только с --debug)",
    )

    args = parser.parse_args()

    # Проверяем конфигурацию
    if config is None:
        console.print("[red]❌ Ошибка: Конфигурация не загружена[/red]")
        console.print("Проверьте наличие и корректность .env файла")
        sys.exit(1)

    # Выводим баннер и конфигурацию
    print_banner()
    print_config_summary()

    # Тестовый режим
    if args.test:
        console.print(
            Panel("[bold]🔧 Тест подключения...[/bold]", border_style="yellow")
        )

        if args.api:
            # Тест Google Sheets
            console.print("\n[bold]Testing Google Sheets...[/bold]")
            try:
                client = GoogleSheetsClient()
                if client.test_connection():
                    console.print("[green]✅ Google Sheets: OK[/green]")
                else:
                    console.print("[red]❌ Google Sheets: FAILED[/red]")
            except Exception as e:
                console.print(f"[red]❌ Google Sheets: {e}[/red]")

        # Тест LLM
        console.print("\n[bold]Testing LLM...[/bold]")
        try:
            llm_processor = LLMProcessor()
            if llm_processor.test_connection():
                console.print("[green]✅ LLM: OK[/green]")
        except Exception as e:
            console.print(f"[red]❌ LLM: {e}[/red]")

        console.print("\n[green]✅ Тестирование завершено[/green]")
        return

    # Основной режим
    try:
        # Получаем данные
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Загрузка данных...", total=None)

            if args.api:
                # Используем Google Sheets API
                try:
                    client = GoogleSheetsClient()
                    data = client.fetch_data()
                except GoogleSheetsError as e:
                    console.print(f"[red]❌ Ошибка Google Sheets: {e}[/red]")
                    if args.debug:
                        console.print_exception()
                    sys.exit(1)
            else:
                # Используем CSV
                if not Path(args.csv).exists():
                    console.print(f"[red]❌ Файл не найден: {args.csv}[/red]")
                    sys.exit(1)

                try:
                    data = CSVReader.read_data(args.csv)
                except Exception as e:
                    console.print(f"[red]❌ Ошибка чтения CSV: {e}[/red]")
                    sys.exit(1)

            progress.update(
                task, completed=100, description="✅ Данные загружены"
            )

        # Показываем сырые данные (если нужно)
        if args.raw and args.debug and data:
            console.print(
                Panel("[bold]📄 Сырые данные[/bold]", border_style="dim")
            )
            for i, row in enumerate(data[:10]):  # Показываем первые 10 строк
                console.print(f"[dim]{i}:[/dim] {row}")

            if len(data) > 10:
                console.print(f"[dim]... и еще {len(data) - 10} строк[/dim]")
            console.print()

        # Анализируем данные
        analyzer = DataAnalyzer(
            category_column=config.google_sheets.category_column
        )
        result = analyzer.analyze(data)

        # Анализ LLM
        llm_results = None
        if args.llm and config.llm.enabled:
            with console.status("[bold green]Анализ LLM...[/bold green]"):
                try:
                    llm_processor = LLMProcessor()
                    requests_for_llm = analyzer.get_requests_for_llm(data)
                    llm_results = llm_processor.analyze_multiple_requests(
                        requests_for_llm
                    )
                except Exception as e:
                    console.print(
                        f"[yellow]⚠️  Ошибка LLM анализа: {e}[/yellow]"
                    )
                    if args.debug:
                        console.print_exception()

        # Выводим результаты
        console.print()
        print_statistics(result, llm_results)

        # Итог
        console.print(
            Panel.fit(
                f"[green]✅ Анализ завершен успешно![/green]\n"
                f"Обработано заявок: {result.total_requests}\n"
                f"LLM анализ: {'✅ Включен' if args.llm and llm_results else '❌ Отключен'}",
                border_style="green",
            )
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Прервано пользователем[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[red]❌ Критическая ошибка: {e}[/red]")
        if args.debug:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()
