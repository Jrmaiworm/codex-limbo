"""Small terminal chart."""
from rich.console import Console


def render(rows, console: Console):
    peak = max((row["tokens"] for row in rows), default=0)
    for row in rows:
        width = round(row["tokens"] / peak * 30) if peak else 0
        color = "red" if width >= 24 else "yellow" if width >= 12 else "green"
        console.print(f'{row["hour"]} [{color}]{"█" * width}[/{color}] {row["tokens"]:,}')
