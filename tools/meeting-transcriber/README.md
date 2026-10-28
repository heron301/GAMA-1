# Meeting Transcriber (MCP server for Claude Desktop)

Transcribes a local meeting recording with faster-whisper, fully offline after the first model download. Claude receives the transcript and writes the summary, decisions, and action items. No audio leaves the machine.

## Setup (Windows — XE3)

1. Install Python 3.11 or later from python.org. Tick "Add python.exe to PATH".
2. Create `E:\Tools\meeting-transcriber`. Copy `meeting_transcriber.py` and `requirements.txt` into it (or run the clone in step 2a).

   2a. From a clone of this repo: `Copy-Item -Recurse <repo>\tools\meeting-transcriber E:\Tools\`

3. Open PowerShell in `E:\Tools\meeting-transcriber` and run:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\pip install -r requirements.txt
   ```

4. Test the first run. This downloads the speech model once (about 500 MB for `small.en`):

   ```powershell
   .\.venv\Scripts\python -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cpu', compute_type='int8')"
   ```

5. Register the server. In the Claude desktop app open Settings, Developer, Edit Config. Add this block inside `"mcpServers"`:

   ```json
   "meeting-transcriber": {
     "command": "E:\\Tools\\meeting-transcriber\\.venv\\Scripts\\python.exe",
     "args": ["E:\\Tools\\meeting-transcriber\\meeting_transcriber.py"]
   }
   ```

6. Restart the Claude desktop app (quit from the system tray, then reopen).
7. Ask: "Transcribe C:\Recordings\standup.mp4 and write the summary, decisions and action items."

## Models

| Model | Use | Download |
|---|---|---|
| `small.en` (default) | Speed | ~500 MB |
| `medium.en` | Names and technical terms | ~1.5 GB |
| `large-v3` | Non-English audio | ~3 GB |

Name the model in your request: "Transcribe ... with medium.en." To change the default, add `"env": {"TRANSCRIBER_MODEL": "medium.en"}` to the config block.

## GPU (optional, XE3)

The XE3 GPU runs `medium.en` and `large-v3` many times faster than the CPU. Add this to the config block:

```json
"env": {"TRANSCRIBER_DEVICE": "cuda"}
```

This needs an NVIDIA GPU with cuBLAS for CUDA 12 and cuDNN 9 DLLs on the PATH. See the faster-whisper README "GPU" section for the Windows library download. If the server fails to start after this change, remove the `env` line to return to CPU.

## Output

Transcripts save beside the recording as `<name>.transcript.txt` (timestamped lines) and `<name>.vtt` (captions). Supported inputs: mp3, mp4, m4a, wav, webm, mkv, mov, ogg, flac, aac, wma, avi. Audio decoding is built in; ffmpeg is not required.

## Limits

Speaker labels need a separate diarization model. This version does not label speakers. A one-hour meeting on CPU with `small.en` takes several minutes; the server sends progress updates so the app does not time out.

## Troubleshooting

Logs: `%APPDATA%\Claude\logs\mcp-server-meeting-transcriber.log`. If the server does not appear in Claude, check JSON commas in the config file and that both paths exist.

## Dependency pins

`requirements.txt` pins `mcp<2` (the 2.x SDK renamed the server API) and `av<18` (PyAV 18+ breaks faster-whisper audio decoding).
