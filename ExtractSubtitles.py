import argparse
import datetime
import gzip
import os
import platform
import sqlite3
import sys

class SubtitleBlob:
    """
    Contains the details of a subtitle file stored in the Plex database
    """

    def __init__(self, stream_id, blob):
        self.stream_id = stream_id
        self.data = gzip.decompress(blob)

    def set_info(self, file, codec, language, forced):
        self.file = file
        self.codec = codec
        self.language = language
        self.forced = forced
    
    def get_name(self, inline):
        folder, basename = os.path.split(self.file)
        filename = os.path.splitext(basename)[0]
        filename += f'.{self.language}'
        if self.forced == 1:
            filename += '.forced'
        filename += f'.{self.codec}'
        return os.path.join(folder, filename) if inline else filename

class Log:
    """
    Simple logging class that writes output to a file.
    """

    file = None
    v = False
    def __init__(self, log_file, verbose):
        if log_file:
            self.file = open(log_file, 'a+')
        self.v = verbose

    def close(self):
        if self.file:
            self.write('Process exited.')
            self.file.close()
            self.file = None
    
    def verbose(self, text=''):
        if self.v:
            self.write(text)

    def error_and_exit(self, text=''):
        self.error(text)
        self.close()

    def error(self, text=''):
        text = f'ERROR: {text}'
        self.print(text)

    def print(self, text=''):
        print(text)
        self.write(text)

    def write(self, text=''):
        if self.file:
            log_time = '[' + datetime.datetime.now().strftime('%Y.%m.%d.%H:%M:%S.%f')[:-3] + ']'
            self.file.write(f'{log_time} {text}\n')

log = None

def process():
    parser = argparse.ArgumentParser()
    parser.add_argument('--save-inline', action='store_true', help='Save subtitles next to the video files, not a single output directory')
    parser.add_argument('-o', '--output-dir', help='Output directory to save subtitles to (cannot be combined with --save-inline)')
    parser.add_argument('-l', '--log-file', help='Log file name. Defaults to ExtractSubtitles.log in the current directory.')
    parser.add_argument('--no-log', action='store_true', help='Don\'t write verbose log information')
    parser.add_argument('-f', '--force', action='store_true', help='Overwrite existing subtitle files. Default behavior is to ignore existing subtitles')
    parser.add_argument('-c', '--confirm-override', action='store_true', help='If a subtitle already exists, confirm whether it should be overwritten')
    parser.add_argument('-d', '--database-folder', help='Folder that contains com.plexapp.plugins.library.db along with the blobs database')
    parser.add_argument('-v', '--verbose', action='store_true', help='Add additional information to the log file. No effect if --no-log is specified.')

    cmd_args = parser.parse_args()

    global log
    log = Log(None if cmd_args.no_log else (cmd_args.log_file if cmd_args.log_file else 'ExtractSubtitles.log'), cmd_args.verbose)
    log.write(f'ExtractSubtitles - New Run')
    log.write(f'\tArguments: ' + ' '.join(sys.argv))

    if cmd_args.save_inline and cmd_args.output:
        log.error_and_exit('Cannot specify both --save-inline and --output.')
        return

    if cmd_args.force and cmd_args.confirm_override:
        log.error_and_exit('Cannot specify both --force and --confirm-override.')
        return

    blob_db, plex_db = find_database(cmd_args)
    save_dir = get_save_dir(cmd_args)

    blobs = get_subtitle_blobs(blob_db)
    get_subtitle_details(blobs, plex_db)

    write_subtitles(blobs, save_dir, cmd_args)

    log.close()


def get_subtitle_blobs(database):
    """
    Return the gzip'd subtitle blobs stored in the Plex blob database
    """

    log.verbose('Retrieving all subtitles from the blobs database')
    blobs = {}
    with sqlite3.connect(database) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT linked_id, blob FROM blobs WHERE blob_type=3")
        for row in cur.fetchall():
            blobs[row[0]] = SubtitleBlob(row[0], row[1])
        cur.close()

    log.verbose(f'Found {len(blobs.keys())} subtitle(s) in the blobs database')
    return blobs


def get_subtitle_details(blobs, database):
    """
    Take the given blobs and find the file they're associated with, updating the given blobs with that information.
    """

    log.verbose('Correlating subtitles to file names')
    with sqlite3.connect(database) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        for stream_id in blobs.keys():
            cur.execute(f"SELECT parts.file, stream.codec, stream.language, stream.forced FROM media_streams AS stream INNER JOIN media_parts AS parts ON parts.id=stream.media_part_id WHERE stream.id={stream_id}")
            row = cur.fetchall()
            if not row:
                log.error(f'Could not find media file associated with stream id {stream_id}')
                continue
            row = row[0]
            blobs[stream_id].set_info(row[0], row[1], row[2], row[3])
        cur.close()
    log.verbose('Correlated subtitles to file names')


