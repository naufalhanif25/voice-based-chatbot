# Voice Chatbot Pipeline – STT, Gemini LLM, TTS Integration and Evaluation

## Project Description
This project is an integrated, AI-powered Voice Chatbot system that combines Speech-to-Text (STT), Large Language Model (LLM), and Text-to-Speech (TTS) components. In addition to providing an interactive web-based interface, the project is equipped with an automated performance testing subsystem (pipeline analysis) to measure transcription accuracy using Word Error Rate (WER) and Character Error Rate (CER) metrics, as well as to track processing latency for each supporting component.

---

## Chatbot Response Modes: Normalize vs Preserve
The system supports two distinct linguistic processing modes for the Gemini LLM, controlled via system instructions located in `data/prompts/`. Both modes strictly enforce a **maximum length of 25 words (1–2 sentences)** and completely ban the use of bullet points, numbered lists, or markdown symbols to ensure seamless Text-to-Speech (TTS) synthesis.

### 1. Normalize Mode (`normalize.md`)
* **Objective:** Standardizes the conversation into clean, formal, and structured Indonesian.
* **Mechanism:** Any foreign loanwords, slang, English terms, or code-switching expressions used by the user are automatically translated or normalized into standard Indonesian equivalents before being passed to the TTS engine.
* **Ideal Use Case:** Formal virtual assistants, official announcements, or environments where standard language consistency is mandatory.

### 2. Preserve Mode (`preserve.md`)
* **Objective:** Maintains a natural, conversational, and multilingual flow.
* **Mechanism:** Relies on contextual code-switching. It preserves and adapts relevant foreign technical terms, colloquial phrases, or specific loanwords used by the user (e.g., *booking, flight, schedule*) if it makes the spoken explanation sound more natural and intuitive.
* **Ideal Use Case:** Daily casual interaction, tech-savvy environments, or dual-language operational contexts.

---

## System Workflow and Operations
This system operates through a chained processing cycle (pipeline) from audio input to audio output with the following workflow:

```
[Audio Input] ──> [STT: whisper.cpp] ──> [LLM: Gemini API] ──> [TTS: Coqui TTS] ──> [Audio Output]
      │                          │
(FFmpeg Remux Fallback)   (Thought Masking)
```

1. **Audio Input:** The user records voice via a microphone on the Gradio interface or sends a `.wav` audio file through the API endpoint.
2. **Speech-to-Text (STT):** The audio file is fed into the `whisper.cpp` CLI binary using the `ggml-large-v3-turbo` model to be converted into transcript text.
3. **FFmpeg Remux Mechanism (Fallback):** If Whisper detects an error in the raw audio structure, the system triggers a recovery function by calling FFmpeg externally to modify the audio parameters to mono, 16000Hz sampling rate, `pcm_s16le` codec, and performs the transcription again.
4. **LLM Processing & Thought Masking:** The transcript text is processed by the Google Gemini API using the modern `google-genai` SDK. To support advanced reasoning models (e.g., Gemini 2.0 Flash Thinking), the system implements an **Anti-Leakage Thought Block Masking** routine. This routine strips out the internal reasoning tokens (`thought: true` parts) before returning the text to the Gradio UI or exporting histories, preventing long analytical text chains from ruining the chat interface or breaking the TTS execution.
5. **Modern Multi-Turn History Management & Sliding Window:** Multi-turn context is preserved using a standard Pydantic `TypeAdapter` that serializes and deserializes the conversation history into `chat_history.json`. It aligns fully with OpenAI-style structural conventions (`{"role": "user | assistant", "content": "..."}`). To prevent token bloat, high response latency, and API timeouts (`DEADLINE_EXCEEDED`) during long conversation chains, the system implements a strict **Sliding Window** mechanism. The conversation history is capped at a maximum of **50 messages (5 user-assistant turns)**. Older messages are automatically truncated during serialization, ensuring that the stored history always starts with a `user` prompt to maintain contextual structural consistency.
6. **Text-to-Speech (TTS):** The ultra-concise, masked text response from Gemini is converted back into a new `.wav` audio file using a local Coqui TTS with external model inference and the vocal characteristics of the `wibowo` speaker.
7. **Audio Output:** The synthesized speech file is returned to the user for direct playback with autoplay enabled.

---

## Pipeline Analysis and Evaluation Workflow
When running the `pipeline_analysis.py` module, the system enters a bulk evaluation testing mode with the following workflow:

1. **File Validation:** Identifies all `.wav` files in the audio data corpus, ignoring duplicate files that contain numbering parenthesis patterns such as `(1)`.
2. **Checkpoint Verification:** Reads the `checkpoint.json` file so that testing that was previously interrupted can be resumed from the last index without reprocessing successfully processed audio files.
3. **Component Execution & Latency Measurement:** Calculates the individual processing duration (in seconds) for the STT, LLM, and TTS subsystems.
4. **Error Value Calculation (WER/CER):** The detected transcript text is tested for accuracy against the original reference text in `reference.json` using the `jiwer` library.
5. **Final Output Generation:** Produces a comprehensive statistical summary consisting of the average WER, average CER, and average overall latency, which is saved into a new timestamped JSON file inside the results directory.

