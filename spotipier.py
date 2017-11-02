from spotipy import Spotify, SpotifyException
import spotipy.util as util
from spotipy.oauth2 import SpotifyOAuth
from actions import *
import os
import webbrowser

PLAYLIST_NAME = os.environ.get('SPOTIFY_PLAYLIST_NAME')
PLAYLIST_ID = os.environ.get('SPOTIFY_PLAYLIST_ID')


class Spotipier(object):

    def __init__(self, username='jackland', scope='playlist-modify-private'):
        self._ACTION_FUNCTIONS = {
            ADD_TRACKS: self.add_tracks_to_playlist,
            GET_TRACK: self.get_track
        }
        self.username = username
        self.scope = scope
        self.token = util.prompt_for_user_token(self.username, self.scope)
        if self.token:
            client_id = os.getenv('SPOTIPY_CLIENT_ID')
            client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
            redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
            self.oauth = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri,
                                 scope=self.scope, cache_path=".cache-" + self.username)
            self.client = Spotify(auth=self.token)
            self.user_id = self.client.me()['id']
        else:
            raise Exception('Authorisation failed. PANIC!')

    def refresh_token(self):
        if self.oauth and self.token:
            self.token = self.oauth.refresh_access_token(self.token)

    def get_playlist_tracks(self):
        tracks = self.client.user_playlist_tracks(self.username, PLAYLIST_ID)
        return tracks

    def add_tracks_to_playlist(self, tracks):
        self.client.user_playlist_add_tracks(self.user_id, PLAYLIST_ID, tracks)

    def get_track(self, track):
        return self.client.track(track)

    def get_user_playlists(self):
        return self.client.user_playlists(self.user_id)

    def get_user(self, user_id):
        return self.client.user(user_id)

