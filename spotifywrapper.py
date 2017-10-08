from spotipy import Spotify
import spotipy.util as util
from actions import *
import os

PLAYLIST_NAME = os.environ.get('SPOTIFY_PLAYLIST_NAME')
PLAYLIST_ID = os.environ.get('SPOTIFY_PLAYLIST_ID')


class SpotifyWrapper(object):

    def __init__(self, username='jackland', scope='playlist-modify-private'):
        self._ACTION_FUNCTIONS = {
            ADD_TRACKS: self.add_tracks_to_playlist,
            GET_TRACK: self.get_track
        }
        self.username = username
        self.scope = scope

        token = util.prompt_for_user_token(self.username, self.scope)
        if token:
            self.client = Spotify(auth=token)
            self.user_id = self.client.me()['id']
        else:
            raise Exception('Authorisation failed. PANIC!')

    def add_tracks_to_playlist(self, tracks):
        self.client.user_playlist_add_tracks(self.user_id, PLAYLIST_ID, tracks)

    def get_track(self, track):
        return self.client.track(track)

    def get_user_playlists(self):
        return self.client.user_playlists(self.user_id)
