# pip install python-dotenv google-genai SpeechRecognition
import os
from dotenv import load_dotenv  
from google import genai
import sys
import speech_recognition as sr
import pyaudio
import webrtcvad
import numpy as np
import gtts
import argparse
import datetime
import requests
from bs4 import BeautifulSoup
import threading
import queue
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from openpibo.oled import Oled
from openpibo.motion import Motion

oled = Oled()
oled.clear()
# oled.draw_image('/home/pi/MIRAE/iamge/smile.jpg')
oled.show()

motion = Motion()
motion.set_motion('greeting', 1)

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
FRAME_DURATION_MS = 30 #프레임 길이(밀리 초) 
FRAME_SIZE = int(RATE * FRAME_DURATION_MS / 1000) #프레임당 샘플 수 
VAD_MODE = 1
RECORD_SECONDS_AFTER_SILENCE = 0.5  # 음성 종료 후 대기 시간 (1.0초 -> 2.5초로 증가)
MAX_SILENCE_FRAMES = int(RECORD_SECONDS_AFTER_SILENCE * 1000 / FRAME_DURATION_MS) # 종료 판단 프레임 수
NOISE_SAMPLE_DURATION = 0.5  # 노이즈 샘플링 시간 증가 (1.0초 -> 1.5초)
NOISE_SAMPLE_FRAMES = int(NOISE_SAMPLE_DURATION * 1000 / FRAME_DURATION_MS)
OUTPUT_FILENAME = "record.wav"
AMP = False
GAIN_DB = 10  # +10 dB 증폭
NOISE_SAMPLE_DURATION_AFTER_SPEECH = 0.5  # 음성 후 추가 대기 시간 (0.5초 -> 1.0초로 증가)

NUM_TTS_PARALLEL = 1  # 동시 TTS 처리 개수
MODEL_ID_LLM = "gemini-2.5-flash"
MODEL_ID_TTS = "gemini-2.5-flash-preview-tts"  # TTS 전용 모델
if sys.platform == 'linux':
    PATH_AUDIO_DIR = "./audio/"
else:
    PATH_AUDIO_DIR = "c:/Temp/"

load_dotenv()

# 메시지 템플릿 정의
SYSTEM_PROMPT = "다음 내용에 대해 자연스럽고 친근한 한국어로 응답해주세요:"

# Function Calling 정의    
def get_current_time(query: str):
    """현재 시간을 반환합니다."""

    now = datetime.datetime.now()
    content = f"현재 시간은 {now.strftime('%Y년 %m월 %d일 %H시 %M분')}입니다."
    return create_answer(query, content)

def get_naver_news():
    """네이버 뉴스 요약 오디오를 들려줍니다."""

    try:
        # SweetVoice.AI.py 파일이 존재하는지 확인
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

    return create_answer(query, price_table)

def sing_song(query: str):
    """노래를 부르고 춤을 춥니다."""
    try:
        # SweetVoice.AI.py 파일이 존재하는지 확인
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
    #extract text from table
    text = table[0].get_text(separator="\n")
    #remove all whitespace
    text = re.sub(r'\s+', '', text)
    #remove multiple newlines
    text = re.sub(r'\n+', '\n', text)
    return create_answer(query, text)


def get_ollama_response(prompt):
    try:
        # Django API 엔드포인트 사용
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
        return {"error": str(e)}
    except ValueError as e:
        print(f"JSON 파싱 오류: {e}")
        return {"error": f"JSON 파싱 오류: {e}"}


def create_answer(query: str, content: str):
    if query == "":
        query = "다음 내용을 요약해줘."
    else:
        if content == "":
            return get_ollama_response(query)
            # return g4f.ChatCompletion.create(model=g4f.models.default,
            #                          messages=[{"role": "user",
            #                                     "content": f"{query}"}])    
        else:
            return get_ollama_response(f"{query}\n참고자료: {content}")
            # return g4f.ChatCompletion.create(model=g4f.models.default,
            #                          messages=[{"role": "user",
            #                                     "content": f"{query}\n참고자료: {content}"}])    

