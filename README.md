# Plex Subtitle Extractor

| :warning: This script interacts directly with your Plex database. It's highly recommended to stop Plex before running this script. |
|---|

This script will extract subtitles that have been added to Plex via Upload or On-Demand subtitle search via OpenSubtitles.org, named according to Plex's guidelines for external subtitles, i.e. matching the file name exactly, plus language code, forced flag (if applicable), and extension.

## Requirements

* Python 3

## Usage

```bash
python ExtractSubtitles.py [-h] [--save-inline] [-o OUTPUT_DIR] [-l LOG_FILE] [--no-log] [-f] [-c] [-d DATABASE_FOLDER] [-v]
```

### Options

Option | Description
---|---
`-h`, `--help` | Print the help article and exit
`--save-inline` | Save subtitles alongside the file associated with the subtitle. Default is to extract all subtitles to a single user-specified folder.
`-o`, `--output-dir OUTPUT_DIR` | Specify the location to save the extracted subtitles. Cannot be combined with `--save-inline`.
`-l`, `--log-file LOG_FILE` | Specify a file to save details about the extraction. Defaults to ExtractSubtitles.log in the current directory. If the file already exists, new log entries will be appended to the file.
`--no-log` | Don't save script run information to a log file.
`-f`, `--force` | Overwrite existing subtitle files. Default behavior is to ignore existing files.
`c`, `--confirm-override` | If a file with the same name already exists, confirm whether it should be overwritten.
`-d`, `--database-folder DATABASE_FOLDER` | Folder that container com.plexapp.plugins.library.db along with the blobs database.
`-v`, `--verbose` | Add additional information to the log file. No effect if `--no-log` is specified.

## Notes

If python 2 is invoked by default, you may need to use `python3` or `py -3` explicitly instead.