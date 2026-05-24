import os
import json
import time
import re
from datetime import datetime
from jiwer import wer, cer
from typing import Any
from app.stt import transcribe_speech_to_text
from app.llm import generate_response
from app.tts import transcribe_text_to_speech
from app.utils import generate_log

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "data", "corpus", "audio")
REFERENCE_FILE = os.path.join(BASE_DIR, "data", "corpus", "transcripts", "reference.json")
RESULTS_DIR = os.path.join(BASE_DIR, "data", "results")
CHECKPOINT_FILE = os.path.join(RESULTS_DIR, "checkpoint.json")

os.makedirs(RESULTS_DIR, exist_ok = True)

def load_checkpoint() -> Any:
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r", encoding = "utf-8") as f:
            return json.load(f)
    return []

def save_checkpoint(results) -> None:
    with open(CHECKPOINT_FILE, "w", encoding = "utf-8") as f:
        json.dump(results, f, ensure_ascii = False, indent = 4)    

def load_reference() -> Any:
    with open(REFERENCE_FILE, "r", encoding = "utf-8") as f:
        return json.load(f)

def get_utter_id(filename) -> str | None:
    match = re.search(r"audio(\d+)", filename.lower())
    
    if match:
        raw_number = match.group(1)
        number = raw_number.lstrip("0") or "0"
        return f"audio{number}"
        
    return None

def run_pipeline(audio_path) -> dict[str, Any]:
    with open(audio_path, "rb") as f:
        file_bytes = f.read()
        
    t0 = time.time()
    transcript = transcribe_speech_to_text(file_bytes, ".wav")
    stt_lat = time.time() - t0

    max_retries = 3
    base_delay = 2
    response_text = ""
    llm_lat = 0.0
    
    for attempt in range(max_retries):
        t1 = time.time()
        
        try:
            response_text = generate_response(transcript)
            llm_lat = time.time() - t1
            
            if "[ERROR]" not in response_text and "500" not in response_text:
                break
        except Exception as api_err:
            response_text = f"[ERROR] Subprocess/API exception: {str(api_err)}"
            llm_lat = time.time() - t1

        if attempt < max_retries - 1:
            wait_time = base_delay * (2 ** attempt)
            print(f"  [WARN] LLM Server Error (500). Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(wait_time)

    if "[ERROR]" in response_text or "500" in response_text:
        print("  [SKIP] LLM error persisted after retries, skipping TTS synthesis.")
        total_lat = time.time() - t0
        
        return {
            "transcript": transcript.strip(),
            "response": response_text,
            "audio_out": None,
            "stt_lat": round(stt_lat, 2),
            "llm_lat": round(llm_lat, 2),
            "tts_lat": 0.0,
            "total_lat": round(total_lat, 2),
            "is_failed": True
        }
    
    t2 = time.time()
    audio_out = transcribe_text_to_speech(response_text)
    tts_lat = time.time() - t2

    total_lat = time.time() - t0

    return {
        "transcript": transcript.strip(),
        "response": response_text,
        "audio_out": audio_out,
        "stt_lat": round(stt_lat, 2),
        "llm_lat": round(llm_lat, 2),
        "tts_lat": round(tts_lat, 2),
        "total_lat": round(total_lat, 2),
        "is_failed": False
    }

def main() -> None:
    reference = load_reference()
    raw_audio_files = sorted([f for f in os.listdir(AUDIO_DIR) if f.endswith(".wav")])
    audio_files = []
    
    for f in raw_audio_files:
        if re.search(r"\(\d+\)", f):
            print(f"[SKIP] Duplicate file skipped: {f}")
            continue
            
        audio_files.append(f)

    results = load_checkpoint()
    processed = set((r["filename"]) for r in results if "error" not in r or r.get("transcript"))

    total_audio = len(audio_files)
    wer_scores, cer_scores = list(), list()

    print(f"[Total audio files: {total_audio}]")

    for i, filename in enumerate(audio_files):
        audio_path = os.path.join(AUDIO_DIR, filename)
        utter_id = get_utter_id(filename)
        ref_text = reference.get(utter_id, None)

        print("\n", end = None) if i > 0 else None
        print(f"Index        : {i + 1}/{total_audio}")
        print(f"Processing   : {filename}")
        print(f"Utterance ID : {utter_id}")
        print(f"Reference    : {ref_text}")
        
        if(filename) in processed:
            print(f"[SKIP] File: {filename} (already processed)")
            continue

        print("\n", end = None) if j > 0 else None
        print(f"  File: {filename}")

        try:
            result = run_pipeline(audio_path)
            transcript = result["transcript"]
            
            print(f"  Transcript : {transcript}")
            print(f"  Response   : {result['response']}")
            print(f"  STT lat.   : {result['stt_lat']}s")
            print(f"  LLM lat.   : {result['llm_lat']}s")
            print(f"  TTS lat.   : {result['tts_lat']}s")
            print(f"  Total lat. : {result['total_lat']}s")
            print(f"  Is Failed  : {result['is_failed']}")

            if ref_text:
                word_error = wer(ref_text.lower(), transcript.lower())
                char_error = cer(ref_text.lower(), transcript.lower())
                
                print(f"  WER: {round(word_error, 4)}")
                print(f"  CER: {round(char_error, 4)}")

                wer_scores.append(word_error)
                cer_scores.append(char_error)
            else:
                word_error, char_error = None, None
                log_message = f"[WARN] WER/CER: No reference found for {utter_id}"

                generate_log(log_message)
                print(f"  {log_message}")

            results.append({
                "filename": filename,
                "utter_id": utter_id,
                "reference": ref_text,
                "transcript": transcript,
                "response": result["response"],
                "audio_out": result["audio_out"],
                "wer": round(word_error, 4) if word_error is not None else None,
                "cer": round(char_error, 4) if char_error is not None else None,
                "stt_lat": result["stt_lat"],
                "llm_lat": result["llm_lat"],
                "tts_lat": result["tts_lat"],
                "total_lat": result["total_lat"],
                "is_failed": result["is_failed"]
            })
            
        except Exception as e:
            log_message = f"[ERROR] {e}"

            generate_log(log_message)
            print(f"  {log_message}")
            
            results.append({
                "filename": filename,
                "utter_id": utter_id,
                "error": str(e),
                "is_failed": True
            })

        save_checkpoint(results)
                
    print("\n", end = "[Summary]")
    avg_wer, avg_cer, avg_lat = None, None, None
    
    if wer_scores:
        avg_wer = round(sum(wer_scores) / len(wer_scores), 4)
        avg_cer = round(sum(cer_scores) / len(cer_scores), 4)
        
        print(f"Avg. WER: {avg_wer}")
        print(f"Avg. CER: {avg_cer}")

    latencies = [r["total_lat"] for r in results if "total_lat" in r]
    
    if latencies:
        avg_lat = round(sum(latencies) / len(latencies), 2)
        print(f"Avg. total lat.: {avg_lat}s")
        
    output_file = os.path.join(RESULTS_DIR, f"pipeline_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    with open(output_file, "w", encoding = "utf-8") as f:
        json.dump({
            "summary": {
                "total_files": len(audio_files),
                "avg_wer": avg_wer if wer_scores else None,
                "avg_cer": avg_cer if wer_scores else None,
                "avg_lat": avg_lat if latencies else None
            },
            "results": results
        }, f, ensure_ascii = False, indent = 4)

    print("\n", end = f"Results saved to: {output_file}")

if __name__ == "__main__":
    main()