def motion_clapping():
    motion.set_motion('clapping1', 1)
    
def motion_handshaking():
    motion.set_motion('handshaking', 1)

def motion_forward():
    motion.set_motion('forward1', 1)
    
# Function Calling 스키마 정의
AVAILABLE_FUNCTIONS = {
    "get_current_time": {
        "function": get_current_time,
        "description": "현재 시간을 알려줍니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "사용자의 요청 메시지"
                }
            },
            "required": []
        }
    },
    "get_naver_news": {
        "function": get_naver_news,
        "description": "네이버 뉴스 요약 오디오를 들려줍니다.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "get_oil_price": {
        "function": get_oil_price,
        "description": "지역별 주유소 가격을 반환합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "사용자의 요청 메시지"
                }
            },
            "required": []
        }
    },
    "sing_song": {
        "function": sing_song,
        "description": "노래를 부르고 춤을 춥니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "사용자의 요청 메시지"
                }
            },
            "required": []
        }
    },
    "get_weather": {
        "function": get_weather,
        "description": "날씨를 알려줍니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "사용자의 요청 메시지"
                }
            },
            "required": []
        }
    },
    "motion_clapping": {
        "function": motion_clapping,
        "description": "손을 크게 흔듭니다.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "motion_handshaking": {
        "function": motion_handshaking,
        "description": "악수를 합니다.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "motion_forward": {
        "function": motion_forward,
        "description": "앞으로 걸어갑니다.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}   

def rms(frame_bytes):
    """16-bit PCM 데이터의 RMS 구하기"""
    shorts = np.frombuffer(frame_bytes, dtype=np.int16)
    return np.sqrt(np.mean(shorts.astype(np.float32) ** 2))

def get_audio_data(frames):
    audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
    return audio_data

def amplify_audio(audio_data, gain_db):
    """녹음된 PCM 데이터를 지정한 dB만큼 증폭"""
    gain = 10 ** (gain_db / 20)
    amplified = np.clip(audio_data.astype(np.float32) * gain, -32768, 32767).astype(np.int16)
    return amplified

def measure_noise_floor(stream, sample_frames):
    print("Measuring ambient noise...")
    noise_levels = []
    for _ in range(sample_frames):
        frame = stream.read(FRAME_SIZE, exception_on_overflow=False)
        noise_levels.append(rms(frame))
    avg_noise = np.mean(noise_levels)
    print(f"Estimated RMS noise level: {avg_noise:.2f}")
    return avg_noise

def speech_to_text(audio, language='ko-KR'):
    """STT 변환 - 독립 함수"""
    try:
        recognizer = sr.Recognizer()
        text = recognizer.recognize_google(audio, language=language)
        return text
    except sr.UnknownValueError:
        print("음성을 인식할 수 없습니다.")
        return None
    except sr.RequestError as e:
        print(f"Google Speech Recognition 서비스 오류: {e}")
        return None
    except Exception as e:
        print(f"STT 오류: {e}")
        return None
    
def listen():
    try:
        stream = audio.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=FRAME_SIZE)

        print("말씀해주세요.")

        frames = []
        silence_counter = 0
        started = False

        while True:
            frame = stream.read(FRAME_SIZE, exception_on_overflow=False)
            is_speech = vad.is_speech(frame, RATE)

            if is_speech:
                frames.append(frame)
                started = True
                silence_counter = 0
            elif started:
                frames.append(frame)
                silence_counter += 1
                if silence_counter > MAX_SILENCE_FRAMES:
                    break

        print("Recording finished")

        audio_data = get_audio_data(frames)
        
        # AudioData 객체 생성
        audio_data_for_stt = sr.AudioData(b''.join(frames), RATE, 2)
        text = speech_to_text(audio_data_for_stt)

        if text:
            print(f"인식된 음성: {text}")
            
            # 중단 명령어 확인
            if "잠시만" in text or "잠깐만" in text or "중단" in text or "멈춰" in text:
                print("사용자 중단 명령 감지!")
                global should_stop_processing, current_tts_executor, current_playing_thread
                should_stop_processing = True
                
                # 병렬 TTS 처리 중단
                tts_processor.stop()
                
                # 기존 TTS 처리 중단
                if current_tts_executor:
                    print("TTS 처리 중단 중...")
                    current_tts_executor.shutdown(wait=False)
                    current_tts_executor = None
                
                if current_playing_thread and current_playing_thread.is_alive():
                    print("오디오 재생 중단 중...")
                
                return None  # 중단 명령이므로 None 반환
            
        return text

    finally:
        stream.stop_stream()
        stream.close()

