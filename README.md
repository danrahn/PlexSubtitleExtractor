# Plex Subtitle Extractor

| :warning: This is currently a work in progress |
|---|

This script will extract subtitles that have been added to Plex via Upload or On-Demand subtitle search via OpenSubtitles.org.

In its current state, the script will ask you for a save location (creating it if necessary) and save all subtitles found in the Plex database to that location, with names that match the file they're associated with. For example, if an English SRT was uploaded for `The Office - S01E01 - Pilot.mkv`, it will be saved to the specified location as `The Office - S01E01 - Pilot.en.mkv`. It should also detect forced subtitles and name them accordingly (`The Office - S01E01 - Pilot.en.forced.mkv`).

Note: This script interacts directly with the Plex database. For best results, restart Plex before running this script, as that will force Plex to commit any in-memory changes to disk.

## Requirements

* Python 3

## Usage

```bash
python ExtractSubtitles.py
```

If python 2 is invoked by default, you may need to use `python3` or `py -3` explicitly instead.