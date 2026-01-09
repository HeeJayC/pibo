# WhisperLiveKit 서버 연동 갤럭시북 클라이언트
# ngrok URL을 통해 데스크톱 서버에 연결
# 원본 pibo.py의 Function Calling 유지
# pip install websocket-client pyaudio gtts requests beautifulsoup4 openpibo

import os
import sys
import json
import websocket
import pyaudio
import threading
import time
from dotenv import load_dotenv
import datetime
import requests
from bs4 import BeautifulSoup
import gtts
import re
import queue as Queue

# 파이보 로봇 import
try:
    from openpibo.oled import Oled
    from openpibo.motion import Motion

    oled = Oled()
    oled.clear()
    oled.show()

    motion = Motion()
    motion.set_motion('greeting', 1)
    PIBO_MODE = True
    print("파이보 모드 활성화")
except ImportError:
    print("파이보 라이브러리 없음 - 시뮬레이션 모드")
    PIBO_MODE = False

    class Oled:
        def clear(self): pass
        def show(self): pass

    class Motion:
        def set_motion(self, name, speed):
            print(f"[모션] {name}")

    oled = Oled()
    motion = Motion()

# 설정
load_dotenv()

# 데스크톱 서버 주소 (ngrok URL로 변경)
# ngrok 실행 후 나오는 URL을 여기에 입력하세요
# 예: "abc123def456.ngrok.io"
SERVER_HOST = "YOUR_NGROK_URL_HERE"  # ngrok URL (https:// 제외)
USE_HTTPS = True  # ngrok은 https 사용

# 오디오 설정
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024

# TTS 설정
if sys.platform == 'linux':
    PATH_AUDIO_DIR = "./audio/"
    os.makedirs(PATH_AUDIO_DIR, exist_ok=True)
else:
    PATH_AUDIO_DIR = "c:/Temp/"


# Function Calling 정의 (원본 pibo.py)

def get_current_time(query: str):
    """현재 시간을 반환합니다."""
    now = datetime.datetime.now()
    content = f"현재 시간은 {now.strftime('%Y년 %m월 %d일 %H시 %M분')}입니다."
    return create_answer(query, content)


def get_naver_news():
    """네이버 뉴스 요약 오디오를 들려줍니다."""
    try:
        if os.path.exists("SweetVoice.AI.py"):
            os.system("python SweetVoice.AI.py")
            return "네이버 뉴스 요약 오디오를 들려줍니다."
        else:
            return "뉴스 서비스 파일을 찾을 수 없습니다. 나중에 다시 시도해주세요."
    except Exception as e:
        return f"뉴스 서비스 실행 중 오류가 발생했습니다: {str(e)}"


def get_oil_price(query: str):
    """지역별 주유소 가격을 반환합니다."""
    print('https://www.opinet.co.kr/user/dopospdrg/dopOsPdrgAreaView.do를 검색 중입니다...')
    url = "https://www.opinet.co.kr/user/dopospdrg/dopOsPdrgAreaView.do"
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    price_table = soup.find("div", {"id": "table_form"}).select("tr")
    return create_answer(query, str(price_table))


def sing_song(query: str):
    """노래를 부르고 춤을 춥니다."""
    try:
        if os.path.exists("music_eye.py"):
            os.system("/usr/bin/python3 music_eye.py")
            return ""
        else:
            return "노래 서비스 파일을 찾을 수 없습니다. 나중에 다시 시도해주세요."
    except Exception as e:
        return f"노래 서비스 실행 중 오류가 발생했습니다: {str(e)}"


def get_weather(query: str):
    """날씨를 알려줍니다."""
    url = "https://www.weather.go.kr/w/observation/land/aws-obs.do"
    print(f'{url}를 검색 중입니다...')
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    table = soup.find("div", {"id": "aws-data-holder"}).select("table")
    text = table[0].get_text(separator="\n")
    text = re.sub(r'\s+', '', text)
    text = re.sub(r'\n+', '\n', text)
    return create_answer(query, text)


