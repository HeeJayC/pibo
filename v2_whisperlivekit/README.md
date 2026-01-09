# v2_whisperlivekit - WhisperLiveKit 로컬 연결

갤럭시북과 파이보를 같은 WiFi로 연결하여 실시간 음성 인식

## 특징

- WhisperLiveKit 기반 실시간 STT
- 화자 구분 (Sortformer)
- 같은 WiFi/핫스팟 연결 필요
- gTTS 음성 합성
- GPU 없이도 동작 (CPU)

## 구성

- server.py: 갤럭시북에서 실행 (WhisperLiveKit 서버)
- client.py: 파이보에서 실행 (클라이언트)

## 설치

### 서버 (갤럭시북)

```bash
pip install -r requirements_whisperlivekit_server.txt
```

### 클라이언트 (파이보)

```bash
pip install -r requirements_whisperlivekit_client.txt
```

## 실행 방법

### 1단계: 갤럭시북에서 서버 실행

```bash
python server.py
```

서버가 시작되면 IP 주소가 표시됩니다 (예: 172.20.10.4)

### 2단계: client.py에서 서버 IP 설정

```python
SERVER_HOST = "172.20.10.4"  # 서버 IP 주소 입력
```

### 3단계: 파이보에서 클라이언트 실행

```bash
python client.py
```

## 지원 기능

- 실시간 음성 인식 (WhisperLiveKit)
- 화자 구분 (Sortformer)
- Function Calling (시간, 날씨, 뉴스, 모션 등)
- gTTS 음성 합성

## 제한사항

- 같은 WiFi/핫스팟 필요
- 원격 접속 불가
- TTS 음질이 기본 수준