def create_script(content: str):
    return get_ollama_response(f"{SYSTEM_PROMPT}\n{content}")
    # return g4f.ChatCompletion.create(model=g4f.models.default, messages=[{"role": "user", "content": f"{SYSTEM_PROMPT}\n{content}"}])
    

def execute_function_call(function_name, arguments):
    """함수 호출을 실행합니다."""
    if function_name in AVAILABLE_FUNCTIONS:
        func = AVAILABLE_FUNCTIONS[function_name]["function"]
        try:
            if arguments:
                result = func(**arguments)
            else:
                result = func()
            return result
        except Exception as e:
            return f"함수 실행 오류: {str(e)}"
    else:
        return f"알 수 없는 함수: {function_name}"

def create_ai_response_with_functions(user_message: str):
    """간단한 키워드 기반 function calling 지원 응답"""
    try:
        user_lower = user_message.lower()
        
        # 시간 관련 요청 감지
        if any(keyword in user_lower for keyword in ['시간', '몇 시', '현재', '지금']):
            print("함수 호출: get_current_time()")
            function_result = execute_function_call("get_current_time", {"query": user_message})
            return function_result
        
        # 뉴스 관련 요청 감지  
        elif any(keyword in user_lower for keyword in ['뉴스', 'news']):
            print("함수 호출: get_naver_news()")
            function_result = execute_function_call("get_naver_news", {})
            return function_result
        
        # 주유소 가격 관련 요청 감지
        elif any(keyword in user_lower for keyword in ['주유소', '가격']):
            print("함수 호출: get_oil_price()")
            function_result = execute_function_call("get_oil_price", {"query": user_message})
            return function_result
        
        # 노래 관련 요청 감지
        elif any(keyword in user_lower for keyword in ['노래', '노래 부르기']):
            print("함수 호출: sing_song()")
            function_result = execute_function_call("sing_song", {"query": user_message})
            return function_result
        
        # 날씨 관련 요청 감지
        elif any(keyword in user_lower for keyword in ['날씨', '날씨 알려줘']):
            print("함수 호출: get_weather()")
            function_result = execute_function_call("get_weather", {"query": user_message})
            return function_result
        
        # 손 크게 흔들기
        elif any(keyword in user_lower for keyword in ['손', '크게 흔들기']):
            print("함수 호출: motion_clapping()")
            function_result = execute_function_call("motion_clapping", {})
            return function_result
        
        # 악수
        elif any(keyword in user_lower for keyword in ['악수', '악수 해줘']):
            print("함수 호출: motion_handshaking()")
            function_result = execute_function_call("motion_handshaking", {})
            return function_result
        
        # 앞으로 걸어감
        elif any(keyword in user_lower for keyword in ['앞으로', '앞으로 걸어감']):
            print("함수 호출: motion_forward()")
            function_result = execute_function_call("motion_forward", {})
            return function_result
        
        # 일반 대화의 경우 g4f 사용
        else:
            return create_ai_response_fallback(user_message)
        
    except Exception as e:
        print(f"Function calling 오류: {e}")
        # 백업으로 g4f 사용
        return create_ai_response_fallback(user_message)

