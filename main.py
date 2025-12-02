#!/usr/bin/env python3
"""
Company Deep Analyzer - Main Entry Point

A systematic framework for deep company and business model analysis
using multi-agent conversation design.

Usage:
    python main.py "公司名称"
    python main.py "Apple" --output report.md
    python main.py "Tesla" --model claude-opus-4-20250514 --no-methodology
"""

import argparse
import sys
import os
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.markdown import Markdown
from rich.table import Table

from orchestrator import Orchestrator, AnalysisReport


console = Console()


def print_banner():
    """Print the application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                    公司深度分析系统                               ║
║                Company Deep Analyzer                             ║
║                                                                  ║
║  基于多Agent对话的系统性公司分析框架                               ║
║  Systematic Multi-Agent Company Analysis Framework               ║
╚══════════════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold blue")


def print_round_info(orchestrator: Orchestrator):
    """Print information about all analysis rounds."""
    table = Table(title="分析流程", show_header=True, header_style="bold magenta")
    table.add_column("轮次", style="cyan", justify="center")
    table.add_column("中文名称", style="green")
    table.add_column("English Name", style="yellow")

    for info in orchestrator.get_agent_info():
        table.add_row(
            str(info["round"]),
            info["name_cn"],
            info["name"]
        )

    console.print(table)
    console.print()


def run_analysis(
    company_name: str,
    model: str = "claude-sonnet-4-20250514",
    include_methodology: bool = True,
    output_file: str = None,
    quiet: bool = False,
) -> AnalysisReport:
    """
    Run the complete analysis and optionally save to file.

    Args:
        company_name: Name of the company to analyze.
        model: Claude model to use.
        include_methodology: Whether to include Round 8.
        output_file: Optional file path to save the report.
        quiet: If True, suppress progress output.

    Returns:
        The complete AnalysisReport.
    """
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]错误：未设置 ANTHROPIC_API_KEY 环境变量[/red]")
        console.print("请设置环境变量后重试：")
        console.print("  export ANTHROPIC_API_KEY='your-api-key'")
        sys.exit(1)

    # Create orchestrator
    orchestrator = Orchestrator(
        model=model,
        include_methodology=include_methodology,
    )

    if not quiet:
        print_banner()
        console.print(f"\n[bold]分析目标：[/bold] {company_name}\n")
        print_round_info(orchestrator)

    # Track current round for progress
    current_round = {"number": 0, "name": ""}

    def on_round_start(round_number: int, round_name: str):
        current_round["number"] = round_number
        current_round["name"] = round_name

    def on_round_complete(round_number: int, round_name: str, success: bool):
        status = "[green]✓[/green]" if success else "[red]✗[/red]"
        if not quiet:
            console.print(f"  {status} 第{round_number}轮：{round_name}")

    orchestrator.on_round_start = on_round_start
    orchestrator.on_round_complete = on_round_complete

    # Run analysis with progress indicator
    if not quiet:
        console.print("[bold]开始分析...[/bold]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        disable=quiet,
    ) as progress:
        task = progress.add_task(
            f"[cyan]正在分析 {company_name}...",
            total=None
        )

        report = orchestrator.analyze(company_name)

        progress.update(task, description="[green]分析完成！")

    # Print summary
    if not quiet:
        console.print("\n")
        console.print(Panel(
            f"[bold green]分析完成！[/bold green]\n\n"
            f"公司：{company_name}\n"
            f"耗时：{report.total_duration_seconds:.1f} 秒\n"
            f"完成轮次：{len([r for r in report.rounds if r.success])}/{len(report.rounds)}",
            title="分析结果",
            border_style="green"
        ))

    # Save to file if requested
    if output_file:
        markdown_report = report.to_markdown()
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(markdown_report)
        if not quiet:
            console.print(f"\n[bold]报告已保存至：[/bold] {output_file}")

    return report


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="公司深度分析系统 - 基于多Agent对话的系统性公司分析框架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py "Apple"                       # 分析 Apple 公司
  python main.py "Tesla" -o tesla_report.md   # 分析 Tesla 并保存报告
  python main.py "Microsoft" --no-methodology  # 跳过方法论提炼（第8轮）
  python main.py "Google" --model claude-opus-4-20250514  # 使用 Opus 模型
        """
    )

    parser.add_argument(
        "company",
        type=str,
        help="要分析的公司名称"
    )

    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="输出报告的文件路径（Markdown格式）"
    )

    parser.add_argument(
        "-m", "--model",
        type=str,
        default="claude-sonnet-4-20250514",
        help="使用的 Claude 模型 (默认: claude-sonnet-4-20250514)"
    )

    parser.add_argument(
        "--no-methodology",
        action="store_true",
        help="跳过第8轮方法论提炼"
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="静默模式，减少输出"
    )

    parser.add_argument(
        "--print-report",
        action="store_true",
        help="在控制台打印完整报告"
    )

    args = parser.parse_args()

    # Generate default output filename if not specified
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_company_name = "".join(c if c.isalnum() else "_" for c in args.company)
        args.output = f"{safe_company_name}_analysis_{timestamp}.md"

    # Run analysis
    report = run_analysis(
        company_name=args.company,
        model=args.model,
        include_methodology=not args.no_methodology,
        output_file=args.output,
        quiet=args.quiet,
    )

    # Print full report if requested
    if args.print_report:
        console.print("\n")
        console.print(Panel("[bold]完整分析报告[/bold]", border_style="blue"))
        console.print("\n")
        markdown_report = report.to_markdown()
        console.print(Markdown(markdown_report))

    return 0


if __name__ == "__main__":
    sys.exit(main())
