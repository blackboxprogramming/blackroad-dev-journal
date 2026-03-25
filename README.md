<!-- BlackRoad SEO Enhanced -->

# ulackroad dev journal

> Part of **[BlackRoad OS](https://blackroad.io)** — Sovereign Computing for Everyone

[![BlackRoad OS](https://img.shields.io/badge/BlackRoad-OS-ff1d6c?style=for-the-badge)](https://blackroad.io)
[![BlackRoad-Forge](https://img.shields.io/badge/Org-BlackRoad-Forge-2979ff?style=for-the-badge)](https://github.com/BlackRoad-Forge)

**ulackroad dev journal** is part of the **BlackRoad OS** ecosystem — a sovereign, distributed operating system built on edge computing, local AI, and mesh networking by **BlackRoad OS, Inc.**

### BlackRoad Ecosystem
| Org | Focus |
|---|---|
| [BlackRoad OS](https://github.com/BlackRoad-OS) | Core platform |
| [BlackRoad OS, Inc.](https://github.com/BlackRoad-OS-Inc) | Corporate |
| [BlackRoad AI](https://github.com/BlackRoad-AI) | AI/ML |
| [BlackRoad Hardware](https://github.com/BlackRoad-Hardware) | Edge hardware |
| [BlackRoad Security](https://github.com/BlackRoad-Security) | Cybersecurity |
| [BlackRoad Quantum](https://github.com/BlackRoad-Quantum) | Quantum computing |
| [BlackRoad Agents](https://github.com/BlackRoad-Agents) | AI agents |
| [BlackRoad Network](https://github.com/BlackRoad-Network) | Mesh networking |

**Website**: [blackroad.io](https://blackroad.io) | **Chat**: [chat.blackroad.io](https://chat.blackroad.io) | **Search**: [search.blackroad.io](https://search.blackroad.io)

---


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
