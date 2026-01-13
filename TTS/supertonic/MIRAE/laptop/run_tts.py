# run_tts.py
import os
import threading
import queue
import winsound  # Windows 내장 재생
from scipy.io import wavfile
from tts_engine import TTSEngine

# MIRAE/laptop에서 2단계 위로 올라가야 함
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

ENGINE = TTSEngine(
    onnx_dir=os.path.join(BASE_DIR, "assets", "onnx"),
    voice_style_path=os.path.join(BASE_DIR, "assets", "voice_styles", "M1.json")
)


# 임시 파일 저장 디렉토리 (MIRAE 폴더 아래)
TEMP_DIR = os.path.join(os.path.dirname(__file__), "..", "_tmp_audio")
os.makedirs(TEMP_DIR, exist_ok=True)

def producer(text, audio_queue):
    """
    문장 단위로 음원 생성하는 스레드
    """
    print("🔄 음원 생성 시작...\n")
    
    for wav, idx in ENGINE.synthesize_streaming(text):
        # 임시 파일로 저장 (MIRAE/_tmp_audio 아래)
        temp_file = os.path.join(TEMP_DIR, f"chunk_{idx}.wav")
        wavfile.write(temp_file, ENGINE.sample_rate, wav)
        
        # 큐에 추가
        audio_queue.put((idx, temp_file))
    
    # 종료 신호
    audio_queue.put(None)
    print("\n✅ 모든 음원 생성 완료!")

def consumer(audio_queue):
    """
    생성된 음원을 순서대로 재생하는 스레드
    """
    print("🔊 재생 준비 완료\n")
    
    while True:
        item = audio_queue.get()
        
        if item is None:
            print("✅ 모든 재생 완료!")
            break
        
        idx, audio_file = item
        print(f"▶️  [{idx}] 재생 중: {os.path.basename(audio_file)}")
        
        try:
            # Windows 내장 winsound 사용
            winsound.PlaySound(audio_file, winsound.SND_FILENAME)
            print(f"   ✅ 재생 완료")
        except Exception as e:
            print(f"   ⚠️  재생 오류: {e}")
        
        # 재생 완료 후 임시 파일 삭제
        if os.path.exists(audio_file):
            os.remove(audio_file)

if __name__ == "__main__":
    # input.txt 읽기
    input_path = os.path.join(os.path.dirname(__file__), "..", "raspberrypi", "input.txt")
    
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    print(f"📝 텍스트 읽기 완료: {len(text)} 글자")
    print(f"📁 임시 파일 저장 위치: {TEMP_DIR}\n")
    print("="*60)
    
    # 큐 생성
    audio_queue = queue.Queue(maxsize=3)  # 최대 3개까지 버퍼링
    
    # 생성 스레드
    producer_thread = threading.Thread(
        target=producer,
        args=(text, audio_queue),
        daemon=True
    )
    
    # 재생 스레드
    consumer_thread = threading.Thread(
        target=consumer,
        args=(audio_queue,),
        daemon=True
    )
    
    # 스레드 시작
    producer_thread.start()
    consumer_thread.start()
    
    # 모든 스레드가 끝날 때까지 대기
    producer_thread.join()
    consumer_thread.join()
    
    print("\n" + "="*60)
    print("🎉 프로그램 종료")