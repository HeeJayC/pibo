# raspberrypi/test_tts.py
import requests
import subprocess
import os
import threading
import queue
import time

# 노트북 IP 설정 : 최희재 노트북
LAPTOP_IP = "172.20.10.6"
LAPTOP_PORT = 8000

TEMP_DIR = os.path.join(os.path.dirname(__file__), "_tmp_audio")
os.makedirs(TEMP_DIR, exist_ok=True)

def fetch_streaming(text, audio_queue):
    """
    스트리밍 방식으로 API 호출하고 청크 받기
    """
    api_url = f"http://{LAPTOP_IP}:{LAPTOP_PORT}/tts-stream"
    print(f"🌐 노트북 API 호출 중... ({api_url})")
    
    try:
        response = requests.post(
            api_url,
            params={"text": text},
            stream=True,  # 스트리밍 모드
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ API 오류: {response.status_code}")
            audio_queue.put(None)
            return
        
        chunk_idx = 0
        buffer = b''
        
        # 스트리밍 데이터 수신
        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:
                continue
            
            buffer += chunk
            
            # 최소 4바이트 (크기 정보) 있는지 확인
            while len(buffer) >= 4:
                # 청크 크기 읽기
                chunk_size = int.from_bytes(buffer[:4], byteorder='big')
                
                # 전체 청크 데이터가 도착했는지 확인
                if len(buffer) < 4 + chunk_size:
                    break
                
                # 청크 데이터 추출
                chunk_data = buffer[4:4+chunk_size]
                buffer = buffer[4+chunk_size:]
                
                chunk_idx += 1
                
                # 임시 파일로 저장
                temp_file = os.path.join(TEMP_DIR, f"chunk_{chunk_idx}.wav")
                with open(temp_file, "wb") as f:
                    f.write(chunk_data)
                
                print(f"✅ [{chunk_idx}] 청크 받기 완료 ({len(chunk_data)} bytes)")
                
                # 큐에 추가
                audio_queue.put((chunk_idx, temp_file))
        
        # 종료 신호
        audio_queue.put(None)
        print("✅ 모든 청크 받기 완료!")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 연결 오류: {e}")
        print(f"💡 노트북 IP({LAPTOP_IP})와 FastAPI 서버 실행 상태를 확인하세요.")
        audio_queue.put(None)

def play_audio(audio_queue):
    """
    큐에서 오디오 파일을 받아서 순서대로 재생
    """
    print("🔊 재생 준비 완료\n")
    
    while True:
        item = audio_queue.get()
        
        if item is None:
            print("✅ 모든 재생 완료!")
            break
        
        idx, audio_file = item
        print(f"▶️  [{idx}] 재생 중...")
        
        # aplay로 재생
        subprocess.run(["aplay", audio_file], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        
        # 재생 후 삭제
        if os.path.exists(audio_file):
            os.remove(audio_file)
        
        print(f"   ✅ [{idx}] 재생 완료")

def fetch_and_play_streaming():
    """
    스트리밍 방식으로 TTS 실행
    """
    # input.txt 읽기
    input_path = os.path.join(os.path.dirname(__file__), "input.txt")
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    print(f"📝 텍스트 읽기 완료: {len(text)} 글자")
    print("="*60)
    
    # 큐 생성
    audio_queue = queue.Queue(maxsize=3)
    
    # 다운로드 스레드
    fetch_thread = threading.Thread(
        target=fetch_streaming,
        args=(text, audio_queue),
        daemon=True
    )
    
    # 재생 스레드
    play_thread = threading.Thread(
        target=play_audio,
        args=(audio_queue,),
        daemon=True
    )
    
    # 스레드 시작
    fetch_thread.start()
    play_thread.start()
    
    # 모든 스레드 종료 대기
    fetch_thread.join()
    play_thread.join()
    
    print("="*60)
    print("🎉 완료!")

if __name__ == "__main__":
    fetch_and_play_streaming()