# utils.py
import random
import numpy as np
import sounddevice as sd
import asyncio

async def async_Speak(audio, sample_rate):
    # Plays audio asynchronously
    sd.play(audio, sample_rate)


async def async_Send(queuedArt, toSpeak, queuedTitle, data_queue):
    # Sends data to the GUI asynchronously
    data_queue.put((queuedArt, toSpeak, queuedTitle))


def set_image(config):
    # Made into a function for future extendability
    return random.choice(config.imagelist)

