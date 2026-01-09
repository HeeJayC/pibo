# v1_basic - 기본 파이보 시스템

원본 파이보 음성 대화 시스템

## 특징

- gTTS 기반 음성 합성
- 로컬 환경에서만 동작
- Function Calling 지원 (시간, 날씨, 뉴스, 모션 등)
- 간단한 설치 및 실행

## 설치

```bash
pip install gtts requests beautifulsoup4 openpibo
```

## 실행

```bash
python pibo.py
```

## 지원 기능

- 시간 확인
- 날씨 조회
- 뉴스 요약
- 주유소 가격 조회
- 노래/춤
- 모션 제어 (박수, 악수, 인사, 이동)

## 제한사항

- 음성 인식 기능 없음 (텍스트 입력만)
- 화자 구분 불가
- 인터넷 연결 필요 (gTTS)
- 음질이 기본적인 수준
