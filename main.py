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

    def __init__(self, filepath='',title='',artist='',album='',genre='',subgenre=[],track=0,year=1800,bpm=0,plays=0,skips=0):
        self.file_path = filepath
        self.title = title
        self.artist = artist
        self.album = album
        self.genre = genre
        self.subgenre = subgenre
        self.track = track
        self.release_year = year
        self.bpm = bpm
        self.play_count = plays
        self.skip_count = skips

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
    ti.title(f"{filepath}")
    new_tags = fetch_tags(song.artist, song.title)
    if new_tags == "error":
        return
    elif new_tags == None:
        blind_fix_tag_for(filepath)
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
    new_tags.genre = ti.prompt("Genre", f"{song.genre.name}")
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

# blind_fix_tag_for(string: filepath)
# Takes in a .mp3 filepath ie "./Scarlet Fire.mp3" or 
# "/home/<user>/Music/311/Come Original.mp3" but requests user to 
# manually provide ID3 tags. It will process the BPM and try to 
# suggest existing tags

def blind_fix_tag_for(filepath):
    # Load file and read tags
    song = eyed3.load(filepath)
    # Use Artist and Title search musicbrainz
    ti.title(f"{filepath}")
    new_tags = Song()
    # Use BPM Analyzer to add BPM
    new_tags.bpm = analyze_bpm(filepath)

    # Prompt user on correctness
    ti.title(f"{filepath}")
    new_tags.title = ti.prompt("Title", f"{song.tag.title}")
    new_tags.artist = ti.prompt("Artist", f"{song.tag.artist}")
    ti.inform("BPM", f"{new_tags.bpm}")
    new_tags.album = ti.prompt("Album", f"{song.tag.album}")
    new_tags.track = ti.prompt("Track",f"{song.tag.track_num}")
    new_tags.genre = ti.prompt("Genre", f"{song.tag.genre.name}")
    getsubgenres = ti.prompt("Subgenres (separate with comma)")
    new_tags.subgenre = getsubgenres.split(',')
    new_tags.release_year = ti.prompt("Release Year (YYYY)", f"{song.tag.recording_date}")

    confirmation = input("\nConfirm and write? (y or [Enter]/n)")
    if confirmation == 'n' or confirmation == 'N':
        return
    else:
        song.tag.clear()
        song.tag.title = new_tags.title
        song.tag.artist = new_tags.artist  
        song.tag.album = new_tags.album
        song.tag.genre = new_tags.genre
        song.tag.comments.set(u"")
        song.tag.comments[0].text = ",".join(new_tags.subgenre)
        song.tag.track_num = new_tags.track
        song.tag.recording_date = new_tags.release_year
        song.tag.bpm = new_tags.bpm
        song.tag.save()

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
# Takes in the artist and song title to spass to get_potentials(). Then 
# gives user interaction to select the most correct search result to be 
# tweaked
def fetch_tags(artist, title):
    print("\n")
    potentials = get_potentials(artist, title)
    if len(potentials) == 0:
        print(f"Error: {title} by {artist} returned 0 viable matches")
        return "error"
        
    # Buffer cursor 12 newlines down
    print("\n"*12)
    viewing = 0
    chosen = -1
    redraw = True
    while chosen < 0:
        if redraw:
            print(f"{ti.clr.CURSUP}"*12, end='') # 12 newlines to reverse
            for key, value in potentials[viewing].items():
                print(f"{' '*48}\r", end='')
                ti.inform(key, value)
            print(f"[{(viewing + 1)}/{len(potentials)}] Arrow keys [<-/->] to cycle. [Enter] accept. [0] skip")
            redraw = False
            
        pressed = getch()
        
        if pressed == 'right': # Right arrow, Next
            viewing = (viewing + 1) % len(potentials)
            redraw = True
        if pressed == 'left': # Left arrow, Previous
            viewing = (viewing - 1) % len(potentials)
            redraw = True
        if pressed == b'0':
            print(f"Giving up on {title} by {artist}")
            return "error"
        if pressed == b'\n' or pressed == b'\r' or pressed == '\r': # Enter
            chosen = viewing
        if pressed == b'\x1a': # Ctlr + Z
            exit()
        
    new_tags = Song(
                    file_path='',
                    title=potentials[chosen]["song"],
                    artist=potentials[chosen]["artist"],
                    album=potentials[chosen]["album"],
                    genre='',
                    subgenre=[],
                    track=potentials[chosen]["track"],
                    release_year=potentials[chosen]["first year"],
                    bpm=0,
                    play_count=0,
                    skip_count=0
                    )
                    
    return new_tags


# get_potentials(string: artist, string: title)
# Takes in the artist and song title to search musicbrainz.org
# Search each release in each recording, filters things like Vinyls and
# 'Now That's What I Call Music 394' like compilations, then returns 
# the list

def get_potentials(artist, title):
    url = f"https://musicbrainz.org/ws/2/recording/?query=artist:'{artist}' AND record:'{title}'&fmt=json"
    headers = {'User-Agent': 'dewey-decibel/1.0 ( nospam@me.com )'}
    response = requests.get(url, headers=headers)
    result = response.json()
    potentials = []
    
    for recordings in result.get('recordings', ''):
        confirm_artist     = recordings.get('artist-credit','')[0].get('name','')
        confirm_song_title = recordings.get('title','')
        confirm_score      = recordings.get('score','')
        first_drop         = recordings.get('first-release-date','')
        confirm_first_year = first_drop[:4] if len(first_drop) > 4 else first_drop
        for release in recordings.get('releases',''):
            try:
                confirm_album          = release.get('title','')
                confirm_status         = release.get('status','')
                confirm_primary_type   = release.get('release-group','').get('primary-type','')
                confirm_secondary_type = release.get('release-group','').get('secondary-type','')
                confirm_medium         = release.get('media','')[0].get('format','')
                confirm_track          = release.get('media','')[0].get('track','')[0].get('number','')
                release_date           = release.get('release-group','').get('date','')
                confirm_release_year   = release_date[:4] if len(release_date) > 4 else release_date
                confirm_country        = release.get('release-events','')[0].get('area','').get('name','')
            
                if (confirm_medium == 'CD' or confirm_medium == 'Digital Media') and confirm_status == 'Official' and confirm_artist != 'Various Artists' and confirm_score > 89:
                    potentials.append({
                               "artist":         confirm_artist,
                               "song":           confirm_song_title,
                               "track":          confirm_track,
                               "album":          confirm_album,
                               "medium":         confirm_medium,
                               "first year":     confirm_first_year,
                               "release year":   confirm_release_year,
                               "validity":       confirm_status,
                               "primary type":   confirm_primary_type,
                               "secondary type": confirm_secondary_type,
                               "country":        confirm_country})
            except Exception as e:
                pass
    return potentials

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
    parser.add_argument('--offline-folder', '-',
                        help="Parse folder for .mp3 files to fix ID3 tags without musicbrainz",
                        type=str,
                        default=None)
    parser.add_argument('--offline-song', '-l',
                        help="Fix ID3 tag on specific song without musicbrainz",
                        type=str,
                        default=None)

    args = parser.parse_args()
    if args.fix_folder != None:
        for file in glob.glob(os.path.join(args.fix_folder,"*.mp3")):
            fix_tag_for(file)
    if args.fix_song != None:
        fix_tag_for(arg.fix_song)

    if args.offline_folder != None:
        for file in glob.glob(os.path.join(args.offline_folder,"*.mp3")):
            blind_fix_tag_for(file)
    if args.offline_song != None:
        blind_fix_tag_for(arg.offline_song)
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