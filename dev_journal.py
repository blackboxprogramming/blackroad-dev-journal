#!/usr/bin/env python3
"""BlackRoad Dev Journal – daily developer log with search, streaks, and export."""

import argparse
import json
import os
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional, List

GREEN  = "\033[0;32m"
RED    = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN   = "\033[0;36m"
BLUE   = "\033[0;34m"
BOLD   = "\033[1m"
NC     = "\033[0m"

def ok(m):   print(f"{GREEN}✓{NC} {m}")
def err(m):  print(f"{RED}✗{NC} {m}", file=sys.stderr)
def info(m): print(f"{CYAN}ℹ{NC} {m}")
def warn(m): print(f"{YELLOW}⚠{NC} {m}")

DB_PATH = os.path.expanduser("~/.blackroad-personal/journal.db")
MOODS   = ("great", "good", "ok", "rough")

# ── Data model ─────────────────────────────────────────────────────────────────
@dataclass
class JournalEntry:
    id: int
    date: str
    title: str
    body: str
    tags: List[str]
    mood: str
    focus_hours: float
    accomplishments: List[str]
    blockers: List[str]
    tomorrow: List[str]
    created_at: str

# ── DB ─────────────────────────────────────────────────────────────────────────
def get_db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS entries (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT NOT NULL,
            title           TEXT NOT NULL,
            body            TEXT NOT NULL DEFAULT '',
            tags_json       TEXT NOT NULL DEFAULT '[]',
            mood            TEXT NOT NULL DEFAULT 'ok',
            focus_hours     REAL NOT NULL DEFAULT 0,
            accomplishments TEXT NOT NULL DEFAULT '[]',
            blockers        TEXT NOT NULL DEFAULT '[]',
            tomorrow        TEXT NOT NULL DEFAULT '[]',
            created_at      TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
            title, body, tags_json, content='entries', content_rowid='id'
        );
        CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
            INSERT INTO entries_fts(rowid, title, body, tags_json)
            VALUES (new.id, new.title, new.body, new.tags_json);
        END;
        CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
            INSERT INTO entries_fts(entries_fts, rowid, title, body, tags_json)
            VALUES ('delete', old.id, old.title, old.body, old.tags_json);
        END;
        CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
            INSERT INTO entries_fts(entries_fts, rowid, title, body, tags_json)
            VALUES ('delete', old.id, old.title, old.body, old.tags_json);
            INSERT INTO entries_fts(rowid, title, body, tags_json)
            VALUES (new.id, new.title, new.body, new.tags_json);
        END;
    """)
    conn.commit()
    return conn

def row_to_entry(row) -> JournalEntry:
    d = dict(row)
    return JournalEntry(
        id=d["id"], date=d["date"], title=d["title"], body=d["body"],
        tags=json.loads(d["tags_json"]), mood=d["mood"],
        focus_hours=d["focus_hours"],
        accomplishments=json.loads(d["accomplishments"]),
        blockers=json.loads(d["blockers"]),
        tomorrow=json.loads(d["tomorrow"]),
        created_at=d["created_at"],
    )

def insert_entry(db, date_str, title, body, tags, mood, focus_hours, accomplishments, blockers, tomorrow) -> int:
    cur = db.execute("""
        INSERT INTO entries (date, title, body, tags_json, mood, focus_hours,
            accomplishments, blockers, tomorrow, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (date_str, title, body, json.dumps(tags), mood, focus_hours,
          json.dumps(accomplishments), json.dumps(blockers), json.dumps(tomorrow),
          datetime.now().isoformat()))
    db.commit()
    return cur.lastrowid

def print_entry(e: JournalEntry, short=False):
    mood_icon = {"great": "🚀", "good": "😊", "ok": "😐", "rough": "😔"}.get(e.mood, "?")
    print(f"\n{BOLD}[{e.id}] {e.date}  {mood_icon} {e.mood.upper()}  ⏱ {e.focus_hours}h{NC}")
    print(f"{CYAN}{e.title}{NC}")
    if e.tags:
        print(f"  tags: {', '.join('#'+t for t in e.tags)}")
    if short:
        return
    if e.body:
        print(f"\n{e.body}\n")
    if e.accomplishments:
        print(f"{GREEN}Accomplishments:{NC}")
        for a in e.accomplishments: print(f"  ✓ {a}")
    if e.blockers:
        print(f"{RED}Blockers:{NC}")
        for b in e.blockers: print(f"  ✗ {b}")
    if e.tomorrow:
        print(f"{YELLOW}Tomorrow:{NC}")
        for t in e.tomorrow: print(f"  → {t}")

