# TTS 시스템 사용 가이드

Supertonic2 기반 한국어 TTS (Text-to-Speech) 엔진

## 폴더 구조

```
TTS/
└── supertonic2/
    ├── onnx/              (ONNX 모델 파일들)
    ├── voice_styles/      (음성 스타일 설정 파일들)
    └── MIRAE/
        ├── laptop/        (데스크톱/노트북용 코드)
        │   ├── run_tts.py
        │   ├── api.py
        │   ├── tts_engine.py
        │   └── helper.py
        └── raspberrypi/   (라즈베리파이용 코드)
            └── test_tts.py
```

## 설치 방법

### 필수 패키지

```bash
pip install scipy onnxruntime numpy
```

Windows의 경우 `winsound`는 기본 내장되어 있습니다.

## 사용 방법

### 1. 기본 실행 (run_tts.py)

```bash
cd "C:\Users\User\UST 인턴\1월 9일\TTS\supertonic2\MIRAE\laptop"
python run_tts.py
```

프로그램이 실행되면 텍스트를 입력하고 음성으로 변환됩니다.

### 2. API 서버 실행 (api.py)

```bash
cd "C:\Users\User\UST 인턴\1월 9일\TTS\supertonic2\MIRAE\laptop"
python api.py
```

FastAPI 서버가 실행되어 HTTP API로 TTS를 사용할 수 있습니다.

## 주요 기능

### 스트리밍 TTS
- 문장 단위로 음성을 생성하면서 동시에 재생
- 긴 텍스트도 빠르게 재생 시작

### 음성 스타일
- `voice_styles` 폴더에서 다양한 음성 스타일 선택 가능
- 기본값: M1.json

### 임시 파일 관리
- 생성된 음성 파일은 `MIRAE/_tmp_audio/` 폴더에 임시 저장
- 재생 후 자동 정리

## 파이보 프로젝트와 연동

파이보 클라이언트에서 gTTS 대신 Supertonic2를 사용하려면:

1. TTS 엔진 import
2. `create_audio_single` 함수 수정
3. Supertonic2 엔진으로 음성 생성

### 연동 예시

```python
from TTS.supertonic2.MIRAE.laptop.tts_engine import TTSEngine

# TTS 엔진 초기화
tts_engine = TTSEngine(
    onnx_dir="경로/TTS/supertonic2/onnx",
    voice_style_path="경로/TTS/supertonic2/voice_styles/M1.json"
)

def create_audio_with_supertonic(text, output_file):
    # 음성 생성
    for wav, idx in tts_engine.synthesize_streaming(text):
        # 첫 번째 청크만 사용 (전체 텍스트 한번에)
        from scipy.io import wavfile
        wavfile.write(output_file, tts_engine.sample_rate, wav)
        break
    return output_file
```

## 파일 설명

### run_tts.py
- 스탠드얼론 TTS 실행 프로그램
- 스트리밍 재생 기능
- Producer-Consumer 패턴으로 효율적인 처리

### api.py
- FastAPI 기반 HTTP API 서버
- REST API로 TTS 서비스 제공

### tts_engine.py
- Supertonic2 TTS 엔진 핵심 코드
- ONNX 모델 로드 및 추론

### helper.py
- 유틸리티 함수들
- 전처리, 후처리 등

## 문제 해결

### ONNX 모델이 없다는 오류
- `supertonic2/onnx/` 폴더에 모델 파일이 있는지 확인
- Supertonic 2 모델을 다운로드 받아 배치

### 음성 스타일 파일 없음
- `supertonic2/voice_styles/` 폴더 확인
- M1.json 파일 존재 여부 확인

### Windows에서 재생 안 됨
- `winsound` 모듈은 Windows 전용
- Linux/Mac에서는 `pyaudio` 또는 `playsound` 사용 필요

## 성능 비교

| 항목 | gTTS | Supertonic2 |
|------|------|-------------|
| 음질 | 보통 | 우수 |
| 속도 | 느림 (인터넷 필요) | 빠름 (로컬) |
| 오프라인 | 불가 | 가능 |
| 한국어 자연스러움 | 보통 | 매우 좋음 |

## 라이선스 및 주의사항

- Supertonic2는 상업적 사용에 제한이 있을 수 있습니다
- 모델 파일은 별도로 다운로드 필요
- ONNX 런타임 버전 호환성 확인 필요
