"""
Feature: voice troubleshooting (speech-to-text half).

Uses SpeechRecognition with the free Google Web Speech API backend --
no API key needed, but it does need internet access on the machine running
this backend (it calls Google's servers). Audio is converted to WAV via
pydub first since recognize_google() needs WAV/PCM input; pydub needs
ffmpeg installed on the system (see README).

If neither is available (offline dev, no ffmpeg), this fails gracefully
and the caller falls back to typed text instead of blocking the demo.
"""
import io
import speech_recognition as sr


def transcribe_audio(file_storage) -> dict:
    """file_storage: a Flask uploaded file (webm/mp3/wav/m4a etc.)"""
    try:
        from pydub import AudioSegment

        raw_bytes = file_storage.read()
        audio = AudioSegment.from_file(io.BytesIO(raw_bytes))
        wav_io = io.BytesIO()
        audio.export(wav_io, format="wav")
        wav_io.seek(0)

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_io) as source:
            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(audio_data)
        return {"success": True, "text": text, "error": None}

    except sr.UnknownValueError:
        return {"success": False, "text": None, "error": "Could not understand the audio -- please try speaking again."}
    except sr.RequestError:
        return {"success": False, "text": None, "error": "Speech service unavailable (needs internet access on the server)."}
    except Exception as exc:  # ffmpeg missing, bad file, etc.
        return {"success": False, "text": None, "error": f"Could not process audio ({exc}). Make sure ffmpeg is installed."}
