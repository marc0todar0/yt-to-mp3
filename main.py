from pytubefix import YouTube, Playlist
import os
import moviepy.editor as mp
from mutagen.id3 import ID3, APIC, PictureType
from mutagen.easyid3 import EasyID3
import requests
from input import get_user_input

urlProvided = None
if len(os.sys.argv) > 1:
    urlProvided = os.sys.argv[1]
folder, url = get_user_input(urlProvided)


# Get Playlist Name
def get_playlist_name(playlist):
    return playlist.title


print("Downloading...")
urls = [u for u in Playlist(url)] if "playlist" in url else [url]
playlist_name = get_playlist_name(Playlist(url)) if "playlist" in url else None

# Cleanup playlist name
if playlist_name and "Album - " in playlist_name:
    playlist_name = playlist_name.split(" - ")[1]

# Create directory for playlist
if playlist_name:
    folder = os.path.join(folder, playlist_name)
    if not os.path.exists(folder):
        os.makedirs(folder)

print(f"Downloading {len(urls)} videos")
max_track_number = len(urls)
track_number = 0

for url in urls:
    track_number += 1
    yt = YouTube(url, use_po_token=True)
    stream = yt.streams.filter(only_audio=True).first()
    if stream is None:
        print(f"Error: No audio stream found for {url}")
        continue
    stream.download(folder)
    print(f"Downloaded MP4 (only audio) {url}")

    # Extract metadata
    author = yt.author
    if "- Topic" in author:
        author = author.replace(" - Topic", "")

    thumbnail_url = yt.thumbnail_url
    publish_date = yt.publish_date.strftime("%Y") if yt.publish_date else "Unknown"

    file_name = stream.default_filename
    mp4_path = os.path.join(folder, file_name)
    mp3_path = os.path.join(folder, os.path.splitext(file_name)[0] + ".mp3")

    # Convert MP4 to MP3
    new_file = mp.AudioFileClip(mp4_path)
    new_file.write_audiofile(mp3_path, codec="libmp3lame", ffmpeg_params=["-q:a", "0"])
    os.remove(mp4_path)

    # Add Cover Art
    audio = ID3(mp3_path)
    audio.add(
        APIC(
            encoding=3,
            mime="image/jpeg",
            type=PictureType.COVER_FRONT,
            desc="Cover",
            data=requests.get(thumbnail_url).content,
        )
    )
    audio.save()

    # Set MP3 Metadata
    audio = EasyID3(mp3_path)
    audio["artist"] = author  # Track artist
    audio["title"] = yt.title  # Track title
    # audio["genre"] = infer_genre(yt.title)  # Inferred Genre
    audio["date"] = publish_date  # Release year
    if playlist_name:
        audio["albumartist"] = (
            author  # Album artist (for compilation use "Various Artists")
        )
        audio["album"] = playlist_name  # Album name from playlist
        audio["tracknumber"] = (
            f"{track_number}/{max_track_number}"  # Track number in album
        )
    metadata = {
        "artist": audio.get("artist"),
        "album": audio.get("album"),
        "tracknumber":audio.get("tracknumber"),
        "date": audio.get("date"),
        "title": audio.get("title"),
        "albumartist": audio.get("albumartist"),
    }
    print(
        f"Metadata set for: {yt.title}"
    )
    print(metadata)

    audio.save()
