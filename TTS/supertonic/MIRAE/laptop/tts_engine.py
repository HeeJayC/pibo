# tts_engine.py
import os
import uuid
import numpy as np
from scipy.io import wavfile
import time
import re

from helper import (
    load_text_to_speech,
    load_voice_style,
)

class TTSEngine:
    def __init__(
        self,
        onnx_dir: str,
        voice_style_path: str,
        lang: str = "ko"
    ):
        """
        TTS 엔진 초기화 (모델은 1번만 로딩)
        """
        self.lang = lang
        self.tts = load_text_to_speech(onnx_dir, use_gpu=False)
        self.voice_style = load_voice_style([voice_style_path])
        self.sample_rate = self.tts.sample_rate

    def synthesize(
        self,
        text: str,
        output_path: str,
        speed: float = 1.05,
        total_step: int = 5
    ):
        """
        텍스트 → wav 파일 생성 (전체 텍스트 한번에)
        """
        wav, _ = self.tts(
            text=text,
            lang=self.lang,
            style=self.voice_style,
            total_step=total_step,
            speed=speed
        )
        
        final_wav = wav.squeeze()
        wavfile.write(output_path, self.sample_rate, final_wav)
        return output_path

    def synthesize_streaming(
        self,
        text: str,
        speed: float = 1.2,
        total_step: int = 5,
        min_chunk_length: int = 50  # 최소 청크 길이 (글자 수)
    ):
        """
        텍스트를 문장 단위로 나눠서 스트리밍 생성 (Generator)
        """
        # 문장 분리 및 병합
        sentences = self._split_and_merge_sentences(text, min_chunk_length)
        
        for i, sentence in enumerate(sentences, 1):
            if not sentence.strip():
                continue
            
            # 로그 출력 (50자로 제한하되 말줄임표 추가)
            display_text = sentence if len(sentence) <= 70 else sentence[:70] + "..."
            print(f"🎤 [{i}/{len(sentences)}] 생성 중: {display_text}")
            
            start_time = time.time()
            wav, _ = self.tts(
                text=sentence,
                lang=self.lang,
                style=self.voice_style,
                total_step=total_step,
                speed=speed
            )
            elapsed = time.time() - start_time
            
            final_wav = wav.squeeze()
            print(f"   ✅ 완료 ({elapsed:.2f}초, {len(sentence)}자)")
            
            yield final_wav, i

    def _split_and_merge_sentences(self, text: str, min_length: int = 30):
        """
        텍스트를 문장 단위로 분리하고, 짧은 문장은 병합
        """
        # 1단계: 기본 문장 분리 (온점, 느낌표, 물음표 기준)
        sentences = re.split(r'([.!?]\s*)', text)
        
        # 2단계: 구두점과 텍스트 다시 합치기
        raw_sentences = []
        for i in range(0, len(sentences)-1, 2):
            sentence = sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '')
            if sentence.strip():
                raw_sentences.append(sentence.strip())
        
        # 마지막 문장 처리
        if len(sentences) % 2 == 1 and sentences[-1].strip():
            raw_sentences.append(sentences[-1].strip())
        
        # 3단계: 짧은 문장 병합
        merged_sentences = []
        buffer = ""
        
        for sentence in raw_sentences:
            # 버퍼에 추가
            if buffer:
                buffer += " " + sentence
            else:
                buffer = sentence
            
            # 최소 길이 이상이면 청크로 확정
            if len(buffer) >= min_length:
                merged_sentences.append(buffer)
                buffer = ""
        
        # 남은 버퍼 처리
        if buffer:
            if merged_sentences:
                # 이전 문장에 합치기
                merged_sentences[-1] += " " + buffer
            else:
                # 버퍼만 있는 경우
                merged_sentences.append(buffer)
        
        return merged_sentences

    def synthesize_temp(self, text: str) -> str:
        """
        임시 wav 파일 생성 (API 용)
        """
        import tempfile
        filename = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.wav")
        return self.synthesize(text, filename)