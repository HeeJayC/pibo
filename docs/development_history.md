# 개발 히스토리

파이보 음성 대화 시스템의 개발 과정을 기록합니다.

## v1_basic - 기본 시스템

초기 파이보 시스템

- gTTS 기반 음성 합성
- Function Calling 구현
- 로컬 환경에서만 동작

### 문제점
- 음성 인식 기능 없음
- 텍스트 입력만 가능
- 화자 구분 불가
- 인터넷 연결 필수 (gTTS)

## v2_whisperlivekit - STT 추가

WhisperLiveKit 도입으로 실시간 음성 인식 구현

- 실시간 STT 추가
- 화자 구분 (Sortformer)
- 갤럭시북 서버 + 파이보 클라이언트 구조

### 개선 사항
- 실시간 음성 인식
- 화자 구분 기능
- WebSocket 기반 통신

### 문제점
- 같은 WiFi/핫스팟 필요
- 원격 접속 불가
- GPU 활용 안 됨
- TTS 음질 개선 필요

## v3_ngrok_integrated - 통합 시스템 (최신)

ngrok 터널링 + 데스크톱 GPU + Supertonic2 TTS

### 아키텍처 변경
- 데스크톱: STT + TTS 통합 서버 (GPU 활용)
- 갤럭시북/파이보: 클라이언트만
- ngrok으로 원격 접속 가능

### 개선 사항
- 데스크톱 GPU 활용 (NVIDIA CUDA)
- 고품질 한국어 TTS (Supertonic2)
- 원격 접속 가능 (ngrok)
- TTS 자동 폴백 (Supertonic2 → gTTS)
- 로그 최적화 (INFO 로그 억제)

### 기술적 결정
1. STT: WhisperLiveKit small 모델 (속도와 정확도 균형)
2. TTS: Supertonic2 ONNX (고품질) + gTTS (폴백)
3. 통신: WebSocket (STT) + HTTP POST (TTS)
4. 터널링: ngrok (무료 버전)

### 해결한 문제들
- 과도한 로그 출력: logging.setLevel(WARNING)
- 네트워크 분리: ngrok 터널링
- TTS 품질: Supertonic2 도입
- GPU 활용: 데스크톱 서버화

## 향후 개선 방향

- TTS 스트리밍 최적화
- WebSocket TTS 지원
- 다중 클라이언트 지원
- 음성 품질 개선
- 응답 속도 최적화
