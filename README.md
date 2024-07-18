# Dewey DeciBEL

Dewwey DeciBEL (DD) is a command line ID3 tagger (and intended also music player). As written, it is a bit destructive of what many would consider useful tags. The current supported tags are only:
 - Song title
 - Artist
 - Album title
 - Genre
 - Subgenres (uses comments section, so repurposable)
 - Track number
 - Recording Year
 - BPM

This project utilizes a prototype version of [Anhuelen](https://github.com/C-Bowen-Jr/anhuelen), so go there for a better implementation.

## Usage
### Fixing ID3 Tags
Currently only the folder (and non recursive) tag fixer is implemented.
```bash
python3 main.py -f /path/to/music/with/mp3s
```
That means ```/home/user/Music``` is not specific enough if your .mp3s are ```/home/user/Music/Some Artist/Here it is.mp3```

### Playing Music
Not yet implemented