import os
import uuid
import tempfile
import subprocess
from app.utils import generate_log

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COQUI_DIR = os.path.join(BASE_DIR, "coqui_tts")
COQUI_MODEL_PATH = os.path.join(COQUI_DIR, "checkpoint_1260000-inference.pth")
COQUI_CONFIG_PATH = os.path.join(COQUI_DIR, "config.json")
COQUI_SPEAKER = "wibowo"

def transcribe_text_to_speech(text: str) -> str:
    path = _tts_with_coqui(text)
    return path

def _tts_with_coqui(text: str) -> str:
    tmp_dir = tempfile.gettempdir()
    output_path = os.path.join(tmp_dir, f"tts_{uuid.uuid4()}.wav")
    
    cmd = [
        "tts",
        "--text", text,
        "--model_path", COQUI_MODEL_PATH,
        "--config_path", COQUI_CONFIG_PATH,
        "--speaker_idx", COQUI_SPEAKER,
        "--out_path", output_path
    ]
    
    try:
        subprocess.run(cmd, check = True)
    except subprocess.CalledProcessError as e:
        log_message = f"[ERROR] TTS subprocess failed: {e}"
        print(log_message)
        generate_log(log_message)

        log_message = "[ERROR] Failed to synthesize speech"
        generate_log(log_message)
        
        return log_message
    return output_path
