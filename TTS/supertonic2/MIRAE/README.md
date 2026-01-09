파이썬 파일 설명
    laptop
        run_tts.py : 노트북에서 TTS 파일 생성 (테스트용 파일)
        api.py : FastAPI 서버 실행용
        helper.py
        tts_engine.py : TTS 엔진
    raspberrypi
        input.txt : TTS 파일 생성용 텍스트 파일 (LLM 답변이 저장되는 파일)
        test_tts.py : 로봇에서 TTS 파일 재생

FastAPI 서버 실행 방법
    cd C:\Users\Heeja\PIBO_TTS\supertonic-2\MIRAE\laptop
    uvicorn api:app --host 0.0.0.0 --port 8000

    http://172.20.10.6:8000/docs
        172.20.10.6 : 최희재 노트북 IP
