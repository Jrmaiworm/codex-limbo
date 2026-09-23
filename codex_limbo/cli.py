"""Command line entry point."""
import argparse
import time
from rich.console import Console
from . import __version__
from .alerts import check
from .advice import recommend
from .charts import render
from .config import load_config
from .database import connect
from .doctor import diagnostics
from .history import grouped, total, today
from .quota import latest, remaining, reset_text, trend
from .sessions import sync


def parser():
    p = argparse.ArgumentParser(prog="codex-limbo", description="Local Codex usage monitor")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    history = sub.add_parser("history")
    history.add_argument("--hours", type=int, choices=(1, 3, 6, 12, 24), default=24)
    watch = sub.add_parser("watch")
    watch.add_argument("--seconds", type=int)
    sub.add_parser("alerts")
    sub.add_parser("advice")
    sub.add_parser("doctor")
    return p


def show_status(db, console):
    rows = latest(db)
    if not rows:
        console.print("No official quota snapshots found in local sessions.")
    for row in rows:
        drop, eta = trend(db, row["limit_id"], row["window_name"])
        console.print(f'[bold]{row["limit_id"]} {row["window_name"]}[/bold]: {remaining(row):.1f}% remaining; reset {reset_text(row["resets_at"])}; credits {row["credits"] or "unavailable"} [dim](official snapshot {row["timestamp"]})[/dim]')
        if drop > 0:
            console.print(f'  Drop {drop:.1f} points; exhaustion estimate {eta:.0f} min' if eta is not None else f'  Drop {drop:.1f} points')
    console.print(f'Tokens today: {today(db):,}; last hour: {total(db, 1):,} [dim](local estimates)[/dim]')
    console.print(f'Local token rate: {total(db, 1) / 60:.1f}/min [dim](last hour average)[/dim]')


def main(argv=None):
    args = parser().parse_args(argv)
    console = Console()
    if args.command == "doctor":
        for line in diagnostics():
            console.print(line)
        return 0
    config = load_config()
    db = connect()
    try:
        if args.command == "watch":
            seconds = args.seconds or config.watch_seconds
            if seconds <= 0:
                raise SystemExit("--seconds must be positive")
            try:
                while True:
                    sync(db)
                    console.clear()
                    show_status(db, console)
                    for color, message in check(db, config):
                        console.print(f'[{color}]{message}[/{color}]')
                    time.sleep(seconds)
            except KeyboardInterrupt:
                return 0
        sync(db)
        if args.command == "status":
            show_status(db, console)
        elif args.command == "history":
            console.print(f'Tokens in last {args.hours}h: {total(db, args.hours):,} [dim](local estimate)[/dim]')
            render(grouped(db, args.hours), console)
        elif args.command == "alerts":
            notices = check(db, config)
            for color, message in notices:
                console.print(f'[{color}]{message}[/{color}]')
            if not notices:
                console.print("[green]No thresholds crossed.[/green]")
        elif args.command == "advice":
            for line in recommend(db):
                console.print(line)
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
