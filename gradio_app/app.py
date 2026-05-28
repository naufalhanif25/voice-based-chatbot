import os
import tempfile
import requests
import gradio as gr
import scipy.io.wavfile
from typing import Any

API_URL = "http://localhost:8000/voice-chat"
RESPONSE_TIMEOUT = 3 * 60

def _voice_chat(audio: Any, mode: str, chat_history: list) -> tuple[list, str | None]:
    if audio is None:
        return chat_history, None
    
    sr, audio_data = audio
    
    with tempfile.NamedTemporaryFile(delete = False, suffix = ".wav") as tmpfile:
        scipy.io.wavfile.write(tmpfile.name, sr, audio_data)
        audio_path = tmpfile.name
        
    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
            
        files = {"file": ("voice.wav", audio_bytes, "audio/wav")}
        payload = {"mode": mode}
        response = requests.post(API_URL, files = files, data = payload, timeout = RESPONSE_TIMEOUT)
        
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
    except Exception as e:
        chat_history.append({"role": "user", "content": "[INFO] Sent Voice Query"})
        chat_history.append({"role": "assistant", "content": f"[ERROR] {str(e)}"})
        
        return chat_history, None

    if response.status_code == 200:
        output_audio_path = os.path.join(tempfile.gettempdir(), f"tts_out_{os.getpid()}.wav")

        with open(output_audio_path, "wb") as f:
            f.write(response.content)

        chat_history.append({"role": "user", "content": "[INFO] Sent Voice Query"})
        chat_history.append({"role": "assistant", "content": "Voice response successfully created! Please listen to it on the audio player below."})

        return chat_history, output_audio_path
    else:
        chat_history.append({"role": "user", "content": "[INFO] Sent Voice Query"})
        chat_history.append({"role": "assistant", "content": f"[ERROR] Backend Server returns Error {response.status_code}"})

        return chat_history, None

def _clear_interface():
    return None, "normalize", [], None

with gr.Blocks(theme = gr.themes.Soft(primary_hue = "teal", secondary_hue = "slate")) as demo:
    gr.Markdown("# Voice-Based Chatbot")
    gr.Markdown("Speak directly into the microphone and get voice answer from the AI assistant.")

    with gr.Row(equal_height = True):
        with gr.Column(scale = 2):
            gr.Markdown("### User Input Panel")
            
            with gr.Row():
                audio_input = gr.Audio(sources = "microphone", type = "numpy", label = "Record Your Question")
                mode_input = gr.Dropdown(
                    choices = ["normalize", "preserve"],
                    value = "normalize",
                    label = "Response Mode"
                )
                
            with gr.Row():
                clear_btn = gr.Button("Clean", variant = "secondary")
                submit_btn = gr.Button("Send", variant = "primary")

    with gr.Column(scale = 3):
        gr.Markdown("### Activity Monitor & AI Reply")
        
        chat_history_view = gr.Chatbot(
            label = "Chat History", 
            type = "messages"
        )
        
        audio_output = gr.Audio(
            type = "filepath", 
            label = "AI Answer Voice Player", 
            interactive = False,
            autoplay = True
        )

    submit_btn.click(
        fn = _voice_chat,
        inputs = [audio_input, mode_input, chat_history_view],
        outputs = [chat_history_view, audio_output],
        show_progress = "full"
    )

    clear_btn.click(
        fn = _clear_interface,
        inputs = [],
        outputs = [audio_input, mode_input, chat_history_view, audio_output]
    )

if __name__ == "__main__":
    demo.launch(share = False)
