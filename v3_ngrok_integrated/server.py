# WhisperLiveKit 기반 데스크톱 STT + TTS 서버 (화자 인식 포함)
# 데스크톱에서 실행 (NVIDIA GPU 활용)
# STT: WhisperLiveKit, TTS: Supertonic2
# pip install whisperlivekit fastapi uvicorn[standard] websockets python-multipart nemo_toolkit[asr] numpy scipy soundfile torch torchaudio transformers onnxruntime

import asyncio
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from whisperlivekit import AudioProcessor, TranscriptionEngine
from dataclasses import asdict, is_dataclass
import torch
import logging

# WhisperLiveKit의 과도한 로그 억제
logging.getLogger("whisperlivekit").setLevel(logging.WARNING)
logging.getLogger("whisperlivekit.audio_processor").setLevel(logging.WARNING)
logging.getLogger("whisperlivekit.simul_whisper.simul_whisper").setLevel(logging.WARNING)
logging.getLogger("whisperlivekit.diarization.sortformer_backend").setLevel(logging.WARNING)

# 전역 변수
transcription_engine = None
tts_engine = None
SUPERTONIC_AVAILABLE = False

# TTS 엔진 로드
try:
    sys.path.append(os.path.join(os.path.dirname(__file__), "TTS", "supertonic2", "MIRAE", "laptop"))
    from tts_engine import TTSEngine
    from scipy.io import wavfile

    TTS_ONNX_DIR = os.path.join(os.path.dirname(__file__), "TTS", "supertonic2", "onnx")
    TTS_VOICE_STYLE = os.path.join(os.path.dirname(__file__), "TTS", "supertonic2", "voice_styles", "M1.json")
    TTS_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "TTS_output")
    os.makedirs(TTS_OUTPUT_DIR, exist_ok=True)

    SUPERTONIC_AVAILABLE = True
    print("Supertonic2 TTS 사용 가능")
except Exception as e:
    print(f"Supertonic2 로드 실패: {e}")
    print("TTS 기능이 비활성화됩니다")


