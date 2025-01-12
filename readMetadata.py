from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
def read_mp3_metadata(file_path):
    try:
        audio = MP3(file_path, ID3=EasyID3)
        for key, value in audio.items():
            print(f"{key}: {value}")
        return audio
    except Exception as e:
        print(f"Error reading metadata: {e}")
        return None
mp3_file = "/Users/marco/Desktop/Hugh Guefner.mp3"
metadata = read_mp3_metadata(mp3_file)