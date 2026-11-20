"""Local leaderboard (Ticket-04 section 3): top 10, persisted on disk across runs."""
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

# 3-12 word characters; Python's \w is Unicode-aware, so Vietnamese letters with diacritics are accepted too.
NAME_RE = re.compile(r'^\w{3,12}$')


def store_path():
    return Path(os.environ.get('DDL_LEADERBOARD', Path.home() / '.dao-den-long' / 'leaderboard.json'))


def load():
    p = store_path()
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
        return data.get('entries', []) if isinstance(data, dict) else []
    except (OSError, ValueError):
        return []


def _sorted(entries):
    # score descending; on a tie whoever reached it first stays on top
    return sorted(entries, key=lambda e: (-int(e['score']), e['achieved_at']))[:10]


def add(name, score, nights_won, seed):
    name = str(name).strip()
    if not NAME_RE.match(name):
        raise ValueError('Tên cần 3–12 ký tự chữ, số hoặc _')
    nights_won = int(nights_won)
    if not 0 <= nights_won <= 3:
        raise ValueError('nights_won must be 0-3')
    entry = {'name': name, 'score': int(score), 'nights_won': nights_won,
             'achieved_at': datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds'),
             'seed': int(seed)}
    entries = _sorted(load() + [entry])
    p = store_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix('.tmp')
    tmp.write_text(json.dumps({'entries': entries}, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(p)
    return entries


def export(out):
    with open(out, 'w', encoding='utf-8') as f:
        json.dump({'entries': _sorted(load())}, f, ensure_ascii=False, indent=2)
