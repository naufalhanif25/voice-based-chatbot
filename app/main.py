import os
import tempfile
import time
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import Any
from app.stt import transcribe_speech_to_text
from app.tts import transcribe_text_to_speech
from app.llm import generate_response
from app.utils import generate_log
from utils.audio_remux import remux_audio

app = FastAPI()

@app.post("/voice-chat")
async def voice_chat(file: UploadFile = File(...)) -> Any:
    file_bytes = await file.read()
    file_ext = os.path.splitext(file.filename)[-1] or ".wav"
    
    transcript = transcribe_speech_to_text(file_bytes, file_ext)
    
    if "[ERROR]" in transcript:
        generate_log(f"[WARN] STT Error detected in production endpoint. Attempting FFmpeg remux for: {file.filename}")
        
        with tempfile.NamedTemporaryFile(delete = False, suffix = file_ext) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name
            
        try:
            remuxed_bytes = remux_audio(temp_path)
            
            if remuxed_bytes:
                new_transcript = transcribe_speech_to_text(remuxed_bytes, ".wav")
                
                if "[ERROR]" not in new_transcript:
                    generate_log(f"[SUCCESS] Production remux successful for {file.filename}")
                    transcript = new_transcript
                else:
                    transcript = "[ERROR] STT failed even after FFmpeg remux"
            else:
                transcript = "[ERROR] STT failed and FFmpeg remuxing system collapsed"
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    if "[ERROR]" in transcript:
        raise HTTPException(status_code = 500, detail = transcript)
        
    max_retries = 3
    base_delay = 2
    response_text = ""
    
    for attempt in range(max_retries):
        try:
            response_text = generate_response(transcript)
            
            if "[ERROR]" not in response_text and "500" not in response_text:
                break
        except Exception as api_err:
            response_text = f"[ERROR] Subprocess/API exception: {str(api_err)}"
            
        if attempt < max_retries - 1:
            wait_time = base_delay * (2 ** attempt)
            generate_log(f"[WARN] LLM Server Error in production. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_time)
            
    if "[ERROR]" in response_text or "500" in response_text:
        raise HTTPException(status_code = 500, detail = f"LLM failed after {max_retries} retries")
        
    audio_path = transcribe_text_to_speech(response_text)
    
    if "[ERROR]" in audio_path:
        raise HTTPException(status_code = 500, detail = audio_path)

    if not os.path.exists(audio_path):
        raise HTTPException(status_code = 500, detail = "[ERROR] Audio file missing before response generation")

    return FileResponse(audio_path, media_type = "audio/wav", filename = "response.wav")