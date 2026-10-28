#!/usr/bin/env python3
"""Safe, conservative Saint Viator career-win updater.

Fetches the current MaxPreps varsity girls volleyball season record, anchors the
2026-27 season to a user-verified 416 career wins, and NEVER fabricates wins on
HTTP errors, missing results, or unexpected page layouts.

The HTML scraper depends on a public, unofficial source and may need maintenance
if its publisher changes the page or blocks automated requests.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = ROOT / "data" / "state.json"
PUBLIC_PATH = ROOT / "site" / "wins.json"
SOURCE_URL = 'https://www.maxpreps.com/il/arlington-heights/saint-viator-lions/volleyball/schedule/'
MAX_WINS_PER_SEASON = 65


class _HTMLText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self._ignore: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in {'script', 'style', 'svg', 'noscript'}:
            self._ignore.append(tag)
        if tag == 'title':
            self._in_title = True

    def handle_endtag(self, tag):
        if self._ignore and self._ignore[-1] == tag:
            self._ignore.pop()
        if tag == 'title':
            self._in_title = False

    def handle_data(self, data):
        if not self._ignore:
            value = data.strip()
            if value:
                self.parts.append(value)
                if self._in_title:
                    self.title_parts.append(value)


def parse_maxpreps_record(html: str) -> tuple[str, int, int]:
    """Return (2026-27, wins, losses) or raise ValueError; fail closed."""
    parser = _HTMLText()
    parser.feed(html)
    title = ' '.join(parser.title_parts)
    text = ' '.join(parser.parts)
    if not re.search(r'Saint\s+Viator', title, re.I) or not re.search(r'Volleyball', title, re.I):
        raise ValueError('Unexpected team or sport in source page title')
    # MaxPreps page title uses a two-digit starting season: "Volleyball 26-27".
    m = re.search(r'Volleyball\s+(20\d{2}|\d{2})\s*[-–]\s*(\d{2})', title, re.I)
    if not m:
        # Current selected season is explicitly labelled in the schedule body.
        m = re.search(r'Saint\s+Viator\s+Volleyball\s+Schedule\s+(20\d{2}|\d{2})\s*[-–]\s*(\d{2})', text, re.I)
    if not m:
        raise ValueError('Current volleyball season not found')
    year = int(m.group(1))
    year = 2000 + year if year < 100 else year
    next_year = int(m.group(2))
    if year < 2026 or year > 2040 or (year + 1) % 100 != next_year:
        raise ValueError('Unexpected volleyball season')
    season = f'{year}-{next_year:02d}'
    # The live schedule has "Overall 12-18 0.400 Win Pct".
    # Do not count any "W 2-0" rows as a career win unless tied to a valid record.
    overall = re.search(r'\bOverall\s*(\d{1,3})\s*[-–]\s*(\d{1,3})\b', text, re.I)
    if not overall:
        raise ValueError('No posted season win/loss record')
    wins, losses = int(overall.group(1)), int(overall.group(2))
    if wins > MAX_WINS_PER_SEASON or losses > MAX_WINS_PER_SEASON:
        raise ValueError('Implausible season win/loss record')
    return season, wins, losses


def fetch_maxpreps() -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Curtin500Tribute/1.0; fan-maintained scoreboard)',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.8',
    }
    request = Request(SOURCE_URL, headers=headers)
    with urlopen(request, timeout=20) as response:
        final_url = response.geturl()
        if 'maxpreps.com' not in final_url:
            raise ValueError('Unexpected source redirect')
        return response.read(2_000_000).decode('utf-8', errors='replace')


def load_json(path: Path) -> dict:
    with path.open(encoding='utf-8') as stream:
        return json.load(stream)


def career_wins(state: dict) -> int:
    baseline_season = state['baseline_season']
    baseline_season_wins = int(state['baseline_season_wins'])
    baseline_wins = int(state['baseline_wins'])
    observed = state['season_records']
    delta = max(0, int(observed.get(baseline_season, baseline_season_wins)) - baseline_season_wins)
    for season, wins in observed.items():
        if season > baseline_season:
            delta += int(wins)
    return max(baseline_wins + delta, int(state.get('verified_floor', baseline_wins)))


def update_from_record(state: dict, season: str, observed_wins: int) -> dict:
    if season < state['baseline_season']:
        raise ValueError('Source returned a season before the confirmed baseline')
    if season > '2040-41' or observed_wins < 0 or observed_wins > MAX_WINS_PER_SEASON:
        raise ValueError('Implausible season or win count')
    # High-water marks prevent a delayed/incorrect source revision from removing wins.
    old = int(state['season_records'].get(season, 0))
    state['season_records'][season] = max(old, observed_wins)
    return state


def main() -> int:
    now = datetime.now(timezone.utc)
    updated_date = now.strftime('%Y-%m-%d')
    checked_at = now.isoformat(timespec='seconds').replace('+00:00', 'Z')
    state = load_json(STATE_PATH)
    current = load_json(PUBLIC_PATH)
    last_wins = int(current.get('wins', 416))
    last_date = current.get('updated', '2026-10-28')
    status = 'source_unavailable'
    received_season = None
    received_wins = None
    error = None
    try:
        season, wins, losses = parse_maxpreps_record(fetch_maxpreps())
        state = update_from_record(state, season, wins)
        received_season, received_wins = season, wins
        # A season record lower than the independently verified baseline may be stale.
        baseline_short = season == state['baseline_season'] and wins < int(state['baseline_season_wins'])
        status = 'source_lag' if baseline_short else 'ok'
        print(f'Checked MaxPreps {season}: {wins}-{losses}; {"source behind baseline" if baseline_short else "record parsed"}')
    except (ValueError, HTTPError, URLError, OSError, TimeoutError) as exc:
        error = f'{type(exc).__name__}: {exc}'
        print('Source check failed (keeping last confirmed total):', error, file=sys.stderr)

    calculated = career_wins(state)
    # Never decrease the published career number based on a feed error or revision.
    total = max(last_wins, calculated)
    if total != last_wins:
        last_date = updated_date
        print(f'New career total: {last_wins} -> {total}')
    if status == 'ok' and calculated < total:
        status = 'source_lag'

    payload = {
        'wins': total,
        'updated': last_date,
        'checked_at': checked_at,
        'sync_status': status,
        'source': 'MaxPreps Saint Viator girls varsity volleyball season record',
        'source_url': SOURCE_URL,
        'season': received_season,
        'reported_season_wins': received_wins,
    }
    PUBLIC_PATH.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    STATE_PATH.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    print('Published win count:', total, 'status:', status)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
