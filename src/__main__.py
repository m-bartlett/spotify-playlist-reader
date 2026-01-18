#!/usr/bin/env python3
import argparse
import json

from . import __version__
from .spotify_playlist_reader import SpotifyPlaylistReader, SpotifyTrack


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument('playlists',
                        nargs='+',
                        help="playlists to download.")

    parser.add_argument('--format', '-f',
                        type=str,
                        help=f"""
                            String template whose template arguments should correspond to track
                            attributes, which are:
                            {', '.join(SpotifyTrack.__dataclass_fields__.keys())}
                        """)

    parser.add_argument('--verbose', action="store_true")
    parser.add_argument('--versions', action="version", version=__version__)

    args = parser.parse_args()

    spotpldl = SpotifyPlaylistReader(verbose=args.verbose)

    playlists_info = {
        # [track.__dict__ for track in spotpldl.get_tracks_from_playlist(playlist)]
        playlist_id: playlist_tracks
        for playlist in args.playlists
        for playlist_id, playlist_tracks in spotpldl.get_tracks_from_playlist(playlist).items()
    }

    if args.format:
        for playlist, playlist_tracks in playlists_info.items():
            for track in playlist_tracks:
                _track = track.__dict__
                _track['artists'] = ' & '.join(track.artists)
                print(args.format.format_map(_track))
    else:
        print(json.dumps(playlists_info, indent=4))


if __name__ == '__main__':
    main()