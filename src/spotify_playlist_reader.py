import base64
import dataclasses
import http.client
import json
import re
import sys


@dataclasses.dataclass
class SpotifyTrack(dict):
    id: str
    name: str
    artists: list[str]
    duration: float
    album: str

    def __post_init__(self):
           self.update(self.__dict__)



class SpotifyPlaylistReader:

    _playlist_base64_payload_regex = re.compile(r'id=\"initialState\"[^>]*?>([^<]+)</')
    _session_token_regex = re.compile(r'<script [^>]*?id=\"session\"[^>]*?>(.*?)</script>')
    _url_regex = re.compile(r'^(?:(?P<scheme>https?)://)?'
                            r'(?P<host>[^/]+)'
                            r'(?P<path>[^\?&]*?)'
                            r'(\?(?P<query>[^\?&]*?))?$')

    def __init__(self, verbose: bool=False) -> None:
        self.verbose = verbose


    def request(self,
                url: str,
                method: str="GET",
                headers: dict={},
                body: str|None=None) -> http.client.HTTPResponse:

        if not (req := self._url_regex.match(url)):
            raise http.client.InvalidURL
        connector = getattr(http.client,
                            f"{req['scheme'].upper()}Connection",
                            http.client.HTTPSConnection)
        conn = connector(req['host'])
        conn.request(method, req['path'], headers=headers, body=body)
        response = conn.getresponse()
        if self.verbose:
            self.printerr(f"Request = {json.dumps(req.groupdict(), indent=4)}")
            self.printerr(f"Response = {response.status} {response.reason}")
        return response


    @staticmethod
    def printerr(msg: str) -> None:
        sys.stderr.write(msg)
        sys.stderr.write('\n')
        sys.stderr.flush()


    @staticmethod
    def _get_playlist_id(playlist_url: str) -> str:
        _, _, playlist_id = playlist_url.rpartition('playlist/')
        return playlist_id


    def get_playlist_data(self, playlist_id: str) -> dict:
        playlist_url = f"https://open.spotify.com/playlist/{playlist_id}"
        response = self.request(playlist_url)
        response_body = response.read().decode()
        playlist_base64_payload = self._playlist_base64_payload_regex.search(response_body)
        if playlist_base64_payload:
            base64_payload = playlist_base64_payload.group(1)
            decoded_payload = base64.urlsafe_b64decode(base64_payload)
            playlist_data = json.loads(decoded_payload)
            playlist_data['id'] = playlist_id
            if self.verbose:
                self.printerr(f"Playlist data = {json.dumps(playlist_data, indent=4)}")
            return playlist_data
        else:
            raise RuntimeError(f"Playlist ID {playlist_id} did not return a valid payload.")


    def extract_playlist_tracks(self, playlist_data: dict) -> dict[str, list[SpotifyTrack]]:
        playlist_items = (playlist_data
                           ['entities']
                           ['items']
                           [f"spotify:playlist:{playlist_data['id']}"]
                           ['content']
                           ['items'])
        playlist_tracks = []
        for item in playlist_items:
            item_data = item['itemV2']['data']
            track = SpotifyTrack(
                id = item_data['uri'].rpartition(':')[2],
                name = item_data['name'],
                artists = [artist['profile']['name'] for artist in item_data['artists']['items']],
                duration = item_data['duration']['totalMilliseconds'] / 1000.0,
                album = item_data['albumOfTrack']['name']
            )
            playlist_tracks.append(track)
        if self.verbose:
            self.printerr(f"Playlist {playlist_data['id']} tracks = "
                          f"{json.dumps(playlist_tracks, indent=4)}")
        return {playlist_data['id']: playlist_tracks}


    def get_tracks_from_playlist(self, playlist: str) -> dict[str, list[SpotifyTrack]]:
        playlist_id = self._get_playlist_id(playlist)
        playlist_data = self.get_playlist_data(playlist_id)
        playlist_tracks = self.extract_playlist_tracks(playlist_data)
        return playlist_tracks