def create_ai_response_fallback(user_message: str):
    """백업 AI 응답 (g4f 사용)"""
    try:
        return get_ollama_response(user_message)
        # return g4f.ChatCompletion.create(
        #     model=g4f.models.default,
        #     messages=[{"role": "user", "content": user_message}]
        # )
    except Exception as e:
        return f"AI 응답 생성 중 오류가 발생했습니다: {str(e)}"

def split_into_sentences(text):
    """텍스트를 문장 단위로 분리합니다."""
    # 한국어 문장 구분자로 분리
    sentences = re.split(r'[.!?]+', text)
    # 빈 문장 제거 및 정리
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences

def create_audio_single(script: str, path_file: str):
    """단일 문장의 오디오 파일을 생성합니다."""
    try:
        tts = gtts.gTTS(script, lang='ko')
        tts.save(path_file)
        print(f"# 오디오 파일 생성 완료: {path_file}")
        return path_file
    except Exception as e:
        print(f"오디오 생성 오류: {e}")
        return None

def create_audio(script: str, path_file: str = "script.mp3"):
    """기존 단일 오디오 생성 함수 (하위 호환성)"""
    return create_audio_single(script, path_file)

class ParallelTTSProcessor:
    """병렬 TTS 처리 및 순차 재생을 관리하는 클래스"""
    
    def __init__(self, max_workers=3):
        self.max_workers = max_workers
        self.audio_queue = queue.Queue()
        self.is_playing = False
        self.should_stop = False
        
    def process_and_play(self, full_text: str):
        """전체 텍스트를 문장으로 나누고 병렬 처리하여 순차 재생"""
        sentences = split_into_sentences(full_text)
        if not sentences:
            return
            
        print(f"총 {len(sentences)}개 문장으로 분리됨")
        
        # 재생 스레드 시작
        play_thread = threading.Thread(target=self._play_audio_queue, daemon=True)
        play_thread.start()
        
        # 병렬 TTS 처리
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 처음 3개 문장 먼저 제출
            future_to_sentence = {}
            processed_count = 0
            
            for i, sentence in enumerate(sentences):
                if i < self.max_workers:  # 처음 3개
                    audio_file = f"sentence_{i}.mp3"
                    future = executor.submit(create_audio_single, sentence, audio_file)
                    future_to_sentence[future] = (i, sentence, audio_file)
                    processed_count += 1
            
            # 완료된 순서대로 처리하고 새로운 작업 추가
            for future in as_completed(future_to_sentence):
                if self.should_stop:
                    break
                    
                sentence_idx, sentence_text, audio_file = future_to_sentence[future]
                result = future.result()
                
                if result:
                    # 완료된 오디오를 큐에 추가 (순서대로 정렬하기 위해 인덱스와 함께)
                    self.audio_queue.put((sentence_idx, result))
                    print(f"✅ 문장 {sentence_idx + 1} 준비 완료")
                
                # 다음 문장이 있으면 새로운 작업 추가
                if processed_count < len(sentences):
                    next_sentence = sentences[processed_count]
                    next_audio_file = f"sentence_{processed_count}.mp3"
                    next_future = executor.submit(create_audio_single, next_sentence, next_audio_file)
                    future_to_sentence[next_future] = (processed_count, next_sentence, next_audio_file)
                    processed_count += 1
        
        # 모든 작업 완료 신호
        self.audio_queue.put((-1, None))  # 종료 신호
        play_thread.join()
        
    def _play_audio_queue(self):
        """큐에서 오디오 파일을 순서대로 재생"""
        audio_buffer = {}  # 인덱스별로 오디오 파일 저장
        next_to_play = 0
        
        while True:
            try:
                item = self.audio_queue.get(timeout=30)  # 30초 타임아웃
                
                if item[0] == -1:  # 종료 신호
                    break
                    
                sentence_idx, audio_file = item
                audio_buffer[sentence_idx] = audio_file
                
                # 순서대로 재생
                while next_to_play in audio_buffer:
                    if self.should_stop:
                        return
                        
                    file_to_play = audio_buffer[next_to_play]
                    print(f"문장 {next_to_play + 1} 재생 중...")
                    self._play_single_audio(file_to_play)
                    
                    # 재생 완료 후 파일 삭제
                    try:
                        os.remove(file_to_play)
                    except:
                        pass
                        
                    del audio_buffer[next_to_play]
                    next_to_play += 1
                    
            except queue.Empty:
                print("오디오 처리 타임아웃")
                break
                
    def _play_single_audio(self, audio_file: str):
        """단일 오디오 파일 재생"""
        try:
            if os.name == 'nt':
                os.system(f"start /wait {audio_file}")
            elif os.name == 'posix':
                os.system(f"play {audio_file}")
            else:
                # Jupyter 환경
                from IPython.display import Audio, display
                display(Audio(audio_file, autoplay=True))
                time.sleep(2)  # 재생 시간 대기
        except Exception as e:
            print(f"오디오 재생 오류: {e}")
            
    def stop(self):
        """처리 중단"""
        self.should_stop = True


