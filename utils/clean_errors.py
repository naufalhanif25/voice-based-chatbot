import os
import json
import re
from typing import Any

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHECKPOINT_FILE = os.path.join(BASE_DIR, "..", "data", "results", "checkpoint.json")
CHAT_HISTORY_FILE = os.path.join(BASE_DIR, "..", "data", "history", "chat_history.json")

def _open_file(file_path: str) -> Any | None:
    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding = "utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"[ERROR] File is corrupted or invalid: {CHECKPOINT_FILE}")
            return None

def clean_error_responses():
    results = _open_file(CHECKPOINT_FILE)
    if results is None:
        return

    chat_histories = _open_file(CHAT_HISTORY_FILE) or []
    
    initial_count = len(results)
    cleaned_results, removed_items = list(), list()
    indices_to_remove = set()
        
    for i, item in enumerate(results):
        filename = item.get("filename") or ""
        utter_id = item.get("utter_id") or ""
        reference = item.get("reference") or ""
        is_failed = item.get("is_failed") or False
        is_error = False
        
        if is_failed or not utter_id or not reference:
            is_error = True
            
        has_parentheses_duplicate = False
        if re.search(r"\(\d+\)", filename) or re.search(r"\(\d+\)", utter_id):
            has_parentheses_duplicate = True

        reason = None
        if is_error or has_parentheses_duplicate:
            if is_error:
                reason = "API/Subprocess Error"
            elif has_parentheses_duplicate:
                reason = "Parentheses Duplicate File (...)"
                
            item["reason"] = reason
            removed_items.append(item)
            indices_to_remove.add(i)
        else:
            cleaned_results.append(item)

    final_count = len(cleaned_results)
    removed_count = initial_count - final_count
    
    if removed_count > 0:
        print(f"[INFO] Deleting {removed_count} out of {initial_count} entries")
        
        for item in removed_items:
            filename = item.get("filename", "Unknown")
            reason = item.get("reason", "Unknown")
            
            print(f"[REMOVED] File: {filename} | Reason: {reason}")

        cleaned_history = [turn for j, turn in enumerate(chat_histories) if j not in indices_to_remove]
        
        with open(CHECKPOINT_FILE, "w", encoding = "utf-8") as f:
            json.dump(cleaned_results, f, ensure_ascii = False, indent = 4)
        
        with open(CHAT_HISTORY_FILE, "w", encoding = "utf-8") as f:
            json.dump(cleaned_history, f, ensure_ascii = False)

        print(f"[SUCCESS] File successfully saved: {CHECKPOINT_FILE}, {CHAT_HISTORY_FILE}")
    else:
        print("[INFO] No error response found")

if __name__ == "__main__":
    clean_error_responses()