---

## Project Directory Structure

```
.
├── README.md                  # Project documentation
├── app                        # Main backend application code
│   ├── coqui_tts              # Inference model and Coqui TTS configuration
│   │   ├── checkpoint_1260000-inference.pth
│   │   ├── config.json
│   │   └── speakers.pth
│   ├── llm.py                 # Google Gemini API integration, history serialization & thought masking
│   ├── main.py                # FastAPI endpoint implementation (/voice-chat)
│   ├── stt.py                 # Transcription integration with whisper.cpp CLI
│   ├── tts.py                 # Speech synthesis integration with Coqui TTS CLI
│   └── utils.py               # System logging utilities and prompt reader
├── data                       # Input and output data repository
│   ├── corpus                 # Test data for the evaluation process
│   │   ├── audio              # Collection of benchmark .wav audio files
│   │   └── transcripts        # reference.json file containing original ground-truth text
│   ├── history                # Storage for the chat_history.json file
│   ├── prompts                # Base instructions for the LLM split by behavioral modes
│   │   ├── normalize.md       # System prompt for formal standardized Indonesian
│   │   └── preserve.md        # System prompt for conversational code-switching Indonesian
│   └── results                # Evaluation output files and checkpoint.json
├── gradio_app
│   └── app.py                 # Interactive web interface using modern OpenAI-style Chatbot schema
├── logs                       # Daily system log files categorized by date
├── models
│   └── whisper.cpp            # Source code, build binaries, and Whisper model files
├── utils                      # Data system maintenance utilities
│   ├── audio_remux.py         # Audio normalization script using FFmpeg
│   └── clean_errors.py        # Cleanup script for failed entries in the checkpoint
├── pipeline_analysis.py       # Script for mass pipeline evaluation testing
├── pyproject.toml             # Dependency configuration for the uv environment
├── requirements.txt           # Traditional Python module dependency list
├── run.sh                     # Bash/Linux/macOS automation script
└── uv.lock                    # Dependency lock file for uv
```

---

## Project Execution Guide

### System Requirements
* Python 3.10 or newer.
* `uv` package manager (highly recommended for fast dependency management).
* `ffmpeg` toolkit installed and registered in the operating system's PATH.
* Gemini API Key credentials saved in the `.env` file within the root directory.

```env
GEMINI_API_KEY=gemini_api_key
GEMINI_MODEL=gemini_model_name
```

### Operational Steps via `run.sh`

You can utilize the `run.sh` script with the following usage syntax: `./run.sh <command>`.

Below is the list of available commands along with their purpose and intent:

1. **`./run.sh setup`**
* **Intent/Purpose:** Performs the initial workspace setup. It verifies the existence of `pyproject.toml`. If not found, it initializes a new project environment using `uv init .` before handing over the process to the dependency installation routine to build the virtual environment (`.venv`) and align all modules.

2. **`./run.sh sync`**
* **Intent/Purpose:** Explicitly invokes the internal dependency installation routine. It ensures the local virtual environment (`.venv`) exists, synchronizes the project state with `pyproject.toml` using `uv sync`, and installs legacy requirements from `requirements.txt` via `uv pip install`.

3. **`./run.sh server`**
* **Intent/Purpose:** Runs the backend API server powered by FastAPI using the Uvicorn ASGI server at host address `0.0.0.0` and port `8000`. The `--reload` option is enabled for hot-reloading.

4. **`./run.sh app`**
* **Intent/Purpose:** Launches the interactive frontend application built with Gradio (`gradio_app/app.py`). It uses modern `type="messages"` chat states, provides a dropdown for switching between **normalize** and **preserve** modes, and automatically stream-plays synthesized voice responses.

5. **`./run.sh analyze`**
* **Intent/Purpose:** Runs automated mass evaluation processing on test files via the `pipeline_analysis.py` script.
* `./run.sh analyze --clean`: Triggers a total reset of legacy analysis results and chat histories before running the evaluation.
* `./run.sh analyze --fresh`: Purges only the corrupted or failed entries inside the active checkpoint via `clean_errors.py` prior to initiating the evaluation.

6. **`./run.sh clean`**
* **Intent/Purpose:** Performs directory maintenance depending on the provided sub-command flag: `--errors` (fixes checkpoint), `--logs` (clears logs), `--results` (wipes reports), or `--all` (comprehensive purge).

7. **`./run.sh sum`**
* **Intent/Purpose:** Displays a comprehensive statistical summary of the evaluation status from the `data/results/checkpoint.json` file using `jq` and `awk`. It calculates the exact failure ratio percentage alongside the success-to-failure operational balance.