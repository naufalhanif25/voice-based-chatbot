import os
import uuid
import re
import tempfile
import json
import subprocess
from app.utils import generate_log, read_json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COQUI_DIR = os.path.join(BASE_DIR, "coqui_tts")
COQUI_MODEL_PATH = os.path.join(COQUI_DIR, "checkpoint_1260000-inference.pth")
COQUI_CONFIG_PATH = os.path.join(COQUI_DIR, "config.json")
COQUI_SPEAKERS_PATH = os.path.join(COQUI_DIR, "speakers.pth")
TRANSCRIPTS_DIR = os.path.join(BASE_DIR, "..", "data", "corpus", "transcripts")
COQUI_SPEAKER = "wibowo"

ALPHABET_PHONETIC = read_json(os.path.join(TRANSCRIPTS_DIR, "alpha_phonetic.json"))
NUMERIC_PHONETIC = read_json(os.path.join(TRANSCRIPTS_DIR, "num_phonetic.json"))
ENGLISH_PHONETIC_MAP = read_json(os.path.join(TRANSCRIPTS_DIR, "english_phonetic.json"))
PHONEME_MAP = read_json(os.path.join(TRANSCRIPTS_DIR, "phoneme.json"))

def _preprocess_acronyms_and_numbers(text: str) -> str:
    def expand_match(match):
        token = match.group(0)
        expanded = []
        
        for char in token:
            char_lower = char.lower()
            
            if char_lower in ALPHABET_PHONETIC:
                expanded.append(ALPHABET_PHONETIC[char_lower])
            elif char_lower in NUMERIC_PHONETIC:
                expanded.append(NUMERIC_PHONETIC[char_lower])
            else:
                expanded.append(char)
        return " " + " ".join(expanded) + " "

    text = re.sub(r"\b[A-Z0-9]{2,}\b", expand_match, text)
    
    return text

def _normalize_articulation(text: str) -> str:
    text = re.sub(r'[\*\_\~\"\']', '', text)
    text = text.lower()
    text = re.sub(r'\b(meng|peng)([aeiou])', r'\1-\2', text)
    text = re.sub(r"d\b", "t", text)
    text = re.sub(r"b\b", "p", text)
    text = re.sub(r"g\b", "k", text)
    text = re.sub(r"v", "f", text)
    text = re.sub(r"tion\b", "syen", text)
    text = text.replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip()
    
    return text

def _apply_english_phonetics(text: str) -> str:
    words = text.split()
    transformed_words = []
    
    for word in words:
        clean_word = re.sub(r"[^\w\-]", "", word)
        punctuation = re.sub(r"[\w\-]", "", word)
        
        if clean_word in ENGLISH_PHONETIC_MAP:
            replaced = ENGLISH_PHONETIC_MAP[clean_word]
            transformed_words.append(f"{replaced}{punctuation}")
        else:
            transformed_words.append(word)
            
    return " ".join(transformed_words)

def _grapheme_to_phoneme(text: str) -> str:
    sorted_keys = sorted(PHONEME_MAP.keys(), key = len, reverse = True)
    pattern = re.compile('|'.join(sorted_keys))

    words = text.split()
    result = []

    for word in words:
        clean = re.sub(r'[^\w]', '', word.lower())
        punctuation = re.sub(r'[\w]', '', word)

        if not clean:
            result.append(word)
            continue

        phonemic_word = pattern.sub(lambda match: PHONEME_MAP[match.group()], clean)
        result.append(phonemic_word + punctuation)

    return ' '.join(result)

def transcribe_text_to_speech(text: str) -> str:
    if not text or "[ERROR]" in text:
        return "[ERROR] Invalid text input for speech synthesis"

    processed_text = _preprocess_acronyms_and_numbers(text)
    processed_text = _apply_english_phonetics(processed_text)
    normalized_text = _normalize_articulation(processed_text)
    final_phonemic_text = _grapheme_to_phoneme(normalized_text)
        
    print(f"[INFO] TTS Input Normalized: \"{final_phonemic_text}\"")
    
    path = _tts_with_coqui(final_phonemic_text)
    
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
        "--speakers_file_path", COQUI_SPEAKERS_PATH,
        "--out_path", output_path
    ]
    
    try:
        subprocess.run(cmd, check = True, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        log_message = f"[ERROR] TTS subprocess failed: {e}"
        print(log_message)
        generate_log(log_message)

        log_message = "[ERROR] Failed to synthesize speech"
        generate_log(log_message)
        
        return log_message
    return output_path
