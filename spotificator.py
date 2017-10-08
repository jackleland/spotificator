from slackclient import SlackClient
from spotifywrapper import SpotifyWrapper
import os
import time


class Spotificator(object):

    BOT_NAME = 'spotificator'
    BOT_ID = os.environ.get('SLACK_BOT_ID')

    # constants
    AT_BOT = "<@" + BOT_ID + ">"
    SPOTIFY_LINK = "https://open.spotify.com/track/"
    SPOTIFY_ALBUM_LINK = "https://open.spotify.com/album/"
    EXAMPLE_COMMAND = "scan"
    READ_WEBSOCKET_DELAY = 1

    def __init__(self, scope='playlist-modify-private'):
        self.slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
        self.spotify_wrapper = SpotifyWrapper(scope=scope)

    def main_loop(self):
        if self.slack_client.rtm_connect():
            print("Spotificator connected and running!")
            while True:
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
        playlists = self.spotify_wrapper.get_user_playlists()
        # for playlist in playlists['items']:
        #     print(playlist['name'] + " - " + playlist['id'])
        while playlists:
            for i, playlist in enumerate(playlists['items']):
                print("%4d %s %s" % (i + 1 + playlists['offset'], playlist['uri'], playlist['name']))
            if playlists['next']:
                playlists = self.spotify_wrapper.client.next(playlists)
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
        response = "Not sure what you mean. Use the *" + self.EXAMPLE_COMMAND + \
                   "* command with numbers, delimited by spaces."
        if command_type == self.AT_BOT and command.startswith(self.EXAMPLE_COMMAND):
            response = "Sure...when you've written the fucking bot you lazy bastard. command = {}".format(command)
        elif command_type == self.SPOTIFY_LINK:
            print(command)
            track = self.spotify_wrapper.get_track(command)
            self.spotify_wrapper.add_tracks_to_playlist([command])
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
                    elif self.SPOTIFY_LINK in output['text']:
                        # return spotify link
                        return output['text'][:-1].split(self.SPOTIFY_LINK)[1].split(' ')[0], \
                               output['channel'], \
                               self.SPOTIFY_LINK
                    elif self.SPOTIFY_ALBUM_LINK in output['text']:
                        # return spotify album link
                        return output['text'].split(self.SPOTIFY_ALBUM_LINK)[1].split(' ')[0], \
                               output['channel'], \
                               self.SPOTIFY_ALBUM_LINK
        return None, None, None


if __name__ == '__main__':
    spotify_client = Spotificator()
    spotify_client.main_loop()
    # spotify_client.get_playlist_id()



