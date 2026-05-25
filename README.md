# Voice Chatbot Pipeline – STT, Gemini LLM, TTS Integration and Evaluation

## Project Description

This project is an integrated, AI-powered Voice Chatbot system that combines Speech-to-Text (STT), Large Language Model (LLM), and Text-to-Speech (TTS) components. In addition to providing an interactive web-based interface, the project is equipped with an automated performance testing subsystem (pipeline analysis) to measure transcription accuracy using Word Error Rate (WER) and Character Error Rate (CER) metrics, as well as to track processing latency for each supporting component.

---

## System Workflow and Operations

This system operates through a chained processing cycle (pipeline) from audio input to audio output with the following workflow:

1. **Audio Input:** The user records voice via a microphone on the Gradio interface or sends a `.wav` audio file through the API endpoint.
2. **Speech-to-Text (STT):** The audio file is fed into the `whisper.cpp` CLI binary using the `ggml-large-v3-turbo` model to be converted into transcript text.
3. **FFmpeg Remux Mechanism (Fallback):** If Whisper detects an error in the raw audio structure, the system triggers a recovery function by calling FFmpeg externally to modify the audio parameters to mono, 16000Hz sampling rate, `pcm_s16le` codec, and performs the transcription again.
4. **LLM Processing:** The transcript text is sent to the Google Gemini API using the `google-genai` SDK with embedded system instructions. The system loads the conversation history (`chat_history.json`) to maintain multi-turn context. This process is protected by dual timeouts and automatic retries if the server experiences disruptions.
5. **Text-to-Speech (TTS):** The text response from Gemini is converted back into a new `.wav` audio file using a local Coqui TTS with external model inference and the vocal characteristics of the `wibowo` speaker.
6. **Audio Output:** The synthesized speech file is returned to the user for direct playback.

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
│   ├── llm.py                 # Google Gemini API integration & history management
│   ├── main.py                # FastAPI endpoint implementation (/voice-chat)
│   ├── stt.py                 # Transcription integration with whisper.cpp CLI
│   ├── tts.py                 # Speech synthesis integration with Coqui TTS CLI
│   └── utils.py               # System logging utilities and prompt reader
├── data                       # Input and output data repository
│   ├── corpus                 # Test data for the evaluation process
│   │   ├── audio              # Collection of benchmark .wav audio files
│   │   └── transcripts        # reference.json file containing original ground-truth text
│   ├── history                # Storage for the chat_history.json file
│   ├── prompts                # Base instructions for the LLM (instruction.md)
│   └── results                # Evaluation output files and checkpoint.json
├── gradio_app
│   └── app.py                 # Interactive web interface code using Gradio
├── logs                       # Daily system log files categorized by date
├── models
│   └── whisper.cpp            # Source code, build binaries, and Whisper model files
├── utils                      # Data system maintenance utilities
│   ├── audio_remux.py         # Audio normalization script using FFmpeg
│   └── clean_errors.py        # Cleanup script for failed entries in the checkpoint
├── pipeline_analysis.py       # Script for mass pipeline evaluation testing
├── pyproject.toml             # Dependency configuration for the uv environment
├── requirements.txt           # Traditional Python module dependency list
├── run.sh                     # Project execution automation script
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
* **Intent/Purpose:** Performs the initial initialization of the project's virtual environment. This command checks for the existence of the `pyproject.toml` file. If found, it runs `uv sync` to precisely align the local environment with the lock file. If it does not exist yet, it triggers `uv init .` first.


2. **`./run.sh server`**
* **Intent/Purpose:** Runs the backend API server powered by FastAPI using the Uvicorn ASGI server at host address `0.0.0.0` and port `8000`. The `--reload` option is enabled so that the server automatically reloads whenever code changes occur in the `app/` directory.


3. **`./run.sh app`**
* **Intent/Purpose:** Launches the interactive frontend application built with Gradio (`gradio_app/app.py`). Through this command, the web interface can be accessed by users via a browser to record voice directly from a microphone and receive audio responses from the system.


4. **`./run.sh analyze`**
* **Intent/Purpose:** Runs automated mass evaluation processing on test files via the `pipeline_analysis.py` script. This command supports additional sub-arguments:
* `./run.sh analyze --clean`: Deletes all legacy analysis history and chat history prior to starting a brand new analysis from scratch.
* `./run.sh analyze --fresh`: Performs a cleanup of corrupted or failed data entries within the saved files before initiating the continuous analysis process.




5. **`./run.sh clean`**
* **Intent/Purpose:** Performs directory maintenance by selectively removing garbage or temporary data depending on the sub-argument provided:
* `--errors`: Executes the `clean_errors.py` module to sort out and discard failed transcript entries from the main checkpoint file.
* `--logs`: Empties all log files inside the `logs/*` directory.
* `--results`: Deletes all evaluation report files and saved checkpoint files inside the `data/results/*` directory.
* `--all`: Runs a comprehensive cleanup function for logs, chat history, and evaluation results simultaneously.




6. **`./run.sh sum`**
* **Intent/Purpose:** Displays a quick summary of the evaluation status from the `data/results/checkpoint.json` file. This command maps the data using the `jq` utility to filter and count the number of files with an `is_failed == true` status, prints the list of problematic filenames, and precisely displays the system failure ratio percentage.