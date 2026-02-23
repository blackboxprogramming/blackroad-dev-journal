"""Tests for dev_journal.py"""
import json, os, sys, tempfile
from pathlib import Path
from datetime import date
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import dev_journal as dj


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(dj, "DB_PATH", str(tmp_path / "test_journal.db"))
    yield tmp_path


def _add(title="Test", mood="ok", hours=4, tags=None, accoms=None, blockers=None, tmrw=None):
    db = dj.get_db()
    return dj.insert_entry(db, date.today().isoformat(), title, "body",
                            tags or [], mood, hours, accoms or [], blockers or [], tmrw or [])

def test_db_initialises(tmp_db):
    db = dj.get_db()
    assert db is not None

def test_insert_and_fetch(tmp_db):
    eid = _add("My Entry", mood="great", hours=5)
    db  = dj.get_db()
    row = db.execute("SELECT * FROM entries WHERE id=?", (eid,)).fetchone()
    assert row["title"] == "My Entry"
    assert row["mood"]  == "great"

def test_row_to_entry(tmp_db):
    eid = _add(tags=["python", "api"])
    db  = dj.get_db()
    row = db.execute("SELECT * FROM entries WHERE id=?", (eid,)).fetchone()
    e   = dj.row_to_entry(row)
    assert isinstance(e, dj.JournalEntry)
    assert "python" in e.tags

def test_search_finds_entry(tmp_db):
    _add("Shipping OAuth feature")
    db   = dj.get_db()
    rows = db.execute(
        "SELECT e.* FROM entries e JOIN entries_fts f ON e.id=f.rowid WHERE entries_fts MATCH ?",
        ("OAuth",)
    ).fetchall()
    assert len(rows) >= 1

def test_search_no_results(tmp_db):
    _add("Nothing special")
    db = dj.get_db()
    rows = db.execute(
        "SELECT e.* FROM entries e JOIN entries_fts f ON e.id=f.rowid WHERE entries_fts MATCH ?",
        ("xyzzy_nonexistent",)
    ).fetchall()
    assert len(rows) == 0

def test_streak_consecutive(tmp_db):
    from datetime import timedelta
    db = dj.get_db()
    today = date.today()
    for i in range(3):
        d = (today - timedelta(days=i)).isoformat()
        dj.insert_entry(db, d, f"Day {i}", "", [], "ok", 4, [], [], [])
    # Should report streak >= 3
    rows = db.execute("SELECT DISTINCT date FROM entries ORDER BY date DESC").fetchall()
    dates = [date.fromisoformat(r["date"]) for r in rows]
    streak = 1
    for i in range(len(dates)-1):
        if (dates[i] - dates[i+1]).days == 1:
            streak += 1
        else:
            break
    assert streak >= 3

def test_mood_values_accepted(tmp_db):
    for mood in dj.MOODS:
        _add(f"Entry {mood}", mood=mood)
    db = dj.get_db()
    assert db.execute("SELECT COUNT(*) FROM entries").fetchone()[0] == len(dj.MOODS)

def test_accomplishments_stored(tmp_db):
    eid = _add(accoms=["Ship it", "Tests pass"])
    db  = dj.get_db()
    row = db.execute("SELECT * FROM entries WHERE id=?", (eid,)).fetchone()
    e   = dj.row_to_entry(row)
    assert "Ship it" in e.accomplishments

def test_blockers_stored(tmp_db):
    eid = _add(blockers=["DB is slow"])
    db  = dj.get_db()
    row = db.execute("SELECT * FROM entries WHERE id=?", (eid,)).fetchone()
    e   = dj.row_to_entry(row)
    assert "DB is slow" in e.blockers

def test_tomorrow_stored(tmp_db):
    eid = _add(tmrw=["Write docs", "Review PR"])
    db  = dj.get_db()
    row = db.execute("SELECT * FROM entries WHERE id=?", (eid,)).fetchone()
    e   = dj.row_to_entry(row)
    assert "Write docs" in e.tomorrow

def test_tag_cloud(tmp_db, capsys):
    _add(tags=["python", "api"])
    _add(tags=["python", "devops"])
    args = MagicMock()
    dj.cmd_tag_cloud(args)
    out = capsys.readouterr().out
    assert "python" in out