def get_ollama_response(prompt):
    try:
        response = requests.post(
            f"https://agentmap.org/api/generate/",
            json={
                "prompt": prompt,
                "model": "gemma3:27b"
            },
            headers={"Content-Type": "application/json"},
            timeout=300
        )
        response.raise_for_status()

        result = response.json()
        if result.get('success'):
            return result.get('response', '').replace("*", "")
        else:
            return result.get('error', '알 수 없는 오류')

    except requests.exceptions.RequestException as e:
        print(f"API 호출 오류: {e}")
        return f"오류: {str(e)}"
    except ValueError as e:
        print(f"JSON 파싱 오류: {e}")
        return f"JSON 파싱 오류: {str(e)}"


def create_answer(query: str, content: str):
    """원본 pibo.py의 create_answer 함수"""
    if query == "":
        query = "다음 내용을 요약해줘."

    if content == "":
        return get_ollama_response(query)
    else:
        return get_ollama_response(f"{query}\n참고자료: {content}")


def motion_clapping():
    motion.set_motion('clapping1', 1)

def motion_handshaking():
    motion.set_motion('handshaking', 1)

def motion_forward():
    motion.set_motion('forward1', 1)

def motion_greeting():
    motion.set_motion('greeting', 1)


def execute_function_call(function_name, arguments):
    """함수 호출 실행"""
    functions = {
        "get_current_time": get_current_time,
        "get_naver_news": get_naver_news,
        "get_oil_price": get_oil_price,
        "sing_song": sing_song,
        "get_weather": get_weather,
        "motion_clapping": motion_clapping,
        "motion_handshaking": motion_handshaking,
        "motion_forward": motion_forward,
        "motion_greeting": motion_greeting,
    }

    if function_name in functions:
        func = functions[function_name]
        try:
            if arguments:
                return func(**arguments)
            else:
                return func()
        except Exception as e:
            return f"함수 실행 오류: {str(e)}"
    return f"알 수 없는 함수: {function_name}"


def create_ai_response_with_functions(user_message: str):
    """원본 pibo.py의 키워드 기반 function calling"""
    try:
        user_lower = user_message.lower()

        # 시간 관련 키워드
        if any(keyword in user_lower for keyword in ['시간', '몇 시', '현재', '지금']):
            print("함수 호출: get_current_time()")
            return execute_function_call("get_current_time", {"query": user_message})

        # 뉴스 관련 키워드
        elif any(keyword in user_lower for keyword in ['뉴스', 'news']):
            print("함수 호출: get_naver_news()")
            return execute_function_call("get_naver_news", {})

        # 유가 관련 키워드
        elif any(keyword in user_lower for keyword in ['유가', '기름값', '주유소']):
            print("함수 호출: get_oil_price()")
            return execute_function_call("get_oil_price", {"query": user_message})

        # 노래 관련 키워드
        elif any(keyword in user_lower for keyword in ['노래', '음악', '춤']):
            print("함수 호출: sing_song()")
            return execute_function_call("sing_song", {"query": user_message})

        # 날씨 관련 키워드
        elif any(keyword in user_lower for keyword in ['날씨']):
            print("함수 호출: get_weather()")
            return execute_function_call("get_weather", {"query": user_message})

        # 박수 관련 키워드
        elif any(keyword in user_lower for keyword in ['박수', '짝짝']):
            print("함수 호출: motion_clapping()")
            execute_function_call("motion_clapping", {})
            return "박수를 칩니다!"

        # 악수 관련 키워드
        elif any(keyword in user_lower for keyword in ['악수']):
            print("함수 호출: motion_handshaking()")
            execute_function_call("motion_handshaking", {})
            return "악수를 합니다!"

        # 안녕 관련 키워드
        elif any(keyword in user_lower for keyword in ['안녕']):
            print("함수 호출: motion_greeting()")
            execute_function_call("motion_greeting", {})
            return "안녕하세요! 반갑습니다!"

        # 앞으로 관련 키워드
        elif any(keyword in user_lower for keyword in ['앞으로']):
            print("함수 호출: motion_forward()")
            execute_function_call("motion_forward", {})
            return "앞으로 이동합니다!"

        # 일반 대화
        else:
            return get_ollama_response(user_message)

    except Exception as e:
        print(f"Function calling 오류: {e}")
        return get_ollama_response(user_message)


