# YouTube 오디오 다운로더

YouTube 또는 YouTube Music에서 고음질 오디오를 다운로드하고, 자동으로 메타데이터와 썸네일을 설정하는 Python 스크립트입니다. 다양한 오디오 형식을 지원하며, 가사 파일(.lrc)도 생성할 수 있습니다.

## 주요 기능

- **다양한 오디오 형식 지원**: FLAC, MP3, AAC, WAV, M4A
- **자동 메타데이터 설정**: 아티스트, 제목, 앨범, 장르, 발매일, 트랙 번호 등
- **썸네일 이미지 삽입**: 다운로드한 오디오 파일에 썸네일을 포함
- **가사 추출 및 .lrc 파일 생성**: 동영상의 자막을 가사로 변환하여 .lrc 파일로 저장
- **FFmpeg을 사용한 고효율 오디오 변환**
- **다중 언어 자막 지원**: 한국어, 일본어, 영어 자막 지원

## 설치 방법

### 요구사항

- **Python**: 버전 3.7 이상
- **FFmpeg**: 시스템에 설치되어 있어야 하며, PATH에 추가되어 있어야 합니다.

### FFmpeg 설치

FFmpeg은 [공식 웹사이트](https://ffmpeg.org/download.html)에서 다운로드할 수 있습니다. 설치 후, FFmpeg 실행 파일의 경로를 시스템 PATH에 추가하세요.

### Python 패키지 설치

```bash
pip install -r requirements.txt
```

## 사용법

스크립트를 사용하려면, 터미널에서 다음과 같이 실행하세요:

```bash
python downloader.py "다운로드할 YouTube URL" -f [형식(선택, 기본 flac)] -o [출력 디렉토리(선택, 기본 ./downloads)] [옵션(선택)]
```

### 인자 설명

- `url`: 다운로드할 YouTube URL (필수)
- `-f`, `--format`: 원하는 오디오 형식 (기본: `flac`). 지원되는 형식: `mp3`, `aac`, `flac`, `wav`, `m4a`
- `-o`, `--output`: 오디오 파일을 저장할 디렉토리 (기본: `./downloads`)
- `--create-lrc`: 가사 파일(.lrc)을 생성합니다. (기본: 비활성화)
- `--ffmpeg-location`: FFmpeg 실행 파일의 절대 경로를 지정합니다. (기본: PATH 경로)

### 예시

#### 기본 사용 (FLAC 형식)

```bash
python downloader.py "https://music.youtube.com/watch?v=example"
```

#### MP3 형식으로 다운로드

```bash
python downloader.py "https://www.youtube.com/watch?v=example" -f mp3
```

#### AAC 형식으로 다운로드 + 다운로드 경로 지정

```bash
python downloader.py "https://www.youtube.com/watch?v=example" -f aac -o "./downloads"
```

#### WAV 형식으로 다운로드 + 다운로드 경로 지정 + 가사 파일 생성

```bash
python downloader.py "https://www.youtube.com/watch?v=example" -f wav -o "./downloads" --create-lrc
```

#### FFmpeg 위치 지정

FFmpeg이 시스템 PATH에 포함되지 않은 경우, `--ffmpeg-location` 옵션을 사용하여 FFmpeg의 경로를 지정할 수 있습니다.

```bash
python downloader.py "https://www.youtube.com/watch?v=example" -f mp3 -o "./downloads" --ffmpeg-location "/usr/local/bin/ffmpeg"
```

## 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE)를 따릅니다.

## 문제 해결 및 문의

문제가 발생하거나 기능 추가를 원하시면 [이슈](https://github.com/사용자명/리포지토리명/issues)를 열어주시거나, 풀 리퀘스트를 제출해주세요.

---

감사합니다! 😊
