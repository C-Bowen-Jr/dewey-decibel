import os
import glob
import random
import json
import requests
import threading
import time
import sys
import tty
import termios
from dataclasses import dataclass
from typing import List
from pprintpp import pprint
import eyed3
import librosa
import logging
import argparse
import anhuelen as ti

animate = False

class clr:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    GREYOUT = '\033[37m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

@dataclass
class Song:
    file_path: str
    title: str
    artist: str
    album: str
    genre: str
    subgenre: List[str]
    track: int
    release_year: int
    bpm: int
    play_count: int
    skip_count: int

# getch()
# Captures key presses. Returns "right" or "left" instead if corresponding 
# arrow key was pressed

def getch():
    fd = sys.stdin.fileno()
    restore = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1).encode()
        if ch == b'\x1b': # arrow keys escape sequence
            extra = sys.stdin.read(2).encode()
            if extra == b'[C':
                ch = "right"
            elif extra == b'[D':
                ch = "left"
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, restore)
    return ch

# fix_tag_for(string: filepath)
# Takes in a .mp3 filepath ie "./Scarlet Fire.mp3" or 
# "/home/<user>/Music/311/Come Original.mp3" and attempts to lookup and correct 
# ID3 tags. Song Title and Artist must be present to preform the search. BPM is 
# analyzed and added. The 'song.clear()' is destructive of all existing tags 
# including album art 

def fix_tag_for(filepath):
    # Load file and read tags
    song = eyed3.load(filepath).tag
    # Use Artist and Title search musicbrainz
    new_tags = fetch_tags(song.artist, song.title)
    if new_tags == "error":
        return
    # Use BPM Analyzer to add BPM
    new_tags.bpm = analyze_bpm(filepath)

    # Prompt user on correctness
    ti.title(f"{filepath}")
    ti.inform("Title", f"{song.title}")
    ti.inform("Artist", f"{song.artist}")
    ti.inform("BPM", f"{new_tags.bpm}")
    new_tags.album = ti.prompt("Album", f"{new_tags.album}")
    new_tags.track = ti.prompt("Track",f"{new_tags.track}")
    new_tags.genre = ti.prompt("Genre", f"{song.genre}")
    getsubgenres = ti.prompt("Subgenres (separate with comma)")
    new_tags.subgenre = getsubgenres.split(',')
    new_tags.release_year = ti.prompt("Release Year (YYYY)", f"{new_tags.release_year}")

    confirmation = input("\nConfirm and write? (y or [Enter]/n)")
    if confirmation == 'n' or confirmation == 'N':
        return
    else:
        song.clear()
        song.title = new_tags.title
        song.artist = new_tags.artist  
        song.album = new_tags.album
        song.genre = new_tags.genre
        song.comments.set(u"")
        song.comments[0].text = ",".join(new_tags.subgenre)
        song.track_num = new_tags.track
        song.recording_date = new_tags.release_year
        song.bpm = new_tags.bpm
        song.save()

# get_songs_album(string: title)
# TODO
def get_songs_album(title):
    pass#print(title)

# get_songs_chunk(TODO)
# TODO
def get_songs_chunk(thing):
    pass#print(thing)

# get_bellcurved_chunk_quantity()
# Randomize the number of songs that fit in the defined chunk
def get_bellcurved_chunk_quantity():
    percent = random.randint(1,51)
    logging.debug(f"bellcurve random: {percent}/50")
    match percent:
      case percent if percent < 10:
          return random.choice[1,5,6]
      case percent if percent < 30:
          return random.choice[2,4]
      case _:
          return 3

# thinking_animation()
# Display a spining bar while waiting on the BPM analyzer, this is handled 
# by a second thread
def thinking_animation():
    global animate
    frames = ['-', '\\', '|', '/']
    current_frame = 0
    while animate:
        print(f"Analyzing... {frames[current_frame]}", end='\r')
        current_frame = (current_frame + 1) % 4
        time.sleep(0.5)

