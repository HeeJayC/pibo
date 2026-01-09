# 파이보 음성 대화 시스템 - ngrok 연결 방식

데스크톱(NVIDIA GPU)과 갤럭시북/파이보를 ngrok을 통해 연결하는 방법

## 구성

- 데스크톱: `desktop_server_with_tts.py` (서버 - GPU 활용, STT + TTS 통합)
- 갤럭시북/파이보: `galaxybook_client_whisperlivekit.py` (클라이언트)

## 설치

### 데스크톱 (서버)

```bash
pip install whisperlivekit fastapi uvicorn[standard] websockets python-multipart nemo_toolkit[asr] numpy scipy soundfile torch torchaudio transformers onnxruntime
```

### 갤럭시북/파이보 (클라이언트)

```bash
pip install websocket-client pyaudio gtts requests beautifulsoup4 openpibo
```

### ngrok 설치

https://ngrok.com/download 에서 다운로드 및 설치

## 실행 방법

### 1단계: 데스크톱에서 서버 실행

```bash
cd "C:\Users\User\UST 인턴\1월 9일"
python desktop_server_with_tts.py
```

### 2단계: ngrok으로 외부 접속 가능하게 만들기

새 터미널을 열고:

```bash
ngrok http 9090
```

나오는 화면에서 Forwarding URL 복사:
```
Forwarding  https://abc123def456.ngrok.io -> http://localhost:9090
```

여기서 `abc123def456.ngrok.io` 부분을 복사하세요 (https:// 제외)

### 3단계: 클라이언트 코드 수정

`galaxybook_client_whisperlivekit.py` 파일 열고:

```python
SERVER_HOST = "abc123def456.ngrok.io"  # 복사한 ngrok URL 입력
```

### 4단계: 갤럭시북/파이보에서 클라이언트 실행

```bash
python galaxybook_client_whisperlivekit.py
```

## 동작 방식

```
[데스크톱 GPU]
     ↓
[WhisperLiveKit STT + Supertonic2 TTS 서버]
     ↓
[ngrok 터널]
     ↓
[인터넷]
     ↓
[갤럭시북/파이보 클라이언트]
```

### 음성 처리 흐름

1. STT (음성 → 텍스트)
   - 클라이언트가 마이크 입력 → WebSocket으로 서버 전송
   - 서버가 WhisperLiveKit으로 실시간 변환 (GPU 가속)
   - 화자 구분된 텍스트를 클라이언트로 전송

2. AI 응답 생성
   - 클라이언트가 Function Calling으로 응답 생성
   - 시간, 날씨, 뉴스, 모션 등 처리

3. TTS (텍스트 → 음성)
   - 클라이언트가 응답 텍스트를 서버 /tts API로 전송
   - 서버가 Supertonic2로 고품질 한국어 음성 생성
   - WAV 파일을 클라이언트로 반환하여 재생
   - 실패 시 gTTS로 자동 폴백

## 주의사항

- ngrok 무료 버전은 세션 시간 제한이 있습니다 (8시간)
- 인터넷 연결 필요
- ngrok URL은 매번 바뀌므로, 재시작할 때마다 클라이언트 코드 수정 필요

## 지원 기능

- 실시간 음성 인식 (WhisperLiveKit)
- 화자 구분 (Sortformer)
- 데스크톱 GPU 활용
- Function Calling (시간, 날씨, 뉴스, 모션 등)
- 고품질 한국어 TTS (Supertonic2 + gTTS 폴백)

## 문제 해결

### ngrok 연결 실패
- ngrok이 실행 중인지 확인
- URL을 정확히 복사했는지 확인
- https:// 부분은 제외하고 입력

### 서버 연결 실패
- 데스크톱에서 서버가 실행 중인지 확인
- 방화벽 설정 확인

### GPU 인식 안 됨
- NVIDIA 드라이버 설치 확인
- CUDA 설치 확인

### TTS 음성이 나오지 않음
- 서버 로그에서 "Supertonic2 TTS 사용 가능" 메시지 확인
- TTS 폴더 구조 확인: TTS/supertonic2/onnx/ 및 voice_styles/ 존재 여부
- 자동 폴백: Supertonic2 실패 시 gTTS 사용
