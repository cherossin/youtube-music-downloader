import yt_dlp
import sys
import os
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3, APIC, USLT, ID3NoHeaderError, TPE1, TIT2, TALB, TCON, TDRC, TRCK, COMM
from mutagen.mp4 import MP4, MP4Cover
from mutagen.asf import ASF, ASFBaseAttribute
import requests
from io import BytesIO
from PIL import Image
import re
from urllib.parse import urlparse
import argparse
import shutil

# FFmpeg이 시스템 PATH에 있는지 확인
def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        print("FFmpeg이 시스템에 설치되어 있지 않거나 PATH에 추가되지 않았습니다.")
        print("FFmpeg을 설치하고 PATH에 추가한 후 다시 시도하세요.")
        sys.exit(1)

check_ffmpeg()

def process_image(thumbnail_url):
    try:
        response = requests.get(thumbnail_url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))

        # 이미지 형식 변환 (webp는 JPEG로 변환)
        if image.format.lower() == 'webp':
            image = image.convert('RGB')
            mime_type = 'image/jpeg'
        else:
            mime_type = f'image/{image.format.lower()}'

        # 정사각형으로 크롭
        width, height = image.size
        min_dim = min(width, height)
        left = (width - min_dim) / 2
        top = (height - min_dim) / 2
        right = (width + min_dim) / 2
        bottom = (height + min_dim) / 2
        image = image.crop((left, top, right, bottom))

        # 이미지 데이터를 BytesIO에 저장
        with BytesIO() as buffer:
            image.save(buffer, format='JPEG' if mime_type == 'image/jpeg' else image.format)
            image_data = buffer.getvalue()

        return mime_type, image_data
    except Exception as e:
        print(f"썸네일 처리 중 오류 발생: {e}")
        return None, None

