#!/usr/bin/env python3
import argparse

from .spotify_playlist_reader import SpotifyPlaylistReader


def main() -> None:

    parser = argparse.ArgumentParser()

    parser.add_argument('playlists',
                        nargs='+',
                        help="playlists to download.")

    parser.add_argument('--output', '-o', default='.', help="Path to output downloaded files")

    parser.add_argument('--search', '-s',
                        metavar='SEARCHPREFIX',
                        nargs='+',
                        default=['ytsearch1'],
                        help="""yt-dlp search prefixes to try to source tracks from. Stops searching
                                on the first match. More info:
                                https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md""")

    parser.add_argument('--receipt',
                        metavar="/path/to/receipt.json",
                        help="Output data of the songs that were downloaded to the given path.")

    parser.add_argument('--verbose', action="store_true")

    args = parser.parse_args()

    spotpldl = SpotifyPlaylistReader(verbose=args.verbose)
    for playlist in args.playlists:
        playlist_tracks = spotpldl.get_tracks_from_playlist(playlist)
        spotpldl.download_tracks(playlist_tracks,
                                 output_dir=args.output,
                                 search_prefixes=args.search)


if __name__ == '__main__':
    main()