def serialize_response(obj):
    """FrontData 객체를 JSON 직렬화 가능한 딕셔너리로 변환"""
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)
    elif isinstance(obj, dict):
        return {k: serialize_response(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_response(item) for item in obj]
    else:
        return obj


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 시 실행되는 lifespan"""
    global transcription_engine, tts_engine

    print("서버 초기화 중...")

    # GPU 사용 여부 확인
    if torch.cuda.is_available():
        print(f"GPU 감지: {torch.cuda.get_device_name(0)}")
        print(f"CUDA 버전: {torch.version.cuda}")
        print("GPU 모드로 실행됩니다")
    else:
        print("GPU 없음: CPU 모드로 실행됩니다")

    # STT 엔진 초기화
    print("\n[STT] WhisperLiveKit 초기화 중...")
    transcription_engine = TranscriptionEngine(
        model_size="small",
        lan="ko",
        diarization=True,
        diarization_backend="sortformer",
        target_language="",
        backend_policy="simulstreaming",
        backend="auto",
        vad=True,
        vac=True,
        frame_threshold=25,
        pcm_input=True,
    )
    print("[STT] 초기화 완료!")
    print("- 모델: small")
    print("- 언어: 한국어")
    print("- 화자 인식: 활성화 (Sortformer)")

    # TTS 엔진 초기화
    if SUPERTONIC_AVAILABLE:
        print("\n[TTS] Supertonic2 초기화 중...")
        try:
            tts_engine = TTSEngine(
                onnx_dir=TTS_ONNX_DIR,
                voice_style_path=TTS_VOICE_STYLE
            )
            print("[TTS] 초기화 완료!")
            print(f"- 샘플링 레이트: {tts_engine.sample_rate} Hz")
            print(f"- 음성 스타일: M1")
        except Exception as e:
            print(f"[TTS] 초기화 실패: {e}")
            tts_engine = None

    print("\n서버 준비 완료!")
    print("=" * 60)

    yield

    print("서버 종료 중...")


app = FastAPI(lifespan=lifespan)

HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>파이보 음성 인식 + TTS (Desktop GPU)</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }
        .container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 { text-align: center; color: #667eea; margin-bottom: 30px; }
        .status {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
            font-weight: bold;
        }
        .status.connected { background: #d4edda; color: #155724; }
        .status.disconnected { background: #f8d7da; color: #721c24; }
        .controls { text-align: center; margin: 30px 0; }
        button {
            padding: 15px 40px;
            font-size: 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            margin: 0 10px;
            transition: all 0.3s;
        }
        button.start { background: #28a745; color: white; }
        button.start:hover { background: #218838; }
        button.stop { background: #dc3545; color: white; }
        button.stop:hover { background: #c82333; }
        button:disabled { background: #6c757d; cursor: not-allowed; }
        #transcript {
            background: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            min-height: 300px;
            max-height: 500px;
            overflow-y: auto;
            margin-top: 20px;
        }
        .segment {
            margin-bottom: 15px;
            padding: 10px;
            border-left: 4px solid #667eea;
            background: white;
        }
        .speaker { font-weight: bold; color: #667eea; margin-bottom: 5px; }
        .speaker-1 { color: #667eea; }
        .speaker-2 { color: #f093fb; }
        .speaker-3 { color: #4facfe; }
        .text { color: #333; line-height: 1.6; }
        .buffer { color: #6c757d; font-style: italic; }
        .info {
            background: #e7f3ff;
            padding: 10px;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>파이보 STT + TTS 시스템</h1>
        <div id="status" class="status disconnected">연결 안 됨</div>
        <div class="controls">
            <button id="startBtn" class="start" onclick="startRecording()">녹음 시작</button>
            <button id="stopBtn" class="stop" onclick="stopRecording()" disabled>녹음 중지</button>
        </div>
        <div class="info">
            <strong>사용 방법:</strong><br>
            1. "녹음 시작" 버튼 클릭<br>
            2. 마이크 권한 허용<br>
            3. 말하기 시작<br>
            4. 실시간으로 텍스트가 표시됩니다 (화자 구분 포함)<br>
            5. TTS API: POST /tts (text: "안녕하세요")
        </div>
        <div id="transcript"></div>
    </div>
    <script>
        let ws = null;
        let mediaRecorder = null;
        let segments = {};

        async function startRecording() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                ws = new WebSocket(`ws://${window.location.host}/asr`);
                ws.onopen = () => {
                    document.getElementById('status').textContent = '연결됨 - 녹음 중';
                    document.getElementById('status').className = 'status connected';
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = false;
                };
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    handleTranscription(data);
                };
                ws.onerror = (error) => { console.error('WebSocket 오류:', error); };
                ws.onclose = () => {
                    document.getElementById('status').textContent = '연결 끊김';
                    document.getElementById('status').className = 'status disconnected';
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('stopBtn').disabled = true;
                };
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
                        ws.send(event.data);
                    }
                };
                mediaRecorder.start(100);
            } catch (err) {
                console.error('마이크 접근 오류:', err);
                alert('마이크 접근 권한이 필요합니다.');
            }
        }

        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state === 'recording') { mediaRecorder.stop(); }
            if (ws) { ws.close(); }
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
        }

        function handleTranscription(data) {
            if (data.type === 'transcript_update' && data.segments) {
                data.segments.forEach(segment => { segments[segment.id] = segment; });
                renderTranscript();
            }
        }

        function renderTranscript() {
            const transcriptDiv = document.getElementById('transcript');
            const sortedSegments = Object.values(segments).sort((a, b) => a.id - b.id);
            let html = '';
            sortedSegments.forEach(segment => {
                const speakerClass = `speaker-${(segment.speaker % 3) + 1}`;
                html += `
                    <div class="segment">
                        <div class="speaker ${speakerClass}">화자 ${segment.speaker}</div>
                        <div class="text">
                            ${segment.text || ''}
                            ${segment.buffer && segment.buffer.diarization ?
                                `<span class="buffer">${segment.buffer.diarization}</span>` : ''}
                        </div>
                    </div>
                `;
            });
            transcriptDiv.innerHTML = html || '<p style="color: #6c757d;">음성을 기다리는 중...</p>';
        }
    </script>
</body>
</html>
"""


@app.get("/")
async def get_index():
    return HTMLResponse(content=HTML_CONTENT)


@app.post("/tts")
async def text_to_speech(request: dict):
    """
    텍스트를 음성으로 변환하는 API

    요청 예시:
    {
        "text": "안녕하세요. 파이보입니다."
    }

    응답: WAV 오디오 파일
    """
    global tts_engine

    if not SUPERTONIC_AVAILABLE or tts_engine is None:
        return JSONResponse(
            status_code=503,
            content={"error": "TTS 엔진이 사용 불가능합니다"}
        )

    text = request.get("text", "")
    if not text:
        return JSONResponse(
            status_code=400,
            content={"error": "텍스트가 비어있습니다"}
        )

    try:
        # 고유한 파일명 생성
        import time
        filename = f"tts_{int(time.time() * 1000)}.wav"
        output_path = os.path.join(TTS_OUTPUT_DIR, filename)

        # TTS 생성
        print(f"[TTS] 음성 생성 중: {text[:50]}...")
        for wav, idx in tts_engine.synthesize_streaming(text):
            # 첫 번째 청크 저장 (전체 텍스트)
            wavfile.write(output_path, tts_engine.sample_rate, wav)
            print(f"[TTS] 음성 저장 완료: {output_path}")
            break

        # 파일 반환
        return FileResponse(
            output_path,
            media_type="audio/wav",
            filename=filename
        )

    except Exception as e:
        print(f"[TTS] 오류: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"TTS 생성 실패: {str(e)}"}
        )


async def handle_websocket_results(websocket: WebSocket, results_generator, connection_active):
    """WebSocket으로 결과 전송"""
    try:
        async for response in results_generator:
            if not connection_active[0]:
                break
            serialized = serialize_response(response)
            try:
                await websocket.send_json(serialized)
            except:
                break
        if connection_active[0]:
            try:
                await websocket.send_json({"type": "ready_to_stop"})
            except:
                pass
    except Exception as e:
        print(f"결과 전송 오류: {e}")


@app.websocket("/asr")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 엔드포인트 - STT"""
    global transcription_engine

    await websocket.accept()
    print(f"\n[STT] 새 클라이언트 연결: {websocket.client}")

    audio_processor = AudioProcessor(transcription_engine=transcription_engine)
    connection_active = [True]

    try:
        results_generator = await audio_processor.create_tasks()
        results_task = asyncio.create_task(
            handle_websocket_results(websocket, results_generator, connection_active)
        )

        while True:
            try:
                message = await websocket.receive_bytes()
                await audio_processor.process_audio(message)
            except WebSocketDisconnect:
                print(f"[STT] 클라이언트 연결 종료: {websocket.client}")
                connection_active[0] = False
                break
            except Exception as e:
                print(f"[STT] 오디오 처리 오류: {e}")
                connection_active[0] = False
                break

    except Exception as e:
        print(f"[STT] WebSocket 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"[STT] 클라이언트 정리: {websocket.client}")


if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 60)
    print("WhisperLiveKit STT + Supertonic2 TTS 서버 (Desktop GPU)")
    print("=" * 60)
    print("서버 주소: http://0.0.0.0:9090")
    print("웹 UI: http://localhost:9090")
    print("STT WebSocket: ws://localhost:9090/asr")
    print("TTS API: POST http://localhost:9090/tts")
    print("\nngrok으로 외부 접속:")
    print("  ngrok http 9090")
    print("=" * 60)
    print("\n서버 시작 중...\n")

    uvicorn.run(app, host="0.0.0.0", port=9090, log_level="info")