def set_metadata(file_path, metadata, audio_format):
    try:
        if audio_format == 'flac':
            audio = FLAC(file_path)
            # 메타데이터 설정
            for key in ['artist', 'title', 'album', 'genre', 'date', 'track_number', 'description', 'lyrics']:
                if metadata.get(key):
                    audio[key if key != 'track_number' else 'tracknumber'] = metadata[key]

            # 썸네일 삽입
            if metadata.get('thumbnail'):
                mime_type, image_data = process_image(metadata['thumbnail'])
                if image_data:
                    pic = Picture()
                    pic.type = 3  # Cover (front)
                    pic.mime = mime_type
                    pic.desc = 'Thumbnail'
                    pic.data = image_data
                    audio.clear_pictures()
                    audio.add_picture(pic)

            audio.save()
            print(f"FLAC 메타데이터가 {file_path}에 적용되었습니다.")

        elif audio_format == 'mp3':
            try:
                audio = ID3(file_path)
            except ID3NoHeaderError:
                audio = ID3()

            # 메타데이터 설정
            if metadata.get('artist'):
                audio['TPE1'] = TPE1(encoding=3, text=metadata['artist'])
            if metadata.get('title'):
                audio['TIT2'] = TIT2(encoding=3, text=metadata['title'])
            if metadata.get('album'):
                audio['TALB'] = TALB(encoding=3, text=metadata['album'])
            if metadata.get('genre'):
                audio['TCON'] = TCON(encoding=3, text=metadata['genre'])
            if metadata.get('date'):
                audio['TDRC'] = TDRC(encoding=3, text=str(metadata['date']))
            if metadata.get('track_number'):
                audio['TRCK'] = TRCK(encoding=3, text=str(metadata['track_number']))
            if metadata.get('description'):
                audio['COMM'] = COMM(encoding=3, lang='eng', desc='Description', text=metadata['description'])
            if metadata.get('lyrics'):
                audio['USLT'] = USLT(encoding=3, desc='Lyrics', text=metadata['lyrics'])

            # 썸네일 삽입
            if metadata.get('thumbnail'):
                mime_type, image_data = process_image(metadata['thumbnail'])
                if image_data:
                    audio.add(APIC(
                        encoding=3,  # 3 is for utf-8
                        mime=mime_type,
                        type=3,  # Cover (front)
                        desc='Thumbnail',
                        data=image_data
                    ))

            audio.save(file_path)
            print(f"MP3 메타데이터가 {file_path}에 적용되었습니다.")

        elif audio_format in ['aac', 'm4a']:
            audio = MP4(file_path)
            # 메타데이터 설정
            if metadata.get('artist'):
                audio.tags["\xa9ART"] = metadata['artist']
            if metadata.get('title'):
                audio.tags["\xa9nam"] = metadata['title']
            if metadata.get('album'):
                audio.tags["\xa9alb"] = metadata['album']
            if metadata.get('genre'):
                audio.tags["\xa9gen"] = metadata['genre']
            if metadata.get('date'):
                audio.tags["\xa9day"] = metadata['date']
            if metadata.get('track_number'):
                audio.tags["trkn"] = [(int(metadata['track_number']), 0)]
            if metadata.get('lyrics'):
                audio.tags["©lyr"] = metadata['lyrics']

            # 썸네일 삽입
            if metadata.get('thumbnail'):
                mime_type, image_data = process_image(metadata['thumbnail'])
                if image_data:
                    cover = MP4Cover(image_data, imageformat=MP4Cover.FORMAT_JPEG if mime_type == 'image/jpeg' else MP4Cover.FORMAT_PNG)
                    audio.tags["covr"] = [cover]

            audio.save()
            print(f"AAC/M4A 메타데이터가 {file_path}에 적용되었습니다.")

        elif audio_format == 'wav':
            # WAV는 메타데이터 지원이 제한적입니다.
            # mutagen의 asf 모듈을 사용하여 WAV 파일의 경우 일부 메타데이터를 설정할 수 있습니다.
            # 하지만 WAV는 주로 무손실 압축을 위해 사용되며, 메타데이터 지원이 제한적입니다.
            audio = ASF(file_path)
            # 메타데이터 설정 (ASF는 WAV와 호환되지 않을 수 있으므로 주의 필요)
            # 여기서는 예시로 일부 메타데이터만 설정합니다.
            if metadata.get('artist'):
                audio['Author'] = ASFBaseAttribute('Author', metadata['artist'])
            if metadata.get('title'):
                audio['Title'] = ASFBaseAttribute('Title', metadata['title'])
            # WAV 파일은 썸네일 삽입이 일반적이지 않으며, 지원되지 않을 수 있습니다.
            audio.save()
            print(f"WAV 메타데이터가 {file_path}에 적용되었습니다.")

        else:
            print(f"{audio_format.upper()} 포맷에 대한 메타데이터 설정이 구현되지 않았습니다.")
            return

    except Exception as e:
        print(f"{audio_format.upper()} 메타데이터 설정 중 오류 발생: {e}")

def download_subtitles_or_lyrics(ydl, video_info, output_dir, is_youtube_music):
    preferred_langs = ['ko', 'ja', 'en']

    if is_youtube_music:
        # YouTube Music에서 가사 추출
        lyrics = video_info.get('lyrics') or video_info.get('description', '')
        if lyrics:
            print("가사를 추출했습니다.")
            return lyrics
        else:
            print("YouTube Music에서 가사를 찾을 수 없습니다.")
            return None
    else:
        # YouTube에서 자막을 가사로 사용
        subtitles = video_info.get('subtitles') or video_info.get('automatic_captions')
        if subtitles:
            selected_lang = next((lang for lang in preferred_langs if lang in subtitles), None)

            if selected_lang:
                ydl_opts_sub = {
                    'writesubtitles': True,
                    'subtitleslangs': [selected_lang],
                    'writeautomaticsub': True,
                    'skip_download': True,
                    'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                }
                with yt_dlp.YoutubeDL(ydl_opts_sub) as ydl_sub:
                    try:
                        ydl_sub.download([video_info['webpage_url']])
                        # 자막 파일 경로 설정
                        subtitle_file_vtt = os.path.join(output_dir, f"{video_info['title']}.{selected_lang}.vtt")
                        subtitle_file_srt = os.path.join(output_dir, f"{video_info['title']}.{selected_lang}.srt")
                        subtitle_file = None
                        if os.path.exists(subtitle_file_vtt):
                            subtitle_file = subtitle_file_vtt
                        elif os.path.exists(subtitle_file_srt):
                            subtitle_file = subtitle_file_srt

                        if subtitle_file:
                            with open(subtitle_file, 'r', encoding='utf-8') as f:
                                subtitle_content = f.read()
                            # 자막 파일을 가사로 변환 (단순 텍스트 추출)
                            if subtitle_file.endswith('.vtt'):
                                lyrics = re.sub(r'WEBVTT.*\n', '', subtitle_content, flags=re.MULTILINE)  # 헤더 제거
                                lyrics = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}', '', lyrics)  # 타임코드 제거
                            elif subtitle_file.endswith('.srt'):
                                lyrics = re.sub(r'\d+\n', '', subtitle_content, flags=re.MULTILINE)  # 숫자 라인 제거
                                lyrics = re.sub(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}', '', lyrics)  # 타임코드 제거
                            lyrics = lyrics.strip()
                            print(f"자막({selected_lang})을 가사로 사용합니다.")

                            # 자막 파일 삭제
                            os.remove(subtitle_file)
                            print(f"자막 파일을 삭제했습니다: {subtitle_file}")

                            return lyrics
                        else:
                            print("자막 파일을 찾을 수 없습니다.")
                            return None
                    except yt_dlp.utils.DownloadError as e:
                        print(f"자막 다운로드 중 오류 발생: {e}")
                        return None
            else:
                print("선호하는 언어의 자막이 없습니다.")
                return None
        else:
            print("자막을 찾을 수 없습니다.")
            return None