def play_audio(path_file: str = "script.mp3"):
    print(f"# 오디오 재생: {path_file}")
    if os.name == 'nt':
        os.system(f"start {path_file}")
    elif os.name == 'posix':
        os.system(f"play {path_file}")        
    else:
        from IPython.display import Audio, display
        display(Audio(path_file, autoplay=True))

def continuous_conversation(args):
    global should_stop_processing
    is_running = True
    while is_running:
        try:
            print("음성 대화 모드 시작")
            print("팁: '종료' = 프로그램 종료, '무음' = 음성 중단")
            
            if args.mic:
                text = listen()
            else:
                text = input("사용자: ")
                    
            if text is None:
                # 중단 명령이거나 음성 인식 실패
                if should_stop_processing:
                    print("사용자 요청으로 작업이 중단되었습니다.")
                    should_stop_processing = False  # 플래그 리셋
                continue
            
            # 종료 명령 확인
            if "종료" in text or "끝" in text:
                print("음성 대화를 종료합니다.")
                break
            
            # 빠른 모드 확인
            
            args.speaker = False if "무음" in text else True
            if args.speaker:
                text = text.replace("무음", "").strip()
            
            # AI 응답 생성
            answer = create_ai_response_with_functions(text)
            print(f"AI: {answer}")
            
            # 빠른 모드가 아닌 경우 병렬 TTS 처리
            if args.speaker:
                print("병렬 TTS 처리 시작...")
                # 새로운 프로세서 인스턴스 생성 (이전 상태 초기화)
                current_processor = ParallelTTSProcessor()
                current_processor.process_and_play(answer)
            else:
                print("빠른 모드: 음성 생성을 건너뜁니다.")
            
        except KeyboardInterrupt:
            print("\n음성 대화를 종료합니다.")
            break
        except Exception as e:
            print(f"오류 발생: {e}")
            continue

if __name__ == "__main__":
    # API 키 설정
    client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    
    parser = argparse.ArgumentParser(description="MIRIX")
    parser.add_argument("-m", "--mic", action='store_true', default=True, help="마이크 사용 여부")
    parser.add_argument("-s", "--speaker", action='store_true', default=True, help="스피커 사용 여부")
    args = parser.parse_args()
    
    # 전역 변수들
    should_stop_processing = False
    current_tts_executor = None
    current_playing_thread = None
    vad = webrtcvad.Vad(VAD_MODE)
    audio = pyaudio.PyAudio()
    tts_processor = ParallelTTSProcessor()
    
    continuous_conversation(args)
