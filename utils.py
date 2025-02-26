# utils.py
import random
import numpy as np
import sounddevice as sd

async def async_SpeakandSend(toSpeak, queuedArt, queuedTitle, data_queue, audio_manager, model_manager):
    #This takes text and transcribes it to audio.
    #Alongside this, in order to deal with timing issues it sends the location of the relevant section AFTER silero creates the audio
    try:
        audio = model_manager.generate_speech(toSpeak)
        print("audio recorded")
        data_queue.put((queuedArt, toSpeak, queuedTitle))
        #This is done because otherwise the image and text and gets put to the GUI before audio plays making 'lag'
        numpy_array = audio
        sd.play(numpy_array, model_manager.config.tts_sample_rate)
        sd.wait()
        print("Audio playback")
        data_queue.put((model_manager.config.idleimage, toSpeak, queuedTitle))
    except:
        print("Audio Skipped due to Silero Issue")
        return False
    return True

def set_image(config):
    #Made into a function for future extendability
    return random.choice(config.imagelist)
