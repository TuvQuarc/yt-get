from argparse import ArgumentParser

from urllib.parse import urlparse, parse_qsl, urlunparse, urlencode
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from yt_dlp import YoutubeDL


CWD = Path.cwd()
ALD = Path(__file__).parent
UPDATE_INTERVAL_DAYS = 7
DEFAULT_SUBTITLE_LANGS = ['ru', 'en']


def update_ytdlp() -> None:
    try:
        print('Start update for embedded `yt-dlp`...')
        subprocess.run(f'uv --project {ALD} add yt-dlp --upgrade --native-tls', shell=True, check=True)
        write_last_updated_now()
    except subprocess.CalledProcessError as e:
        print(f'Error: Failed to update yt-dlp: {e}', file=sys.stderr)


def write_last_updated_now() -> None:
    luf = Path(ALD) / 'last_updated.txt'
    try:
        with open(luf, 'w') as f:
            f.write(f'{datetime.now(timezone.utc).isoformat()}')
    except OSError as e:
        print(f'Error: Failed to write last update timestamp to `{luf}`: {e}', file=sys.stderr)


def read_last_updated() -> datetime | None:
    try:
        with open(Path(ALD) / 'last_updated.txt', 'r') as f:
            last_updated = f.read()
        return datetime.fromisoformat(last_updated)
    except OSError, ValueError:
        return None


def ytdlp_need_update() -> bool:
    last_update = read_last_updated()
    if not last_update:
        return True

    days_since_update = (datetime.now(timezone.utc) - last_update).days
    
    return days_since_update > UPDATE_INTERVAL_DAYS


def parse_arguments() -> ArgumentParser:
    parser = ArgumentParser(
        prog='yt-get',
        description='Downloader for Youtube videos, audios and playlists.'
    )

    parser.add_argument('urls', nargs='*', type=str, help='one or more URLs of the videos or playlists')
    parser.add_argument('-a', '--audio-only', action='store_true', help='only download audio')
    parser.add_argument('-c', '--cookie-file', dest='cookie_file', type=str, help='file with cookies')
    parser.add_argument('-i', '--input-file', dest='input_file', type=str, help='file with URLs of the videos or playlists')
    parser.add_argument('-u', '--update', action='store_true', help='update embedded `yt-dlp` before other tasks')
    parser.add_argument('-g', '--geo-bypass', dest='geo_code', type=str, help='geo-bypass country code (two-letter ISO 3166-2 country code)')

    args = parser.parse_args()

    if args.update:
        update_ytdlp()

    if not args.input_file and not args.urls:
        print("Error: No URLs provided. Use one or more URLs as arguments or specify an input file with -i\n", file=sys.stderr)
        parser.print_help()
        sys.exit(1)
    
    return args


def fix_url(url: str) -> str:
    url = url.strip()
    if not url:
        raise ValueError('Empty URL provided')

    parsed_url = urlparse(url, allow_fragments=False)

    scheme = parsed_url.scheme
    domain = parsed_url.netloc
    path = parsed_url.path
    params = parse_qsl(parsed_url.query)

    if domain.lower() == 'youtu.be':
        domain = 'youtube.com'
        if len(path) <= 1:
            raise ValueError(f'Incorrect URL: {url}')
        params.append(('v', path[1:]))
        path = '/watch'

    params = [item for item in params if item[0] == 'v' or item[0] == 'list']
    params_str = urlencode(params, doseq=True)

    return urlunparse((scheme, domain, path, '', params_str, ''))


def is_playlist_url(url: str) -> bool:
    if url:
        parsed_url = urlparse(url)
        return parsed_url.path == '/playlist'
    else:
        return False