# ── Commands ──────────────────────────────────────────────────────────────────
def cmd_add(args):
    db    = get_db()
    today = date.today().isoformat()
    tags  = [t.strip().lstrip("#") for t in args.tags.split(",")] if args.tags else []
    accoms   = [a.strip() for a in args.accomplishments.split("|")] if args.accomplishments else []
    blockers = [b.strip() for b in args.blockers.split("|")] if args.blockers else []
    tmrw     = [t.strip() for t in args.tomorrow.split("|")] if args.tomorrow else []

    if args.mood not in MOODS:
        err(f"mood must be one of: {', '.join(MOODS)}"); sys.exit(1)

    eid = insert_entry(db, today, args.title, args.body or "",
                       tags, args.mood, args.hours, accoms, blockers, tmrw)
    ok(f"Journal entry #{eid} added for {today}")

def cmd_today(args):
    db    = get_db()
    today = date.today().isoformat()
    rows  = db.execute("SELECT * FROM entries WHERE date=? ORDER BY id", (today,)).fetchall()
    if not rows:
        warn(f"No entries for {today}"); return
    for row in rows:
        print_entry(row_to_entry(row))

def cmd_show(args):
    db  = get_db()
    row = db.execute("SELECT * FROM entries WHERE id=?", (args.id,)).fetchone()
    if not row:
        err(f"Entry #{args.id} not found"); return
    print_entry(row_to_entry(row))

def cmd_search(args):
    db  = get_db()
    rows = db.execute("""
        SELECT e.* FROM entries e
        JOIN entries_fts f ON e.id = f.rowid
        WHERE entries_fts MATCH ?
        ORDER BY e.date DESC LIMIT 20
    """, (args.query,)).fetchall()
    if not rows:
        info(f"No results for \"{args.query}\""); return
    info(f"{len(rows)} result(s) for \"{args.query}\"")
    for row in rows:
        print_entry(row_to_entry(row), short=True)

def cmd_streak(args):
    db   = get_db()
    rows = db.execute("SELECT DISTINCT date FROM entries ORDER BY date DESC").fetchall()
    if not rows:
        info("No entries yet"); return
    dates  = [date.fromisoformat(r["date"]) for r in rows]
    streak = 1
    for i in range(len(dates)-1):
        if (dates[i] - dates[i+1]).days == 1:
            streak += 1
        else:
            break
    ok(f"Current streak: {streak} day(s)")
    print(f"  Total days with entries: {len(dates)}")

def cmd_mood_trend(args):
    db   = get_db()
    days = args.days or 30
    since = (date.today() - timedelta(days=days)).isoformat()
    rows  = db.execute(
        "SELECT mood, COUNT(*) as cnt FROM entries WHERE date>=? GROUP BY mood",
        (since,)).fetchall()
    if not rows:
        warn("No data"); return
    total = sum(r["cnt"] for r in rows)
    print(f"\n{BOLD}Mood distribution (last {days} days):{NC}")
    for row in sorted(rows, key=lambda r: MOODS.index(r["mood"])):
        pct = row["cnt"] / total * 100
        bar = "█" * int(pct / 5)
        icon = {"great":"🚀","good":"😊","ok":"😐","rough":"😔"}.get(row["mood"],"?")
        print(f"  {icon} {row['mood']:<6} {bar:<20} {row['cnt']} ({pct:.0f}%)")