def write_subtitles(blobs, save_dir, cmd_args):
    """
    Write the given subtitles to the given save directory
    """

    total = 0
    saved = 0
    ignored = 0
    overwritten = 0
    errored = 0
    for subtitle in blobs.values():
        total += 1
        filename = subtitle.get_name(save_dir == None)
        if save_dir:
            filename = os.path.join(save_dir, filename)

        if os.path.exists(filename):
            if cmd_args.force or (cmd_args.confirm_override and get_yes_no(f'"{os.path.basename(filename)}" already exists, overwrite')):
                log.verbose(f'{os.path.basename(filename)} exists, but overwriting due to ' + ('--force' if cmd_args.force else 'user choice'))
                overwritten += 1
            else:
                log.verbose(f'{os.path.basename(filename)} exists, ignoring')
                ignored += 1
                continue

        log.print(f'Writing {filename}')
        with open(filename, 'wb') as sub_file:
            try:
                sub_file.write(subtitle.data)
                saved += 1
            except:
                log.error('Could not write data. Data snippet:')
                log.print(subtitle.data[:100])
                errored += 1
    
    log.write()
    log.print(f'Done! Processed {total} subtitles - saved {saved} (overwriting {overwritten} existing file(s)), ignored {ignored}, and failed to save {errored}')


def find_database(cmd_args):
    """
    Attempt to automatically find the required Plex databases. If not found, ask the user to provide the full path to the 'Databases' folder
    """

    db_base = None
    if cmd_args.database_folder:
        log.verbose(f'Found --database-folder argument: "{cmd_args.database_folder}"')
        db_base = cmd_args.database_folder
    else:
        log.verbose(f'Attempting to find Plex data directory')
        system = platform.system().lower()
        db_base = ''
        if system == 'windows' and 'LOCALAPPDATA' in os.environ:
            db_base = os.path.join(os.environ['LOCALAPPDATA'], 'Plex Media Server', 'Plug-in Support', 'Databases')
        elif system == 'darwin':
            db_base = os.path.join('~', 'Library', 'Application Support', 'Plex Media Server', 'Plug-in Support', 'Databases')
        elif system == 'linux' and 'PLEX_HOME' in os.environ:
            db_base = os.path.join(os.environ['PLEX_HOME'], 'Plex Media Server', 'Plug-in Support', 'Databases')

    # Surrounding quotes aren't necessary
    if len(db_base) > 0 and db_base[0] in ['"', "'"] and db_base[len(db_base) - 1] in ['"', "'"]:
        db_base = db_base[1:len(db_base) - 1]

    blob_db = 'com.plexapp.plugins.library.blobs.db'
    plex_db = 'com.plexapp.plugins.library.db'

    if len(db_base) > 0 and os.path.exists(db_base) and os.path.isfile(os.path.join(db_base, blob_db)) and os.path.isfile(os.path.join(db_base, plex_db)):
        blob_db = os.path.join(db_base, blob_db)
        plex_db = os.path.join(db_base, plex_db)
        return blob_db, plex_db

    log.verbose(f'Could not find databases in specified location, asking user...')
    db_base = input('Could not find database directory. Please enter the full path to the "Databases" folder: ')
    while not os.path.exists(db_base) or not os.path.isfile(os.path.join(db_base, blob_db)) or not os.path.isfile(os.path.join(db_base, plex_db)):
        db_base = input('That directory does not exist (or does not contain the Plex databases). Please enter the full path: ')
    
    log.verbose(f'Got database location: "{db_base}"')
    return os.path.join(db_base, blob_db), os.path.join(db_base, plex_db)


def get_save_dir(cmd_args):
    """
    Ask the user where they want to save the subtitles
    """

    if cmd_args.save_inline:
        log.verbose('--save-inline specified, not processing save_dir')
        return None

    save_dir = cmd_args.output_dir if cmd_args.output_dir else input('Where do you want to save your extracted subtitles (full path)? ')
    while not os.path.isdir(save_dir):
        if get_yes_no('Provided output path does not exist. Would you like to create it'):
            try:
                os.makedirs(save_dir)
                return save_dir
            except OSError:
                log.error('Sorry, something went wrong attempting to create the save directory.')
        save_dir = input('Where do you want to save your extracted subtitles (full path)? ')
    
    log.verbose(f'Got save dir: "{save_dir}"')
    return save_dir


def get_yes_no(prompt):
    """
    Return True or False depending on whether the user enters 'Y' or 'N'
    """
    while True:
        response = input(f'{prompt} (y/n)? ')
        ch = response.lower()[0] if len(response) > 0 else 'x'
        if ch in ['y', 'n']:
            return ch == 'y'


process()