def download(url: str, audio_only: bool=False, geo_bypass: str | None=None, cookie_file: str | None = None) -> None:
    default_args = {
        'ignoreerrors': 'only_download',
        'overwrites': False,
        'continuedl': True,
        'updatetime': True,
        'windowsfilenames': True,
        'compat_opts': {'no-certifi'},
        'source_address': '0.0.0.0',
    }
    if geo_bypass:
        default_args['geo_bypass_country'] = geo_bypass
    
    if cookie_file:
        default_args['cookiefile'] = cookie_file

    video_args = {
        'subtitleslangs': DEFAULT_SUBTITLE_LANGS,
        'postprocessors': [
            {
                'already_have_subtitle': False,
                'key': 'FFmpegEmbedSubtitle',
            },
            {
                'add_chapters': True,
                'add_infojson': 'if_exists',
                'add_metadata': True,
                'key': 'FFmpegMetadata',
            },
            {
                'already_have_thumbnail': False,
                'key': 'EmbedThumbnail',
            },
        ],
        'writesubtitles': True,
        'writethumbnail': True,
        'format': 'bestvideo+bestaudio[language^=ru]+bestaudio[language^=en]/bestvideo+bestaudio[language^=ru]/bestvideo+bestaudio[language^=en]/bestvideo+bestaudio/best',
        'allow_multiple_audio_streams': True,
        'merge_output_format': 'mkv',
    }

    audio_args = {
        'format': 'bestaudio/best',
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'nopostoverwrites': False,
                'preferredcodec': 'aac/best',
                'preferredquality': '0',
            },
            {
                'add_chapters': True,
                'add_infojson': 'if_exists',
                'add_metadata': True,
                'key': 'FFmpegMetadata',
            },
        ],
        'final_ext': 'aac',
    }

    playlist_filename_format = {
        'outtmpl': {'default': '%(channel)s - %(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s', 'pl_thumbnail': ''},
    }

    single_filename_format = {
        'outtmpl': {'default': '%(channel)s - %(title)s.%(ext)s', 'pl_thumbnail': ''},
    }

    is_playlist = is_playlist_url(url)

    if audio_only:
        if is_playlist:
            args = default_args | audio_args | playlist_filename_format
        else:
            args = default_args | audio_args | single_filename_format
    else:
        if is_playlist:
            args = default_args | video_args | playlist_filename_format
        else:
            args = default_args | video_args | single_filename_format

    with YoutubeDL(args) as ydl:
        ydl.download([url])


if __name__ == '__main__':
    try:
        if ytdlp_need_update():
            update_ytdlp()

        args = parse_arguments()

        urls: list[str] = list()

        if args.urls:
            for url in args.urls:
                urls.append(fix_url(url))
        
        if args.input_file:
            path = Path(args.input_file)
            input_file = path.resolve() if path.is_absolute() else (CWD / path).resolve()
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    for line_num, url in enumerate(f, 1):
                        url = url.strip()
                        if not url or url[0] in '#;':
                            continue
                        try:
                            urls.append(fix_url(url))
                        except ValueError as e:
                            print(f'Warning: Skipping invalid URL on line {line_num}: {e}', file=sys.stderr)
            except OSError as e:
                print(f'Error: Failed to read input file `{input_file}`: {e}', file=sys.stderr)
                if len(urls) == 0:
                    sys.exit(1)
                else:
                    print('Continuing with URLs from command-line arguments', file=sys.stderr)

        if args.geo_code and len(args.geo_code) != 2:
            print('Error: Geo-bypass country code must be a two-letter ISO 3166-2 code', file=sys.stderr)
            sys.exit(1)

        geo_code = None
        if args.geo_code:
            geo_code = args.geo_code.upper()
        
        cookie_file = None
        if args.cookie_file:
            path = Path(args.cookie_file)
            cookie_file = path.resolve() if path.is_absolute() else (CWD / path).resolve()

        for url in urls:
            download(url=url, audio_only=args.audio_only, geo_bypass=args.geo_code, cookie_file=cookie_file)
        
    except KeyboardInterrupt:
        print('\nDownload cancelled by user', file=sys.stderr)
        sys.exit(130)