def cmd_weekly(args):
    db   = get_db()
    today = date.today()
    start = today - timedelta(days=today.weekday())
    rows  = db.execute(
        "SELECT * FROM entries WHERE date>=? ORDER BY date", (start.isoformat(),)
    ).fetchall()
    total_hours = sum(r["focus_hours"] for r in rows)
    print(f"\n{BOLD}Weekly summary  {start} → {today}{NC}")
    print(f"  Entries    : {len(rows)}")
    print(f"  Focus hrs  : {total_hours:.1f}")
    all_accoms = []
    for r in rows:
        all_accoms.extend(json.loads(r["accomplishments"]))
    if all_accoms:
        print(f"\n{GREEN}Accomplishments this week:{NC}")
        for a in all_accoms: print(f"  ✓ {a}")

def cmd_export_md(args):
    db    = get_db()
    start = args.start or "2020-01-01"
    end   = args.end   or date.today().isoformat()
    rows  = db.execute(
        "SELECT * FROM entries WHERE date BETWEEN ? AND ? ORDER BY date",
        (start, end)
    ).fetchall()
    if not rows:
        warn("No entries in range"); return
    out = f"# Dev Journal Export  {start} → {end}\n\n"
    for row in rows:
        e = row_to_entry(row)
        out += f"## {e.date} – {e.title}\n\n"
        out += f"**Mood:** {e.mood}  **Focus:** {e.focus_hours}h\n\n"
        if e.tags: out += f"**Tags:** {', '.join('#'+t for t in e.tags)}\n\n"
        if e.body: out += f"{e.body}\n\n"
        if e.accomplishments:
            out += "**Accomplishments:**\n"
            for a in e.accomplishments: out += f"- {a}\n"
            out += "\n"
        if e.blockers:
            out += "**Blockers:**\n"
            for b in e.blockers: out += f"- {b}\n"
            out += "\n"
    fname = f"journal_{start}_{end}.md"
    with open(fname, "w") as f: f.write(out)
    ok(f"Exported {len(rows)} entries to {fname}")

def cmd_tag_cloud(args):
    db   = get_db()
    rows = db.execute("SELECT tags_json FROM entries").fetchall()
    freq: dict = {}
    for row in rows:
        for tag in json.loads(row["tags_json"]):
            freq[tag] = freq.get(tag, 0) + 1
    if not freq:
        warn("No tags yet"); return
    print(f"\n{BOLD}Tag cloud:{NC}")
    for tag, cnt in sorted(freq.items(), key=lambda x: -x[1]):
        bar = "█" * cnt
        print(f"  #{tag:<20} {bar} {cnt}")

def cmd_list(args):
    db   = get_db()
    rows = db.execute("SELECT * FROM entries ORDER BY date DESC LIMIT 20").fetchall()
    if not rows:
        warn("No entries"); return
    for row in rows:
        print_entry(row_to_entry(row), short=True)

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(prog="br-journal", description="BlackRoad Dev Journal")
    sub    = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add", help="Add a journal entry")
    p.add_argument("title")
    p.add_argument("--body",            default="")
    p.add_argument("--tags",            default="")
    p.add_argument("--mood",            default="ok", choices=MOODS)
    p.add_argument("--hours",           type=float, default=0)
    p.add_argument("--accomplishments", default="", help="Pipe-separated list")
    p.add_argument("--blockers",        default="")
    p.add_argument("--tomorrow",        default="")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("today", help="Show today's entries"); p.set_defaults(func=cmd_today)
    p = sub.add_parser("show",  help="Show entry by ID")
    p.add_argument("id", type=int); p.set_defaults(func=cmd_show)

    p = sub.add_parser("search", help="Full-text search")
    p.add_argument("query"); p.set_defaults(func=cmd_search)

    p = sub.add_parser("streak", help="Show current streak"); p.set_defaults(func=cmd_streak)

    p = sub.add_parser("mood-trend", help="Mood distribution")
    p.add_argument("--days", type=int, default=30); p.set_defaults(func=cmd_mood_trend)

    p = sub.add_parser("weekly", help="Weekly summary"); p.set_defaults(func=cmd_weekly)

    p = sub.add_parser("export-md", help="Export to Markdown")
    p.add_argument("--start", default=None); p.add_argument("--end", default=None)
    p.set_defaults(func=cmd_export_md)

    p = sub.add_parser("tag-cloud", help="Show tag frequency"); p.set_defaults(func=cmd_tag_cloud)
    p = sub.add_parser("list",      help="List recent entries");  p.set_defaults(func=cmd_list)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
