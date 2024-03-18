#Test Recording wav/mp3
import torch
import torchaudio
import sounddevice as sd

language = 'en'
model_id = 'v3_en'
deviceSilero = torch.device('cpu')

toSpeak = "I am thinking of a word... For our game, you will try to guess it while I give hints. You can also ask questions while you guess. Do you understand? Say yes or okay to continue."
TTSmodel, example_text = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                    model='silero_tts',
                                    language=language,
                                    speaker=model_id)
TTSmodel.to(deviceSilero)  # gpu or cpu
sample_rate = 48000
speaker = 'en_58'
put_accent=True
put_yo=True

print("TTS Model Loaded")

audio = TTSmodel.apply_tts(text=toSpeak,
                        speaker=speaker,
                        sample_rate=sample_rate,
                        put_accent=put_accent,
                        put_yo=put_yo)
print("audio recorded")
numpy_array = audio.numpy()

torchaudio.save('testing.mp3',
                  audio.unsqueeze(0),
                  sample_rate=sample_rate)
sd.play(numpy_array,sample_rate)
sd.wait()
print("Audio playback")