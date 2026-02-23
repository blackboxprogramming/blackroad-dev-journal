# blackroad-dev-journal

Developer journal and daily log with full-text search, mood tracking, streaks, and Markdown export.

## Usage

```bash
# Add an entry
python dev_journal.py add "Shipped auth module" \
  --mood great --hours 6 \
  --tags "auth,python,backend" \
  --accomplishments "OAuth2 done|tests passing" \
  --blockers "refresh token edge case" \
  --tomorrow "add rate limiting|write docs"

# View today
python dev_journal.py today

# Full-text search
python dev_journal.py search "OAuth2"

# Current streak
python dev_journal.py streak

# Mood trend (last 30 days)
python dev_journal.py mood-trend --days 30

# Weekly summary
python dev_journal.py weekly

# Tag cloud
python dev_journal.py tag-cloud

# Export to Markdown
python dev_journal.py export-md --start 2025-01-01 --end 2025-12-31

# List recent entries
python dev_journal.py list
```

## Moods

`great` 🚀 | `good` 😊 | `ok` 😐 | `rough` 😔

## Storage

SQLite at `~/.blackroad-personal/journal.db` with FTS5 full-text search.

## License

Proprietary — BlackRoad OS, Inc.
