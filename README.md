# Keystra — Realistic Typing Simulator

A desktop Python application that simulates realistic human typing into any active window.

## Features

- **Realistic human timing** — character delays based on keyboard layout difficulty, word complexity, and fatigue modelling
- **4 typing profiles** — Fast Typist, Average, Slow Thinker, Hunt & Peck
- **Typo simulation** — realistic neighboring-key mistakes with automatic backspace correction
- **Adjustable speed** — 5–150 WPM slider (overrides profile base speed)
- **Pause / Resume / Stop** — full playback control
- **Countdown timer** — 0 / 3 / 5 second countdown before typing begins
- **Live WPM graph** — real-time speed visualisation
- **Stats panel** — WPM, chars, words, typos, elapsed time

## Requirements

```
python >= 3.8
pynput        # keyboard simulation (optional — falls back to simulation mode)
tkinter       # usually included with Python
```

## Installation

```bash
pip install pynput
python human_typer.py
```

## Usage

1. Paste or type text into the input box
2. Choose a typing profile and adjust the WPM slider
3. Toggle "Simulate typos" on/off
4. Click **START TYPING**
5. Quickly switch focus to the target window (VS Code, browser, etc.)
6. Watch it type!

## Architecture

| Class | Responsibility |
|---|---|
| `Settings` | All configurable parameters |
| `TypingStats` | Real-time metrics (WPM, chars, typos) |
| `TypingEngine` | Core typing logic — timing, typos, pauses, keyboard output |
| `SpeedChart` | Canvas-based live WPM graph |
| `HumanTyperApp` | Main Tkinter window, UI, event handling |

## Disclaimer

This tool is intended for demonstrations, accessibility assistance, and typing practice only.