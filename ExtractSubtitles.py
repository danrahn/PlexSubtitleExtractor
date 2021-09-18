import sqlite3
import os
import gzip

db_base = os.path.join(os.environ['LOCALAPPDATA'], 'Plex Media Server', 'Plug-in Support', 'Databases')
blob_db = os.path.join(db_base, 'com.plexapp.plugins.library.blobs.db')
plex_db = os.path.join(db_base, 'com.plexapp.plugins.library.db')
if not os.path.isfile(blob_db) or not os.path.isfile(plex_db):
    print("BAD!")
    exit(0)
save_dir = input('Where do you want to save your extracted subtitles (full path)? ')
while not os.path.isdir(save_dir):
    create = ''
    while not create or create[0].lower() not in ['y', 'n']:
        create = input('That path does not exist. Would you like to create it (Y/N)? ')
    if create[0].lower() == 'y':
        try:
            os.makedir(save_dir)
        except OSError:
            save_dir = input('Error creating save path, please enter another location: ')

blobs = {}
with sqlite3.connect(blob_db) as conn:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT linked_id, blob FROM blobs WHERE blob_type=3")
    for row in cur.fetchall():
        blobs[row[0]] = {}
        blobs[row[0]]["blob"] = row[1]
    cur.close()

with sqlite3.connect(plex_db) as conn:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    for stream_id in blobs.keys():
        cur.execute(f"SELECT parts.file, stream.codec, stream.language, stream.forced FROM media_streams AS stream INNER JOIN media_parts AS parts ON parts.id=stream.media_part_id WHERE stream.id={stream_id}")
        row = cur.fetchall()
        if not row:
            print(f'Error grabbing associated file with stream id {stream_id}')
            continue
        row = row[0]
        blobs[stream_id]["info"] = { "file" : row[0], "codec" : row[1], "language" : row[2], "forced" : row[3] }
    cur.close()

for subtitle in blobs.values():
    base = os.path.splitext(os.path.basename(subtitle["info"]["file"]))[0]
    base += f'.{subtitle["info"]["language"]}'
    if subtitle['info']['forced'] == 1:
        base += '.forced'
    base += f'.{subtitle["info"]["codec"]}'
    data = gzip.decompress(subtitle['blob'])
    open_as = 'wb'
    if (subtitle['info']['codec'] in ['srt', 'ass', 'ssa']):
        open_as = 'w'
        data = data.decode().replace('\r\n', '\n')
    print(f'Writing {base}')
    with open(os.path.join(save_dir, base), open_as, encoding='utf-8') as sub_file:
        try:
            sub_file.write(data)
        except:
            print(data[:100])
            break