# TTS

def create_audio_single(script: str, path_file: str):
    """서버의 TTS API를 호출하여 음성 생성 (Supertonic2)"""
    try:
        # 서버 TTS API 호출
        protocol = "https" if USE_HTTPS else "http"
        tts_url = f"{protocol}://{SERVER_HOST}/tts"

        print(f"[TTS] 서버에서 음성 생성 중...")
        response = requests.post(
            tts_url,
            json={"text": script},
            timeout=30
        )

        if response.status_code == 200:
            # WAV 파일 저장
            with open(path_file, 'wb') as f:
                f.write(response.content)
            print(f"[TTS] 음성 생성 완료: {path_file}")
            return path_file
        else:
            print(f"[TTS] 서버 오류: {response.status_code}")
            # 실패 시 gTTS로 폴백
            print(f"[TTS] gTTS로 폴백...")
            tts = gtts.gTTS(script, lang='ko')
            tts.save(path_file)
            return path_file

    except Exception as e:
        print(f"[TTS] 서버 연결 실패: {e}")
        # 실패 시 gTTS로 폴백
        try:
            print(f"[TTS] gTTS로 폴백...")
            tts = gtts.gTTS(script, lang='ko')
            tts.save(path_file)
            return path_file
        except Exception as e2:
            print(f"오디오 생성 오류: {e2}")
            return None


def play_audio(path_file: str):
    try:
        if os.name == 'nt':
            os.system(f'start "" "{path_file}"')
        elif os.name == 'posix':
            os.system(f"play {path_file} 2>/dev/null || aplay {path_file} 2>/dev/null || mpg123 {path_file} 2>/dev/null")
    except Exception as e:
        print(f"오디오 재생 오류: {e}")


# WebSocket 클라이언트

class WhisperLiveKitClient:
    def __init__(self, server_url):
        self.server_url = server_url
        self.ws = None
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.transcript_queue = Queue.Queue()
        self.current_transcript = ""
        self.is_recording = False
        self.connected = False

    def on_message(self, ws, message):
        try:
            data = json.loads(message)

            if data.get("type") == "config":
                print(f"서버 설정 수신: {data}")

            elif data.get("type") == "transcript_update":
                segments = data.get("segments", [])

                # 전체 트랜스크립트 재구성
                full_text = ""
                for segment in segments:
                    speaker = segment.get("speaker", 0)
                    text = segment.get("text", "")
                    buffer_diarization = segment.get("buffer", {}).get("diarization", "")

                    # 화자 정보 포함
                    if text or buffer_diarization:
                        full_text += f"[화자{speaker}] {text}{buffer_diarization} "

                if full_text.strip():
                    self.current_transcript = full_text.strip()
                    print(f"\n실시간 인식: {self.current_transcript}")

            elif data.get("type") == "ready_to_stop":
                # 녹음 종료 시 최종 트랜스크립트를 큐에 넣음
                if self.current_transcript:
                    # 화자 정보 제거하고 순수 텍스트만 추출
                    clean_text = re.sub(r'\[화자\d+\]\s*', '', self.current_transcript)
                    self.transcript_queue.put(clean_text)
                    print(f"\n최종 인식 결과: {clean_text}")

        except json.JSONDecodeError:
            print(f"잘못된 JSON: {message}")
        except Exception as e:
            print(f"메시지 처리 오류: {e}")

    def on_error(self, ws, error):
        print(f"WebSocket 오류: {error}")
        self.connected = False

    def on_close(self, ws, close_status_code, close_msg):
        print("서버 연결 종료")
        self.connected = False
        self.is_recording = False

    def on_open(self, ws):
        print("서버 연결 성공!")
        self.connected = True

    def connect(self):
        print(f"서버 연결 중: {self.server_url}")

        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(
            self.server_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )

        ws_thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        ws_thread.start()

        for i in range(10):
            if self.connected:
                return True
            time.sleep(0.5)

        print("서버 연결 실패!")
        return False

    def start_recording(self):
        """녹음 시작"""
        if not self.connected:
            print("서버에 연결되지 않았습니다.")
            return

        self.stream = self.audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        self.is_recording = True
        self.current_transcript = ""

        print("\n녹음 시작... (Enter 키를 누르면 중지)")

        def record_audio():
            while self.is_recording:
                try:
                    data = self.stream.read(CHUNK, exception_on_overflow=False)
                    if self.ws and self.ws.sock and self.ws.sock.connected:
                        self.ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)
                except Exception as e:
                    print(f"녹음 오류: {e}")
                    break

        record_thread = threading.Thread(target=record_audio, daemon=True)
        record_thread.start()

    def stop_recording(self):
        """녹음 중지"""
        self.is_recording = False

        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        print("녹음 중지")

        # 잠시 대기 (서버 처리 시간)
        time.sleep(1)

    def get_transcript(self):
        """트랜스크립트 가져오기"""
        try:
            return self.transcript_queue.get(timeout=5)
        except Queue.Empty:
            return None

    def close(self):
        if self.ws:
            self.ws.close()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()


