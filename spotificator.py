from slackclient import SlackClient
from spotipier import Spotipier
import os
import time


class Spotificator(object):

    BOT_NAME = 'spotificator'
    BOT_ID = os.environ.get('SLACK_BOT_ID')

    # constants
    AT_BOT = "<@" + BOT_ID + ">"
    SPOTIFY_URL = "https://open.spotify.com/"
    SPOTIFY_TRACK_LINK = SPOTIFY_URL + "track/"
    SPOTIFY_ALBUM_LINK = SPOTIFY_URL + "album/"
    TEST_CHANNEL_ID = 'G6Z023N1Y'
    LIVE_CHANNEL_ID = 'C6NB64MV5'
    BOT_COMMANDS = ["scan"]
    READ_WEBSOCKET_DELAY = 1
    POLL_INTERVAL = 1800.0

    def __init__(self, scope='playlist-modify-private'):
        self.slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
        self.spotifpier = Spotipier(scope=scope)
        self.playlist_tracks = self.spotifpier.get_playlist_tracks()

    def main_loop(self):
        if self.slack_client.rtm_connect():
            print("Spotificator connected and running!")
            t_begin = time.time()
            polled = False
            while True:
                t_current = time.time()
                t_elapsed = t_current - t_begin
                if (t_elapsed % self.POLL_INTERVAL) <= 5*self.READ_WEBSOCKET_DELAY and not polled:
                    print('{} - Refreshing spotify token'.format(time.asctime()))
                    self.spotifpier.refresh_token()
                    polled = True
                elif polled and (t_elapsed % self.POLL_INTERVAL > (self.POLL_INTERVAL - (20*self.READ_WEBSOCKET_DELAY))):
                    polled = False
                self.check_playlist()
                command, channel, command_type = self.parse_slack_output(self.slack_client.rtm_read())
                if command:
                    self.handle_command(command, channel, command_type)
                time.sleep(self.READ_WEBSOCKET_DELAY)
        else:
            print("Connection failed. Check slack token or bot ID")

    def get_bot_id(self):
        api_call = self.slack_client.api_call("users.list")
        if api_call.get('ok'):
            print('API CALL OK')
            # Retrieve all users so we can find our bot
            users = api_call.get('members')
            for user in users:
                if 'name' in user and user.get('name') == self.BOT_NAME:
                    return user.get('id')
        else:
            print("Could not find bot user with the name " + self.BOT_NAME)
            return None

    def get_playlist_id(self):
        playlists = self.spotifpier.get_user_playlists()
        while playlists:
            for i, playlist in enumerate(playlists['items']):
                print("%4d %s %s" % (i + 1 + playlists['offset'], playlist['uri'], playlist['name']))
            if playlists['next']:
                playlists = self.spotifpier.client.next(playlists)
            else:
                playlists = None

    @staticmethod
    def parse_spotify_link(link):
        # TODO make a spotify link parsing method/class
        pass

    def handle_command(self, command, channel, command_type):
        """
            Receives commands directed at the bot and determines if they
            are valid commands. If so, then acts on the commands. If not,
            returns back what it needs for clarification.
        """
        response = "Not sure what you mean. Use the *" + self.BOT_COMMANDS[0] + \
                   "* command with numbers, delimited by spaces."
        if command_type == self.AT_BOT and command.startswith(self.BOT_COMMANDS[0]):
            context = self.scan_channel(channel)
            if 'found' in context and 'added' in context:
                response = "Scanned channel, found {a} tracks and added {b} of them to the playlist."\
                    .format(a=context['found'], b=context['added'])
            elif 'reason' in context:
                response = "Channel scan failed: " + context['reason']
        elif command_type == self.SPOTIFY_TRACK_LINK:
            print(command)
            track = self.spotifpier.get_track(command)
            self.spotifpier.add_tracks_to_playlist([command])
            response = "Added {title} by {artist} to Moosic".format(title=track['name'], artist=track['artists'][0]['name'])
        self.slack_client.api_call("chat.postMessage", channel=channel,
                                   text=response, as_user=True)

    def parse_slack_output(self, slack_rtm_output):
        """
            The Slack Real Time Messaging API is an events firehose.
            this parsing function returns None unless a message is
            directed at the Bot, based on its ID.
        """
        output_list = slack_rtm_output
        if output_list and len(output_list) > 0:
            for output in output_list:
                if output and 'text' in output:
                    if self.AT_BOT in output['text']:
                        # return text after the @ mention, whitespace removed
                        return output['text'].split(self.AT_BOT)[1].strip().lower(), \
                               output['channel'], \
                               self.AT_BOT
                    elif self.SPOTIFY_TRACK_LINK in output['text']:
                        # return spotify track link
                        return output['text'][:-1].split(self.SPOTIFY_TRACK_LINK)[1].split(' ')[0], \
                               output['channel'], \
                               self.SPOTIFY_TRACK_LINK
                    elif self.SPOTIFY_ALBUM_LINK in output['text']:
                        # return spotify album link
                        return output['text'].split(self.SPOTIFY_ALBUM_LINK)[1].split(' ')[0], \
                               output['channel'], \
                               self.SPOTIFY_ALBUM_LINK
        return None, None, None

    def check_playlist(self):
        new_pl_tracks = self.spotifpier.get_playlist_tracks()
        message = ''
        # print('Checking playlist for manually added tracks.')
        old_track_ids = self._get_playlist_set()
        for pl_track in new_pl_tracks['items']:
            new_track_id = pl_track['track']['id']
            if new_track_id not in old_track_ids:
                print('...Found new track')
                user = self.spotifpier.get_user(pl_track['added_by']['id'])
                message += "NEW TRACK: {user} added {title} by {artist} to Moosic \n".format(
                    user=user['display_name'],
                    title=pl_track['track']['name'],
                    artist=pl_track['track']['artists'][0]['name'])
        if message != '':
            self.slack_client.api_call("chat.postMessage", channel=self.LIVE_CHANNEL_ID, text=message, as_user=True)
        self.playlist_tracks = new_pl_tracks

    def _get_playlist_set(self):
        track_set = set()
        for pl_track in self.playlist_tracks['items']:
            track_id = pl_track['track']['id']
            track_set.add(track_id)
        return track_set


    def scan_channel(self, channel):
        """
        Function called by the 'scan' command, which searches through the channel called from
        and adds all spotify track links, which aren't in the playlist already, to the playlist.
        Intended for use if bot is down temporarily or not always up.
        """
        print(channel)
        # api_call = self.slack_client.api_call('channels.history', count=1000, channel=channel)
        # if api_call.get('ok'):
        #     print('API CALL OK')
        #     # Retrieve all users so we can find our bot
        #     channel_history = api_call.get('messages')
        #     n = 0
        #     for message in channel_history:
        #         if self.SPOTIFY_TRACK_LINK in message['text']:
        #             print(message['text'])
        #             n += 1
        #     return {'found': len(channel_history), 'added': n}
        # else:
        #     print("API CALL FAILED")
        #     return {'reason': api_call.get('error')}
        return {'reason': 'Jack\'s not implemented this yet'}


if __name__ == '__main__':
    spotify_client = Spotificator()
    spotify_client.main_loop()
    # spotify_client.get_playlist_id()

