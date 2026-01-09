# WhisperLiveKit 기반 갤럭시북 STT 서버 (화자 인식 포함)
# pip install whisperlivekit
# pip install git+https://github.com/NVIDIA/NeMo.git@main#egg=nemo_toolkit[asr]

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from whisperlivekit import AudioProcessor, TranscriptionEngine
from dataclasses import asdict, is_dataclass

# 전역 TranscriptionEngine (싱글톤)
transcription_engine = None


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
    global transcription_engine

    print("WhisperLiveKit 서버 초기화 중...")

    # TranscriptionEngine 생성 (싱글톤)
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
        pcm_input=True,  # raw PCM 입력 사용 (FFmpeg 바이패스)
    )

    print("TranscriptionEngine 초기화 완료!")
    print("- 모델: small")
    print("- 언어: 한국어")
    print("- 화자 인식: 활성화 (Sortformer)")
    print("- 백엔드 정책: SimulStreaming")

    yield

    print("서버 종료 중...")


app = FastAPI(lifespan=lifespan)

HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>파이보 음성 인식 (WhisperLiveKit)</title>
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
        <h1>파이보 음성 인식 시스템</h1>
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
            4. 실시간으로 텍스트가 표시됩니다 (화자 구분 포함)
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


async def handle_websocket_results(websocket: WebSocket, results_generator, connection_active):
    """WebSocket으로 결과 전송"""
    try:
        async for response in results_generator:
            if not connection_active[0]:
                break
            # FrontData를 딕셔너리로 변환
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
    """WebSocket 엔드포인트"""
    global transcription_engine

    await websocket.accept()
    print(f"\n새 클라이언트 연결: {websocket.client}")

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
                print(f"클라이언트 연결 종료: {websocket.client}")
                connection_active[0] = False
                break
            except Exception as e:
                print(f"오디오 처리 오류: {e}")
                connection_active[0] = False
                break

    except Exception as e:
        print(f"WebSocket 오류: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"클라이언트 정리: {websocket.client}")


if __name__ == "__main__":
    import uvicorn

    print("\nWhisperLiveKit 기반 파이보 STT 서버")
    print("서버 주소: http://0.0.0.0:9090")
    print("웹 UI: http://localhost:9090")
    print("WebSocket: ws://localhost:9090/asr")
    print("\n서버 시작 중...\n")

    uvicorn.run(app, host="0.0.0.0", port=9090, log_level="info")
