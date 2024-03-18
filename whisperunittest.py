import whisper
import ffmpeg
import time

duration = 7
model_size = "small"
deviceWhisper = 'cpu'
print("Loading model:", model_size)
STTmodel = whisper.load_model(model_size).to(deviceWhisper)
print("STT Model loaded successfully.")

#async def transcribe_directly(duration=10):
    #This function transcribes tagalog audio and transcribes it to english
file_name = "recorded_audio.wav"  # File to store recorded audio
#Note this is necessary, whisper cannot be run off of a stream AFAIK

try:      
    #await play_asset(soundlist[0],blocking=False) #Start talking sound
    # Use ffmpeg to record audio from the default audio input device
    process = (
        ffmpeg.input('audio=Microphone (Realtek(R) Audio)', format='dshow')
        .output(file_name, format='wav', t=duration)
        .overwrite_output()
        .run_async(pipe_stdin=True)
    )

    #await asyncio.sleep(duration)  # Wait for the specified duration
    time.sleep(duration)
    # Stop ffmpeg process
    process.communicate(input=b'q')
    print("Recording completed.")
    #await play_asset(soundlist[1]) #Stop talking sound 
    # Transcribe the audio to text
    
    options = whisper.DecodingOptions(task='translate', language='Tagalog', fp16=False)
    audio = whisper.load_audio(file_name)
    audio = whisper.pad_or_trim(audio)
    mel = whisper.log_mel_spectrogram(audio).to(STTmodel.device)
    print("Audio processed for transcription.")
    result = whisper.decode(STTmodel, mel, options)
    print("Transcription completed.")

    print (result.text)
    #return result.text
    

except Exception as e:
    #return f"An error occurred: {e}"
    print("An error occured")