def save_lyrics_lrc(file_path, lyrics):
    try:
        # .lrc 파일 경로 설정
        base, _ = os.path.splitext(file_path)
        lrc_path = f"{base}.lrc"

        # 간단하게 전체 가사를 첫 줄에 타임코드 없이 저장
        with open(lrc_path, 'w', encoding='utf-8') as f:
            f.write(lyrics)

        print(f".lrc 파일이 생성되었습니다: {lrc_path}")
    except Exception as e:
        print(f".lrc 파일 생성 중 오류 발생: {e}")

def download_audio(url, output_dir, audio_format='flac', create_lrc=False, ffmpeg_location=None):
    """
    주어진 YouTube 또는 YouTube Music URL에서 고음질 오디오를 다운로드합니다.

    :param url: 다운로드할 YouTube 또는 YouTube Music 링크
    :param output_dir: 오디오 파일을 저장할 디렉토리
    :param audio_format: 원하는 오디오 형식 (예: 'mp3', 'aac', 'flac', 'wav')
    :param create_lrc: .lrc 파일을 생성할지 여부 (기본: False)
    :param ffmpeg_location: FFmpeg 실행 파일의 절대 경로 (선택 사항)
    """
    supported_formats = ['mp3', 'aac', 'flac', 'wav', 'm4a']
    if audio_format not in supported_formats:
        print(f"지원되지 않는 오디오 형식입니다: {audio_format}")
        print(f"지원되는 형식: {', '.join(supported_formats)}")
        sys.exit(1)

    # 출력 디렉토리가 없으면 생성
    os.makedirs(output_dir, exist_ok=True)
    print(f"다운로드 디렉토리: {output_dir}")

    # 원본 URL이 YouTube Music인지 확인
    parsed_url = urlparse(url)
    is_youtube_music = 'music.youtube.com' in parsed_url.netloc.lower()
    print(f"Is YouTube Music: {is_youtube_music}")

    # preferredquality 설정
    preferred_quality = {
        'mp3': '320',
        'aac': '256',
        'flac': '0',
        'wav': '0',
        'm4a': '256'
    }.get(audio_format, 'best')

    # yt-dlp의 progress_hook을 사용하여 다운로드 완료 확인
    downloaded_file_path = None

    def download_hook(d):
        nonlocal downloaded_file_path
        if d['status'] == 'finished':
            print("다운로드 및 변환이 완료되었습니다.")

    # yt-dlp 옵션 설정
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),  # 원본 제목 사용
        'postprocessors': [
            {
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,        # 원하는 오디오 코덱
                'preferredquality': preferred_quality,  # 설정한 품질
            },
        ],
        'restrictfilenames': False,  # 원본 제목 유지 (비ASCII 문자와 공백 허용)
        'noplaylist': True,
        'quiet': False,
        'no_warnings': True,
        'addmetadata': True,    # 메타데이터 추가
        'prefer_ffmpeg': True,  # FFmpeg을 선호
        'progress_hooks': [download_hook],  # 다운로드 후 hook 호출
    }

    if ffmpeg_location:
        ydl_opts['ffmpeg_location'] = ffmpeg_location

    if create_lrc:
        ydl_opts['writesubtitles'] = True
        ydl_opts['writeautomaticsub'] = True

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            print(f"다운로드 중: {url}")
            video_info = ydl.extract_info(url, download=True)
            print("다운로드가 완료되었습니다.")

            # 최종 오디오 파일 경로 추출
            # 'requested_downloads' 키를 사용하여 최종 파일 경로를 추출
            final_file_path = None
            if 'requested_downloads' in video_info and len(video_info['requested_downloads']) > 0:
                for download in video_info['requested_downloads']:
                    if download.get('ext') == audio_format:
                        final_file_path = download.get('filepath')
                        break

            # 'filepath' 또는 'path' 키를 사용하여 다운로드된 파일 경로 가져오기
            if not final_file_path:
                final_file_path = video_info.get('filepath') or video_info.get('path')

            if not final_file_path:
                # 'filepath' 또는 'path' 키가 없으면, 수동으로 추측
                title = video_info.get('title', 'Unknown_Title')
                final_file_path = os.path.join(output_dir, f"{title}.{audio_format}")

            # 다운로드된 파일이 존재하는지 확인
            if not os.path.exists(final_file_path):
                print(f"파일을 찾을 수 없습니다: {final_file_path}")
                sys.exit(1)

            print(f"파일이 다운로드 및 변환되었습니다: {final_file_path}")
            print("다운로드 디렉토리의 파일 목록:")
            for f in os.listdir(output_dir):
                print(f" - {f}")

            # 썸네일 URL 추출
            thumbnail_url = video_info.get('thumbnail')

            # 가사 추출
            lyrics = download_subtitles_or_lyrics(ydl, video_info, output_dir, is_youtube_music)

            # 파일 존재 여부 확인 후 메타데이터 설정
            if os.path.exists(final_file_path):
                metadata = {
                    'artist': video_info.get('artist') or video_info.get('uploader', 'Unknown Artist'),
                    'title': video_info.get('title', 'Unknown Title'),
                    'album': video_info.get('album') or video_info.get('playlist_title', 'Unknown Album'),
                    'genre': video_info.get('genre', 'Unknown Genre'),
                    'date': video_info.get('release_date') or video_info.get('upload_date') or '',
                    'track_number': video_info.get('track_number', ''),
                    'description': video_info.get('description', ''),
                    'thumbnail': thumbnail_url,
                    'lyrics': lyrics if lyrics else ''
                }

                set_metadata(final_file_path, metadata, audio_format)

                # .lrc 파일 생성 (옵션)
                if create_lrc and lyrics:
                    save_lyrics_lrc(final_file_path, lyrics)

            else:
                print(f"파일을 찾을 수 없습니다: {final_file_path}")

        except yt_dlp.utils.DownloadError as e:
            print(f"다운로드 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube 또는 YouTube Music에서 고음질 오디오를 다운로드합니다.")
    parser.add_argument("url", help="다운로드할 YouTube 또는 YouTube Music URL")
    parser.add_argument("-f", "--format", default="flac", choices=['mp3', 'aac', 'flac', 'wav', 'm4a'], help="원하는 오디오 형식 (기본: flac)")
    parser.add_argument("-o", "--output", default="./downloads", help="오디오 파일을 저장할 디렉토리 (기본: ./downloads)")
    parser.add_argument("--create-lrc", action='store_true', help="가사 파일(.lrc)을 생성합니다.")
    parser.add_argument("--ffmpeg-location", help="FFmpeg 실행 파일의 절대 경로를 지정합니다.")

    args = parser.parse_args()

    # 절대 경로인지 확인하고 설정
    output_dir = os.path.abspath(args.output) if not os.path.isabs(args.output) else args.output

    download_audio(
        url=args.url,
        output_dir=output_dir,
        audio_format=args.format,
        create_lrc=args.create_lrc,
        ffmpeg_location=args.ffmpeg_location
    )
