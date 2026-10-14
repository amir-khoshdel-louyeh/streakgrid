# streakgrid

Tactical habit tracker for Windows, Linux & Android — GitHub-style heatmaps, widgets, flexible scheduling, smart streaks & 100% on-device. Monorepo.

## Features (v1 parity with HabitForge Tactical)

- GitHub-style rolling heatmaps
- Home Screen widgets (Android) / Desktop widgets (Win/Linux), one-tap check-off
- Flexible scheduling: weekly, interval, custom + pause without breaking streak
- Smart streaks (schedule-aware)
- Multi-completion (e.g. 8 glasses → tap to increment)
- Color-coded folders
- Retroactive editing (tap any past date)
- Nag mode (persistent reminder until done)
- Stats dashboard: completion rate, best streak, weekly chart, per-habit breakdown
- 8 achievements (First Step → Century Club)
- 100% on-device, no account, no cloud

## Structure

```
apps/android/  # Kotlin + Jetpack Compose + Glance widgets
apps/windows/  # C# + WinUI 3 widgets
apps/linux/    # Python + PySide6 (Qt) widgets
core/docs/     # shared spec: data model, streak rules, heatmap algo
```

Shared data model (SQLite, same schema on all platforms):
`habits / completions / folders / pauses / achievements`

## Quickstart

Each app runs standalone. See `apps/<platform>/README.md` (coming next).

## Roadmap

- [ ] v0.1 core spec + SQLite schema
- [ ] v0.2 Android MVP (habits + heatmap + widget)
- [ ] v0.3 Linux + Windows MVP
- [ ] v1.0 stats dashboard + achievements + nag mode
