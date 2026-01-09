# 파이보 음성 대화 시스템

파이보 로봇을 위한 음성 인식 및 대화 시스템

## 프로젝트 구조

```
pibo/
├── v1_basic/              기본 파이보 시스템 (gTTS)
├── v2_whisperlivekit/     WhisperLiveKit 로컬 연결
├── v3_ngrok_integrated/   ngrok + GPU + 고품질 TTS (최신, 권장)
└── docs/                  문서
```

## 버전 비교

| 항목 | v1_basic | v2_whisperlivekit | v3_ngrok_integrated |
|------|----------|-------------------|---------------------|
| STT | 없음 | WhisperLiveKit | WhisperLiveKit (GPU) |
| TTS | gTTS | gTTS | Supertonic2 + gTTS |
| 화자 인식 | 없음 | 있음 | 있음 |
| 원격 접속 | 없음 | 같은 WiFi만 | ngrok으로 가능 |
| GPU 필요 | 없음 | 없음 | 권장 |
| 설치 난이도 | 쉬움 | 보통 | 어려움 |
| 음질 | 보통 | 보통 | 우수 |
| 적합한 상황 | 테스트 | 같은 장소 | 실제 운영 |

## 버전 선택 가이드

### v1_basic
- 가장 간단한 버전
- 음성 인식 없이 텍스트 입력만 필요할 때
- 빠른 테스트 및 프로토타입

### v2_whisperlivekit
- 갤럭시북과 파이보가 같은 장소에 있을 때
- 같은 WiFi/핫스팟 연결 가능할 때
- GPU 없이 CPU로 실행

### v3_ngrok_integrated (권장)
- 데스크톱과 갤럭시북/파이보가 다른 장소에 있을 때
- NVIDIA GPU 활용 가능할 때
- 최고 품질의 음성 인식 및 합성 필요할 때
- 실제 운영 환경

## 빠른 시작

각 버전 폴더의 README.md를 참고하세요:

- [v1_basic/README.md](v1_basic/README.md)
- [v2_whisperlivekit/README.md](v2_whisperlivekit/README.md)
- [v3_ngrok_integrated/README.md](v3_ngrok_integrated/README.md)

## 주요 기능

- 실시간 음성 인식 (v2, v3)
- 화자 구분 (v2, v3)
- Function Calling
  - 시간 확인
  - 날씨 조회
  - 뉴스 요약
  - 주유소 가격
  - 노래/춤
  - 모션 제어 (박수, 악수, 인사, 이동)
- 고품질 한국어 TTS (v3)

## 기술 스택

- STT: WhisperLiveKit (Whisper + Sortformer)
- TTS: Supertonic2 / gTTS
- 음성 처리: PyAudio
- 웹 프레임워크: FastAPI
- AI: Ollama (gemma3:27b)
- 터널링: ngrok

## 개발 히스토리

자세한 개발 과정은 [docs/development_history.md](docs/development_history.md) 참고

## 라이선스

이 프로젝트는 교육 및 연구 목적으로 사용됩니다.

## 기여자

- A-Inhye (parkinhye0412@gmail.com)
