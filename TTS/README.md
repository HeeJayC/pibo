FastAPI 서버 실행 방법

&nbsp;   cd C:\\Users\\Heeja\\PIBO\_TTS\\supertonic-2\\MIRAE\\laptop

&nbsp;   uvicorn api:app --host 0.0.0.0 --port 8000



&nbsp;   http://172.20.10.6:8000/docs

&nbsp;       172.20.10.6 : 최희재 노트북 IP



파이썬 파일 설명

&nbsp;   laptop

&nbsp;       run\_tts.py : 노트북에서 TTS 파일 생성 (테스트용 파일)

&nbsp;       api.py : FastAPI 서버 실행용

&nbsp;       helper.py

&nbsp;       tts\_engine.py : TTS 엔진

&nbsp;   raspberrypi

&nbsp;       input.txt : TTS 파일 생성용 텍스트 파일 (LLM 답변이 저장되는 파일)

&nbsp;       test\_tts.py : 로봇에서 TTS 파일 재생