# 메인

def main():
    print("파이보 음성 대화 클라이언트 (WhisperLiveKit 연동)")
    print("화자 인식 기능 활성화")
    print("데스크톱 서버에 ngrok을 통해 연결")

    # ngrok URL 확인
    if SERVER_HOST == "YOUR_NGROK_URL_HERE":
        print("\n오류: SERVER_HOST를 설정하지 않았습니다!")
        print("1. 데스크톱에서 ngrok 실행: ngrok http 9090")
        print("2. 나온 URL(예: abc123.ngrok.io)을 SERVER_HOST에 입력")
        print("3. 이 프로그램 다시 실행")
        return

    # WebSocket URL 생성 (https 사용 시 wss://)
    protocol = "wss" if USE_HTTPS else "ws"
    server_url = f"{protocol}://{SERVER_HOST}/asr"
    print(f"서버: {server_url}")

    client = WhisperLiveKitClient(server_url)

    try:
        if not client.connect():
            print("서버에 연결할 수 없습니다.")
            print("데스크톱에서 서버가 실행 중인지 확인하세요:")
            print("  python desktop_server_whisperlivekit.py")
            print("  ngrok http 9090")
            return

        print("\n음성 대화를 시작합니다!")
        print("종료하려면 '종료', '끝', '그만'이라고 말하세요.\n")

        while True:
            # 녹음 시작
            client.start_recording()

            # Enter 키 대기
            input()

            # 녹음 중지
            client.stop_recording()

            # 트랜스크립트 가져오기
            text = client.get_transcript()

            if text:
                print(f"\n인식 결과: {text}\n")

                if any(word in text for word in ['종료', '끝', '그만', '정지']):
                    print("\n프로그램을 종료합니다.")
                    break

                print("응답 생성 중...")
                response = create_ai_response_with_functions(text)
                print(f"파이보: {response}\n")

                if response:
                    audio_file = os.path.join(PATH_AUDIO_DIR, "response.wav")
                    if create_audio_single(response, audio_file):
                        play_audio(audio_file)
                        time.sleep(len(response) * 0.1)
            else:
                print("음성을 인식하지 못했습니다. 다시 시도해주세요.\n")

    except KeyboardInterrupt:
        print("\n\n사용자 중단")

    finally:
        client.close()
        print("클라이언트 종료")


if __name__ == "__main__":
    main()
