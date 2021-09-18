# Plex Subtitle Extractor

| :warning: This is currently a work in progress |
|---|

This script will extract subtitles that have been added to Plex via Upload or On-Demand subtitle search via OpenSubtitles.org.

In its current state, the script will ask you for a save location (creating it if necessary) and save all subtitles found in the Plex database to that location.

Note: This script interacts directly with the Plex database. For best results, restart Plex before running this script, as that will force Plex to commit any in-memory changes to disk.

## Requirements

* Python 3

## Usage

```bash
python ExtractSubtitles.py
```