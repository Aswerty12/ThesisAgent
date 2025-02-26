# audio_manager.py
import ffmpeg
import sounddevice as sd
import soundfile as sf
import asyncio
import os
import tempfile  # Import tempfile


class AudioManager:
    def __init__(self, config):
        self.config = config

    async def record_audio(self, duration=10):
        # file_name = "recorded_audio.wav"
        # Use a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            file_name = temp_file.name  # Get the name of the temporary file

        try:
            process = (
                ffmpeg.input('audio=Microphone (Realtek(R) Audio)', format='dshow')
                .output(file_name, format='wav', t=duration)
                .overwrite_output()
                .run_async(pipe_stdin=True)
            )

            await asyncio.sleep(duration)
            process.communicate(input=b'q')
            print("Recording completed.")
            return file_name

        except Exception as e:
            print(f"An error occurred during recording: {e}")
            return None

    async def play_audio(self, sound_name, blocking=False):  # Changed default to False
        try:
            sound_path = os.path.join(os.getcwd(), self.config.asset_dir, sound_name)
            data, fs = sf.read(sound_path)
            sd.play(data, fs)
            if blocking:
                sd.wait()
        except FileNotFoundError:
            print(f"Error: Sound file not found at {sound_path}")
        except Exception as e:
            print(f"Error playing sound file {e}")

