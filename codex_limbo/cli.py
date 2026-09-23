"""Command line entry point."""
import argparse
import time
from datetime import datetime, timedelta, timezone
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from . import __version__
from .alerts import check
from .advice import recommend
from .charts import render
from .config import load_config
from .database import connect
from .doctor import diagnostics
from .history import grouped, recent_model, total, today
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


def show_status(db, console, config):
    period = config.period_minutes
    rows = latest(db)
    if not rows:
        console.print("Nenhum snapshot de cota encontrado nas sessões locais.")
    for row in rows:
        drop, eta = trend(db, row["limit_id"], row["window_name"], period)
        percent = remaining(row)
        color = "green" if percent >= 50 else "yellow" if percent >= 20 else "red"
        details = Table.grid(padding=(0, 2))
        details.add_column(style="bold", no_wrap=True)
        details.add_column(overflow="fold")
        details.add_row("Restante", Text(f"{percent:.1f}%", style=color))
        details.add_row("Reset", reset_text(row["resets_at"]))
        details.add_row("Créditos", row["credits"] if row["credits"] is not None else "indisponíveis")
        try:
            snapshot = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")).astimezone().strftime("%d/%m/%Y %H:%M")
        except ValueError:
            snapshot = row["timestamp"]
        details.add_row("Atualização", snapshot)
        if drop is not None and drop > 0:
            details.add_row("Queda", f"{drop:.1f} pontos em {period} min")
        try:
            snapshot_time = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
            if snapshot_time.tzinfo is None:
                snapshot_time = snapshot_time.replace(tzinfo=timezone.utc)
            stale = snapshot_time < datetime.now(timezone.utc) - timedelta(minutes=period)
        except ValueError:
            stale = True
        if stale:
            forecast = "snapshot antigo"
        elif eta is not None:
            forecast = f"{eta:.0f} min até esgotar (estimativa)"
        elif drop is None:
            forecast = "aguardando snapshots da cota"
        elif drop > 0:
            forecast = "aguardando 1 min de dados"
        else:
            forecast = f"sem queda nos últimos {period} min"
        details.add_row("Previsão", forecast)
        window_name = "semanal" if row["window_name"] == "weekly" else row["window_name"]
        title = Text(f'Cota oficial · {row["limit_id"]} · {window_name}', style="bold gold1")
        console.print(Panel(details, title=title, border_style="gold3", expand=False))
    hour_tokens = total(db, 1)
    period_tokens = total(db, period / 60)
    model = recent_model(db, period)
    usage = Table.grid(padding=(0, 2))
    usage.add_column(style="bold", no_wrap=True)
    usage.add_column(overflow="fold")
    usage.add_row("Hoje", f"{today(db):,} tokens")
    usage.add_row("Última hora", f"{hour_tokens:,} tokens")
    usage.add_row(f"Últimos {period} min", f"{period_tokens:,} tokens")
    usage.add_row("Ritmo", f"{period_tokens / period:,.1f} tokens/min")
    usage.add_row("Modelo ativo", model[0] if model else "sem atividade recente")
    if model:
        usage.add_row(f"Modelo/{period} min", f"{model[1]:,} tokens")
    console.print(Panel(usage, title="Uso local · estimativas", border_style="cyan", expand=False))


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
                    show_status(db, console, config)
                    for color, message in check(db, config):
                        console.print(f'[{color}]{message}[/{color}]')
                    time.sleep(seconds)
            except KeyboardInterrupt:
                return 0
        sync(db)
        if args.command == "status":
            show_status(db, console, config)
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
