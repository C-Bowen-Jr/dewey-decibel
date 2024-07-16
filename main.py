import os
import random
import json
import requests
import threading
import time
import musicbrainzngs as mb
from dataclasses import dataclass
from typing import List
from pprintpp import pprint
import eyed3
import librosa
import logging
import argparse
import anhuelen as ti

mb.set_useragent(app='dewey_decible', version='0.1', contact='nospam@me.com')
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

def fix_tag_for(filepath):
    # Load file and read tags
    song = eyed3.load(filepath).tag
    # Use Artist and Title search musicbrainz
    new_tags = fetch_tags(song.artist, song.title)
    if new_tags == "error":
        return
    # Use BPM Analyzer to add BPM
    bpm = analyze_bpm(filepath)
    # Display correction block

    ti.title(f"{filepath}")
    ti.inform("Title", f"{song.title}")
    ti.inform("Artist", f"{song.artist}")
    ti.inform("BPM", f"{bpm}")
    new_tags.album = ti.prompt("Album", f"{new_tags.album}")
    new_tags.track = ti.prompt("Track",f"{new_tags.track}")
    new_tags.genre = ti.prompt("Genre", f"{song.genre}")
    getsubgenres = ti.prompt("Subgenres (separate with comma)")
    new_tags.subgenre = getsubgenres.split(',')
    new_tags.release_year = ti.prompt("Release Year (YYYY)", f"{new_tags.release_year}")

    confirmation = input("\nConfirm and write? (y or [Enter]/n)")
    if confirmation == 'n' or confirmation == 'N':
        pass
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

def get_test_library():
    songs = []
    with open("test_library.json", 'r') as f:
        data = json.load(f)
        for song_id3 in data['library']:
            song = Song(
                file_path=song_id3.get('file_path', ''),
                title=song_id3['title'],
                artist=song_id3['artist'],
                album=song_id3['album'],
                genre=song_id3['genre'],
                subgenre=song_id3.get('subgenre', []),
                track=song_id3['track'],
                release_year=song_id3['release_year'],
                bpm=song_id3['bpm'],
                play_count=song_id3['play_count'],
                skip_count=song_id3['skip_count']
            )
            songs.append(song)
        return songs

def get_songs_album(title):
    pass#print(title)

def get_songs_chunk(thing):
    pass#print(thing)

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

def thinking_animation():
    global animate
    frames = ['-', '\\', '|', '/']
    current_frame = 0
    while animate:
        print(f"Analyzing... {frames[current_frame]}", end='\r')
        current_frame = (current_frame + 1) % 4
        time.sleep(0.5)

def analyze_bpm(file_path):
    global animate
    animate = True
    animation = threading.Thread(target=thinking_animation)
    animation.start()
    y, sr = librosa.load(file_path)
    bpm, _ = librosa.beat.beat_track(y=y, sr=sr)
    animate = False
    print("                    ", end='\r')
    return int(bpm)

def fetch_tags(artist, title):
    print(f"Finding {title} by {artist}:")
    #result = mb.search_recordings(artist=artist, recording=title)
    url = f"https://musicbrainz.org/ws/2/recording/?query=artist:'{artist}' AND record:'{title}'&fmt=json"
    headers = {'User-Agent': 'dewey-decibel/0.1 ( nospam@me.com )'}
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

                if album_type == '' and primary_type == 'Album' and (medium == 'CD' or medium == 'Digital Media') and status == 'Official':
                    release_date = release.get('release-events','')[0].get('date','')
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
                    #pprint(new_tags)
                    return new_tags
                    #print(f" - Good find: date({release_date}) and track({track}) released on {album_title}")
            except Exception as e:
                print("why though? ",e)
    pprint(result)
    print("No match found, showing result above")
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

    args = parser.parse_args()
    pprint(args)

if __name__ == "__main__":
    playlist = []
    library = get_test_library()

    #print(analyze_bpm("Curl of the Burl.mp3"))
    #fetch_tags("bad info", "will fail")
    #fetch_tags("Gorillaz", "clint eastwood")
    #fetch_tags("Hath", "kenosis")
    #fetch_tags("tribulation", "leviathans")
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
        playlist = get_songs_chunk(vibe_filtered_library)