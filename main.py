from pytube import YouTube
from pytube import Playlist
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


def get_playlist_name(playlist):
    return playlist.title


print("Downloading...")
urls = [u for u in Playlist(url)] if "playlist" in url else [url]
playlist_name = get_playlist_name(Playlist(url)) if "playlist" in url else None
# add a directory to save the files if playlist_name is not None
if playlist_name:
    folder = os.path.join(folder, playlist_name)
    if not os.path.exists(folder):
        os.makedirs(folder)
print("Downloading " + str(len(urls)) + " videos")
for url in urls:
    try:
        yt = YouTube(url)
        stream = yt.streams.filter(only_audio=True).first()
        if stream is None:
            print("Error: No audio stream found for", url)
            continue
        stream.download(folder)
        print("Downloaded mp4(only audio) " + url)

        # Extract author (channel name) and thumbnail URL
        author = yt.author
        thumbnail_url = yt.thumbnail_url

        file_name = stream.default_filename
        mp4_path = os.path.join(folder, file_name)
        mp3_path = os.path.join(folder, os.path.splitext(file_name)[0] + ".mp3")
        new_file = mp.AudioFileClip(mp4_path)

        # Ensure correct audio duration by setting ffmpeg parameter
        new_file.write_audiofile(
            mp3_path, codec="libmp3lame", ffmpeg_params=["-q:a", "0"]
        )
        os.remove(mp4_path)

        # Modify MP3 metadata
        audio = ID3(mp3_path)
        audio.add(
            APIC(
                encoding=3,  # utf-8
                mime="image/jpeg",  # image/jpeg or image/png
                type=PictureType.COVER_FRONT,  # Front cover
                desc="Cover",
                data=requests.get(thumbnail_url).content,
            )
        )
        audio.save()

        # Modify MP3 metadata
        audio = EasyID3(mp3_path)
        audio["artist"] = author  # Modify artist/author metadata
        audio["title"] = yt.title  # Modify title metadata
        if playlist_name:
            audio["album"] = playlist_name  # Modify album metadata
        audio.save()

    except Exception as e:
        print("Error downloading " + url)
        print(e)
