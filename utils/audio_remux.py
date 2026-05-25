import subprocess
import tempfile
import os
from app.utils import generate_log

def remux_audio(input_path: str) -> bytes | None:
    try:
        with tempfile.NamedTemporaryFile(suffix = ".wav", delete = False) as tmp_file:
            tmp_output_path = tmp_file.name
            
        cmd = [
            "ffmpeg", 
            "-y", 
            "-i", input_path, 
            "-ar", "16000",
            "-ac", "1", 
            "-c:a", "pcm_s16le",
            tmp_output_path
        ]
        
        result = subprocess.run(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE, text = True)
        
        if result.returncode != 0:
            generate_log(f"[ERROR] FFmpeg failed: {result.stderr}")
            return None
            
        with open(tmp_output_path, "rb") as f:
            remuxed_bytes = f.read()
            
        os.remove(tmp_output_path)

        return remuxed_bytes
    except Exception as e:
        generate_log(f"[ERROR] {str(e)}")
        return None