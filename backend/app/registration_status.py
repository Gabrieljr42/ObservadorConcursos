"""Registration classification for filters, without rewriting source status."""
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
import unicodedata


def registration_situation(concurso, *, now=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    start, end = concurso.inscricao_inicio, concurso.inscricao_fim
    raw = getattr(concurso, 'raw_data', None) or {}
    amendments = raw.get('tenderproof', {}).get('amendments', [])
    current = (amendments[-1].get('periods') or {}).get('current', {}) if amendments else {}
    if start is not None and end is not None:
        # Legacy extraction stored date-only evidence as midnight. Use the
        # application's Brazilian calendar for those dates, not UTC midnight.
        clock = now.astimezone(ZoneInfo('America/Sao_Paulo'))
        def boundary(value, closing):
            precision = current.get('end_precision' if closing else 'start_precision', current.get('precision'))
            if precision != 'instant' and value.time().replace(tzinfo=None) == time.min:
                day = datetime.combine(value.date(), time.max if closing else time.min,
                                       tzinfo=clock.tzinfo)
                return day, True
            return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value, False
        opening, _ = boundary(start, False)
        closing, day_precision = boundary(end, True)
        if opening > closing:
            return 'unknown'
        if now < opening:
            return 'upcoming'
        if (now <= closing) if day_precision else (now < closing):
            return 'open'
        return 'closed'
    status = unicodedata.normalize('NFKD', concurso.status or '').encode('ascii', 'ignore').decode().lower().strip()
    if status in ('inscricoes abertas', 'inscricao aberta'):
        return 'open'
    if status == 'inscricoes em breve':
        return 'upcoming'
    if status in ('encerrado', 'encerrada', 'finalizado', 'finalizada', 'homologado', 'homologada'):
        return 'closed'
    return 'unknown'
