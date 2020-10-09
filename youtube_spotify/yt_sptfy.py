import json
import requests
import os

from user_info import spotify_user_id, spotify_token
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl

class CreatePlaylist:

    def __init__(self):
        self.all_song_info = self.all_song_info
        self.user_id = spotify_user_id
        self.spotify_token = spotify_token
        self.youtube_client = self.get_youtube_client()

    # Step 1: Log into Youtube
    def get_youtube_client(self):
        # copied from Youtube Data API
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "YOUR_CLIENT_SECRET_FILE.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    #Step 2: Get our liked videos and Creating a dictionary of all important song information
    def get_liked_videos(self):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            myRating="like"
        )
        response = request.execute()

        #collect each video and get important information
        for item in response["items"]:
            video_title = item["snippet"]["title"]
            youtube_url = "https://www.youtube.com/watch?{}".format(item["id"])

            #using youtube_dl from github to extract song name and artist
            video = youtube_dl.YoutubeDL({}).extract_info(youtube_url, download=False)
            song_name = video["track"]
            artist = video["artist"]

            #save all important information
            self.all_song_info[video_title] ={
            "youtube_url":youtube_url,
            "song_name":song_name,
            "artist":artist,

            #getting spotify uri to easily add to playlist
            "spotify_uri":self.get_spotify_song(song_name,artist)
            }

    #Step 3: Create a new playlist
    def create_playlist(self):
        #JSON (Java Script Object Notation) writes code in js so browser can parse it easier (most likely a dict)
        #json.dumps ensures that the objects are in string format

        #request body is the name and description the playlist, as well as the status of the playlist
        #this is taken from Spotify Web API documentation
        request_body = json.dumps({
            "name": "Youtube Liked Songs",
            "description": "Liked songs from Youtube",
            "public": True
        })

        #The endpoint uses the endpoint url from spotify account to generate url
        endpoint = f'https://api.spotify.com/v1/users/{self.user_id}/playlists'
        #request.post is a HTTPS method that allows for code to create and update data on servers
        response = requests.post(
            endpoint,
            data = request_body,
            headers={
                "Content-Type":"applications/json",
                "Authorization":f'Bearer {self.sporify_token}'
            }
        )

        response.json= response.json()

        #this is the id for the playlist that was created
        return response.json["id"]

    #Step 4: Search for song on Spotify
    def get_spotify_song(self, song_name, artist):

        endpoint = "https://api.spotify.com/v1/search?q=track%3A{}%20artist%3A{}&type=album".format(
            song_name,
            artist
        )

        response = requests.post(
            endpoint,
            headers = {
            "Content-Type": "applications/json",
            "Authorization": f'Bearer {self.sporify_token}'
        }
        )

        response.json = response.json()
        songs = response.json["tracks"]["items"]

        uri = songs[0]["uri"]

        return uri
   #Step 5: Add song to playlist
    def add_song_to_playlist(self):
        # populate our dictionary with songs
        self.get_liked_videos()
        
        # collect all uri
        uris = []
        for song,info in self.all_song_info.items():
            uris.append(info["spotify_uri"])

        # create new playlist
        playlist_id = self.create_playlist()
        # add song to playlist
        request_data = json.dumps(uris)

        query = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"

        response = requests.post(
            query,
            headers={
                "Content-Type": "applications/json",
                "Authorization": f'Bearer {self.spotify_token}'
            }
        )

        response_json = response.json()
        return response_json