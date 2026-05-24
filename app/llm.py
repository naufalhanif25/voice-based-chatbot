import os
from google import genai
from google.genai import types
from pydantic import TypeAdapter
from dotenv import load_dotenv
from app.utils import generate_log, read_instruction
from typing import Any

load_dotenv()

MODEL = os.getenv("GEMINI_MODEL")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHAT_HISTORY_FILE = os.path.join(BASE_DIR, "..", "data", "history", "chat_history.json")
PROMPT_DIR = os.path.join(BASE_DIR, "..", "data", "prompts")

instruction = read_instruction(os.path.join(PROMPT_DIR, "instruction.md"))
client = genai.Client(api_key = GOOGLE_API_KEY)
history_adapter = TypeAdapter(list[types.Content])

def export_chat_history(chat) -> str:
    return history_adapter.dump_json(chat.get_history()).decode("utf-8")

def save_chat_history(chat) -> None:
    json_history = export_chat_history(chat)
    
    with open(CHAT_HISTORY_FILE, "w", encoding = "utf-8") as f:
        f.write(json_history)

def load_chat_history(config: str) -> Any:
    if not os.path.exists(CHAT_HISTORY_FILE):
        return client.chats.create(model = MODEL, config = config)
    
    if os.path.getsize(CHAT_HISTORY_FILE) == 0:
        return client.chats.create(model = MODEL, config = config)

    with open(CHAT_HISTORY_FILE, "r", encoding = "utf-8") as f:
        json_str = f.read().strip()

    if not json_str:
        return client.chats.create(model = MODEL, config = config)

    try:
        history = history_adapter.validate_json(json_str)
        
        return client.chats.create(model = MODEL, config = config, history = history)
    except Exception as e:
        log_message = f"[ERROR] Failed to load chat history: {e}"
        print(log_message)
        generate_log(log_message)
        
        return client.chats.create(model = MODEL, config = config)
        
def generate_response(prompt: str) -> str:
    config = types.GenerateContentConfig(system_instruction = instruction)

    try:
        chat = load_chat_history(config)
        response = chat.send_message(prompt)
        save_chat_history(chat)
        
        return response.text.strip()
    except Exception as e:
        log_message = f"[ERROR] {str(e)}"
        generate_log(log_message)
        
        return log_message
