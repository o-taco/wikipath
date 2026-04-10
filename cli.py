"""Command-line interface for the Wikipedia path finder."""

import asyncio
import sys
import time

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from wiki_path.api_client import WikiApiClient
from wiki_path.bfs import find_path
from wiki_path.path_utils import format_path, normalize_title

console = Console(legacy_windows=False)


@click.command(context_settings={"ignore_unknown_options": True})
@click.argument("source", required=False, default=None)
@click.argument("target", required=False, default=None)
@click.option("--max-depth", default=6, show_default=True, help="Maximum number of hops.")
@click.option("--verbose", "-v", is_flag=True, help="Print frontier sizes at each depth.")
@click.option("--timeout", default=120, show_default=True, help="Search timeout in seconds.")
def main(source: str, target: str, max_depth: int, verbose: bool, timeout: int) -> None:
    """Find the shortest Wikipedia hyperlink path between SOURCE and TARGET."""
    if not source or not target:
        console.print("[bold]Wikipedia Path Finder[/bold]")
        console.print("Find the shortest hyperlink path between two Wikipedia articles.\n")
        try:
            source = console.input("[bold]Source article:[/bold] ").strip()
            target = console.input("[bold]Target article:[/bold] ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if not source or not target:
            console.print("[red]Both articles are required.[/red]")
            input("\nPress Enter to exit...")
            return

    asyncio.run(_run(source, target, max_depth, verbose, timeout))
    if getattr(sys, "frozen", False):
        try:
            input("\nPress Enter to exit...")
        except (EOFError, KeyboardInterrupt):
            pass


async def _run(
    source: str, target: str, max_depth: int, verbose: bool, timeout: int
) -> None:
    source = normalize_title(source)
    target = normalize_title(target)

    async with WikiApiClient() as client:
        console.print("[dim]Resolving article titles...[/dim]")
        src_title, src_exists, src_disambig = await client.resolve_title(source)
        tgt_title, tgt_exists, tgt_disambig = await client.resolve_title(target)

        if not src_exists:
            console.print(f"[red]Article not found:[/red] {source}")
            return
        if not tgt_exists:
            console.print(f"[red]Article not found:[/red] {target}")
            return
        if src_disambig:
            console.print(
                f"[yellow]Warning:[/yellow] '{src_title}' is a disambiguation page."
            )
        if tgt_disambig:
            console.print(
                f"[yellow]Warning:[/yellow] '{tgt_title}' is a disambiguation page."
            )

        source, target = src_title, tgt_title
        console.print(f"[bold]Source:[/bold] {source}")
        console.print(f"[bold]Target:[/bold] {target}")
        console.print()

        status_text = {"msg": "Starting search..."}

        async def progress_callback(depth: int, fwd_size: int, bwd_size: int) -> None:
            msg = (
                f"Depth {depth} | "
                f"Forward frontier: [cyan]{fwd_size:,}[/cyan] | "
                f"Backward frontier: [magenta]{bwd_size:,}[/magenta]"
            )
            status_text["msg"] = msg
            if verbose:
                console.print(f"  [dim]{msg}[/dim]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=not verbose,
        ) as progress:
            task = progress.add_task("Searching...", total=None)

            async def updating_callback(
                depth: int, fwd_size: int, bwd_size: int
            ) -> None:
                await progress_callback(depth, fwd_size, bwd_size)
                progress.update(task, description=status_text["msg"])

            start = time.perf_counter()
            try:
                path = await asyncio.wait_for(
                    find_path(source, target, client, max_depth, updating_callback),
                    timeout=float(timeout),
                )
            except asyncio.TimeoutError:
                console.print(f"[red]Search timed out after {timeout}s.[/red]")
                return

        elapsed = time.perf_counter() - start

        if path is None:
            console.print(
                f"[yellow]No path found within {max_depth} hops.[/yellow]"
            )
        else:
            result = format_path(path)
            console.print(
                Panel(result, title="[bold green]Path Found[/bold green]", expand=False)
            )
            console.print(f"[dim]Completed in {elapsed:.2f}s[/dim]")


if __name__ == "__main__":
    main()
