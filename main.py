import yt_dlp
import os
import moviepy.editor as mp
from mutagen.id3 import ID3, APIC, PictureType
from mutagen.easyid3 import EasyID3
import requests
import re
import sys
import time
from typing import List, Dict, Optional
import json

def sanitize_string(text: str) -> str:
    # Allow letters, numbers, spaces, dots, parentheses, and some special characters
    return re.sub(r'[^a-zA-Z0-9\s_\-\.\(\)]', '', text)

def clean_url(url: str) -> str:
    # Remove playlist parameter if present in a watch URL
    if 'watch?' in url and 'list=' in url:
        base_url = url.split('&list=')[0]
        return base_url
    return url

def download_playlist(url: str, folder: str) -> None:
    # Clean the URL if it's a single track with playlist parameter
    if 'watch?' in url:
        url = clean_url(url)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(folder, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'concurrent_fragment_downloads': 16,  # Increased concurrent downloads
        'retries': 10,
        'fragment_retries': 10,
        'skip_unavailable_fragments': True,
        'noprogress': True,
        'extract_flat': False,  # Changed from "in_playlist" to False
        'playlist_items': '1:25',  # Limit to first 25 items for safety
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            print("Getting track information...")
            # Get info
            info = ydl.extract_info(url, download=False)
            
            is_playlist = 'entries' in info and len(info.get('entries', [])) > 1
            
            if is_playlist:
                # It's a playlist
                playlist_name = info.get('title', 'Unknown Playlist')
                if "Album - " in playlist_name:
                    playlist_name = playlist_name.split(" - ")[1]
                playlist_name = sanitize_string(playlist_name)
                folder = os.path.join(folder, playlist_name)
                total_tracks = len(info['entries'])
                
                # Get album info from first track
                first_track = next((entry for entry in info['entries'] if entry), None)
                if first_track:
                    album_artist = first_track.get('artist', first_track.get('uploader', 'Unknown Artist'))
                    if "- Topic" in album_artist:
                        album_artist = album_artist.replace(" - Topic", "")
                    
                    # Get cover art from first track
                    cover_art_data = None
                    if first_track.get('thumbnail'):
                        try:
                            print("Downloading cover art...")
                            cover_art_data = requests.get(first_track['thumbnail']).content
                        except Exception as e:
                            print(f"Warning: Could not download cover art - {str(e)}")
            else:
                # It's a single video
                folder = os.path.join(folder, "singoli")
                total_tracks = 1
                album_artist = info.get('artist', info.get('uploader', 'Unknown Artist'))
                if "- Topic" in album_artist:
                    album_artist = album_artist.replace(" - Topic", "")
                cover_art_data = None
                if info.get('thumbnail'):
                    try:
                        print("Downloading cover art...")
                        cover_art_data = requests.get(info['thumbnail']).content
                    except Exception as e:
                        print(f"Warning: Could not download cover art - {str(e)}")
                playlist_name = None
            
            if not os.path.exists(folder):
                os.makedirs(folder)
            
            # Update output template with new folder
            ydl_opts['outtmpl'] = os.path.join(folder, '%(title)s.%(ext)s')
            
            # Download with updated options
            print(f"\nDownloading {'playlist' if is_playlist else 'track'}...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                result = ydl_download.download([url])
            
            # Set metadata
            print("\nSetting metadata...")
            processed_files = []
            
            if is_playlist:
                for i, entry in enumerate(info['entries'], 1):
                    if entry:
                        try:
                            title = entry.get('title', f'Track {i}')
                            possible_filenames = [
                                title,
                                sanitize_string(title),
                                title.replace('(', '').replace(')', ''),
                                title.replace(' ', '')
                            ]
                            
                            mp3_path = None
                            for filename in possible_filenames:
                                test_path = os.path.join(folder, f"{filename}.mp3")
                                if os.path.exists(test_path):
                                    mp3_path = test_path
                                    break
                            
                            if mp3_path and mp3_path not in processed_files:
                                print(f"Processing {i}/{total_tracks}: {title}")
                                processed_files.append(mp3_path)
                                
                                # Add ID3 tags
                                try:
                                    audio = ID3(mp3_path)
                                except:
                                    audio = ID3()
                                
                                # Add cover art
                                if cover_art_data:
                                    audio.add(
                                        APIC(
                                            encoding=3,
                                            mime='image/jpeg',
                                            type=PictureType.COVER_FRONT,
                                            desc='Cover',
                                            data=cover_art_data
                                        )
                                    )
                                audio.save(mp3_path)
                                
                                # Set basic metadata
                                audio = EasyID3(mp3_path)
                                audio['title'] = title
                                audio['artist'] = album_artist
                                audio['album'] = playlist_name
                                audio['albumartist'] = album_artist
                                audio['tracknumber'] = f"{i}/{total_tracks}"
                                
                                if entry.get('release_year'):
                                    audio['date'] = str(entry['release_year'])
                                elif entry.get('upload_date'):
                                    audio['date'] = entry['upload_date'][:4]
                                
                                audio.save()
                        except Exception as e:
                            print(f"Error processing track {i}: {str(e)}")
                            continue
                
                print(f"\nSuccessfully processed {len(processed_files)} out of {total_tracks} tracks")
            else:
                # Single track metadata
                try:
                    title = info.get('title', 'Unknown Title')
                    possible_filenames = [
                        title,
                        sanitize_string(title),
                        title.replace('(', '').replace(')', ''),
                        title.replace(' ', '')
                    ]
                    
                    mp3_path = None
                    for filename in possible_filenames:
                        test_path = os.path.join(folder, f"{filename}.mp3")
                        if os.path.exists(test_path):
                            mp3_path = test_path
                            break
                    
                    if mp3_path:
                        print(f"Processing: {title}")
                        
                        # Add ID3 tags
                        try:
                            audio = ID3(mp3_path)
                        except:
                            audio = ID3()
                        
                        # Add cover art
                        if cover_art_data:
                            audio.add(
                                APIC(
                                    encoding=3,
                                    mime='image/jpeg',
                                    type=PictureType.COVER_FRONT,
                                    desc='Cover',
                                    data=cover_art_data
                                )
                            )
                        audio.save(mp3_path)
                        
                        # Set basic metadata (no album info for single tracks)
                        audio = EasyID3(mp3_path)
                        audio['title'] = title
                        audio['artist'] = album_artist
                        
                        if info.get('release_year'):
                            audio['date'] = str(info['release_year'])
                        elif info.get('upload_date'):
                            audio['date'] = info['upload_date'][:4]
                        
                        audio.save()
                        print("Metadata set successfully")
                    else:
                        print(f"Warning: File not found - {title}")
                except Exception as e:
                    print(f"Error processing track: {str(e)}")
            
            print("\nDownload and metadata update completed!")
            
        except Exception as e:
            print(f"Error downloading: {str(e)}")
            sys.exit(1)

# Get input URL
start_time = time.time()

urlProvided = None
if len(sys.argv) > 1:
    urlProvided = sys.argv[1]

# Get folder path from config
with open("config.json") as f:
    config = json.load(f)
    folder = config["folder"]

if not os.path.exists(folder):
    print(f"Creating output folder: {folder}")
    os.makedirs(folder)

print(f"Starting download from: {urlProvided}")
download_playlist(urlProvided, folder)

end_time = time.time()
execution_time = end_time - start_time
minutes = int(execution_time // 60)
seconds = int(execution_time % 60)
print(f"\nTotal execution time: {minutes} minutes and {seconds} seconds")