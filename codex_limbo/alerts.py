"""Threshold checks for local usage and quota changes."""
from datetime import datetime, timedelta, timezone
from .history import total
from .quota import latest, trend


def check(db, config) -> list[tuple[str, str]]:
    notices = []
    tokens = total(db, config.period_minutes / 60)
    high_tokens = tokens >= config.token_threshold
    primary_reported = False
    for row in latest(db):
        try:
            snapshot_time = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
            if snapshot_time.tzinfo is None:
                snapshot_time = snapshot_time.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if snapshot_time < datetime.now(timezone.utc) - timedelta(minutes=config.period_minutes):
            continue
        drop, minutes_left = trend(db, row["limit_id"], row["window_name"], config.period_minutes)
        high_drop = drop is not None and drop >= config.quota_drop_percent
        near_exhaustion = minutes_left is not None and minutes_left < config.exhaustion_minutes
        is_primary = row["window_name"] == "5h"
        if not (high_drop or near_exhaustion or (high_tokens and is_primary)):
            continue
        if is_primary:
            primary_reported = True
        name = f'{row["limit_id"]} {"semanal" if row["window_name"] == "weekly" else row["window_name"]}'
        lines = [f"Cota {name}", f"  Últimos {config.period_minutes} min: {tokens:,} tokens locais"]
        if drop is None:
            lines.append("  Percentual da cota: faltam snapshots para calcular")
        else:
            lines.append(f"  Cota consumida: {drop:.1f}% nos últimos {config.period_minutes} min")
        if high_tokens or high_drop:
            lines.append("  Consumo elevado.")
        if minutes_left is None:
            lines.append("  Previsão de esgotamento indisponível por enquanto.")
        else:
            lines.append(f"  Nesse ritmo, a cota pode acabar em {minutes_left:.0f} min (estimativa).")
        notices.append(("red" if high_tokens or near_exhaustion else "yellow", "\n".join(lines)))
    if high_tokens and not primary_reported:
        notices.append(("red", f"Últimos {config.period_minutes} min: {tokens:,} tokens locais. Consumo elevado.\n  Sem snapshots recentes da cota para calcular percentual ou previsão."))
    return notices