# analyze_bpm(string: filepath) -> int
# Uses the same filepath as the ID3 lookup, also clears away the thinking 
# animation text before returning the found value
def analyze_bpm(filepath):
    global animate
    animate = True
    animation = threading.Thread(target=thinking_animation)
    animation.start()
    y, sr = librosa.load(filepath)
    bpm, _ = librosa.beat.beat_track(y=y, sr=sr)
    animate = False
    print("                    ", end='\r')
    return int(bpm)

# fetch_tags(string: artist, string: title)
# Takes in the artist and song title to search musicbrainz.org
# Search each release in each recording until a proper album is found. Known issue 
# is that this will never return a compilation album, so in the event of needing 
# that, a more manual search outside this program must be used and corrected for 
# in the fix_tags_for(). This also doesn't worry about the differences between say 
# a USA release compared to a Brazil, or Japanese release.
def fetch_tags(artist, title):
    print(f"Finding '{title}' by '{artist}'...")
    
    url = f"https://musicbrainz.org/ws/2/recording/?query=artist:'{artist}' AND record:'{title}'&fmt=json"
    headers = {'User-Agent': 'dewey-decibel/1.0 ( nospam@me.com )'}
    response = requests.get(url, headers=headers)
    result = response.json()
    
    for recordings in result.get('recordings', ''):
        for release in recordings.get('releases',''):
            try:
                album_title = release.get('title', '')
                album_type = release.get('release-group','').get('secondary-types','')
                primary_type = release.get('release-group','').get('primary-type','')
                medium = release.get('media','')[0].get('format','')
                status = release.get('status','')
                credit = release.get('artist-credit','')[0].get('name','')

                if album_type == '' and primary_type == 'Album' and (medium == 'CD' or medium == 'Digital Media') and status == 'Official' and credit != 'Various Artists':
                    release_date = recordings.get('first-release-date','')
                    area = release.get('release-events','')[0].get('area','').get('name','')
                    track = release.get('media','')[0].get('track','')[0].get('number','')
                    
                    new_tags = Song(
                                    file_path='',
                                    title=title,
                                    artist=artist,
                                    album=album_title,
                                    genre='',
                                    subgenre=[],
                                    track=track,
                                    release_year=release_date,
                                    bpm=0,
                                    play_count=0,
                                    skip_count=0
                                   )
                    
                    return new_tags
            except Exception as e:
                print("Error ",e)
    pprint(result)
    print("No match found, showing raw result of the search above")
    return "error"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fix-folder', '-f',
                        help="Parse folder for .mp3 files to fix ID3 tags",
                        type=str,
                        default=None)
    parser.add_argument('--fix-song', '-s',
                        help="Fix ID3 tag on specific song",
                        type=str,
                        default=None)
    parser.add_argument('--get-bpm', '-b',
                        help="Analyze specific song's BPM",
                        type=str,
                        default=None)

    args = parser.parse_args()
    if args.fix_folder != None:
        for file in glob.glob(os.path.join(args.fix_folder,"*.mp3")):
            fix_tag_for(file)
    if args.fix_song != None:
        fix_tag_for(arg.fix_song)
    if args.get_bpm != None:
        print(f"BPM: {analyze_bpm(args.get_bpm)}")

if __name__ == "__main__":
    main()
    """playlist = []
    library = get_test_library()

    fix_tag_for("./Renegade One.mp3")


    trait = random.choice(['artist', 'genre', 'subgenre', 'album'])
    
    if trait != 'subgenre':
        potential_vibes = list(set(getattr(song, trait) for song in library ))
    else:
        potential_vibes = list(set(random.choice(getattr(song, trait)) for song in library ))

    vibe = random.choice(potential_vibes)

    #print(f"Playing {trait}({vibe}):")
    if trait == 'album':
        playlist = get_songs_album(vibe)
    else:
        vibe_filtered_library = [song for song in library if getattr(song, trait) == vibe]
        playlist = get_songs_chunk(vibe_filtered_library)"""