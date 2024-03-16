import json
import os
from pytube import YouTube
from pytube import Playlist


def get_user_input():
    with open("config.json") as f:
        data = json.load(f)
        folder = data["folder"]
        url = data["url"]

    # interact with the user if the folder and url are correct
    if os.path.exists(folder):
        print("The folder in which you will find your .mp3 files is: " + folder)
        print("Is this correct? (yes/no)")
        response = input()
    if not os.path.exists(folder) or response == "no":
        folder = input("Enter the folder path where you want to save the .mp3 files: ")
        folder = os.path.expanduser(folder)
        while not os.path.exists(folder):
            print("The folder does not exist. Please provide a valid folder.")
            folder = input(
                "Enter the folder path where you want to save the .mp3 files: "
            )
            folder = os.path.expanduser(folder)
        data["folder"] = folder
        with open("config.json", "w") as f:
            json.dump(data, f)

    # provide url
    print("The url of the video/playlist is: " + url)
    print("Is this correct? (yes/no)")
    response = input()
    while response == "no":
        print("insert the url of the video or playlist")
        url = input()
        # is the url valid?
        try:
            if "playlist" in url:
                Playlist(url)
            else:
                # single video
                YouTube(url)

            data["url"] = url
            with open("config.json", "w") as f:
                json.dump(data, f)
            print("The url has been updated to: " + url)
            response = "yes"
        except Exception as e:
            print("The url is not valid. please provide a valid url")
            response = "no"
    return folder, url
