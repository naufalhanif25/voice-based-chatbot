import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse
from typing import Any
from app.stt import transcribe_speech_to_text
from app.tts import transcribe_text_to_speech
from app.llm import generate_response

app = FastAPI()

@app.post("/voice-chat")
async def voice_chat(file: UploadFile = File(...)) -> Any:
    file_bytes = await file.read()
    file_ext = os.path.splitext(file.filename)[-1] or ".wav"
    
    transcript = transcribe_speech_to_text(file_bytes, file_ext)
    
    if "[ERROR]" in transcript:
        raise HTTPException(status_code = 500, detail = transcript)
        
    response_text = generate_response(transcript)
    
    if "[ERROR]" in response_text:
        raise HTTPException(status_code = 500, detail = response_text)
        
    audio_path = transcribe_text_to_speech(response_text)
    
    if "[ERROR]" in audio_path:
        raise HTTPException(status_code = 500, detail = audio_path)

    if not os.path.exists(audio_path):
        raise HTTPException(status_code = 500, detail = "[ERROR] Audio file missing before response generation")

    return FileResponse(audio_path, media_type = "audio/wav", filename = "response.wav")