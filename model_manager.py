# model_manager.py
import torch
import whisper
import os

class ModelManager:
    def __init__(self, config):
        self.config = config
        self.stt_model = self.load_stt_model()
        self.tts_model = self.load_tts_model()

    def load_stt_model(self):
        print(f"Loading STT model: {self.config.stt_model_size}")
        model = whisper.load_model(self.config.stt_model_size).to(self.config.stt_device)
        print("STT Model loaded successfully.")
        return model

    def load_tts_model(self):
        print("Loading TTS model")
        try:
            model, example_text = torch.hub.load(
                repo_or_dir="snakers4/silero-models",
                model="silero_tts",
                language=self.config.tts_language,
                speaker=self.config.tts_model_id,
                force_reload=False,
                trust_repo=True,
                source="github", # Changed source to github
            )
            model.to(self.config.tts_device)
            print("TTS Model loaded successfully.")
            return model
        except Exception as e:
            print(f"Error loading TTS model: {e}")
            raise


    def transcribe_audio(self, file_name):
        try:
            options = whisper.DecodingOptions(task='translate', language='Tagalog', fp16=False)
            audio = whisper.load_audio(file_name)
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(self.stt_model.device)
            print("Audio processed for transcription.")
            result = whisper.decode(self.stt_model, mel, options)
            print("Transcription completed.")
            return result.text
        except Exception as e:
          print(f"Error occured when transcribing {e}")
          return None

    def generate_speech(self, text):
        try:
            audio = self.tts_model.apply_tts(text=text,
                                             speaker=self.config.tts_speaker,
                                             sample_rate=self.config.tts_sample_rate,
                                             put_accent=self.config.tts_put_accent,
                                             put_yo=self.config.tts_put_yo)
            return audio.numpy()
        except Exception as e:
          print(f"Error occured when generating speech {e}")
          return None
