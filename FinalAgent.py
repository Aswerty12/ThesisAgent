import asyncio
import sys
import whisper
import ffmpeg
import requests
import json
import re
from datetime import datetime
import torch
import asyncio
import numpy as np
import sounddevice as sd
import soundfile as sf
import random
import queue
import threading
import tkinter as tk
import time
import os
from PIL import Image, ImageTk, ImageSequence


#This preloads all the necessary models before the chat loop
#FOR api 
url = "http://127.0.0.1:5001/v1/chat/completions"

headers = {
    "Content-Type": "application/json"
}

#Loading of STT into CPU
model_size = "small"
deviceWhisper = 'cpu'
print("Loading model:", model_size)
STTmodel = whisper.load_model(model_size).to(deviceWhisper)
print("STT Model loaded successfully.")


#Loading of TTS model into CPU
language = 'en'
model_id = 'v3_en'
deviceSilero = torch.device('cpu')

TTSmodel, example_text = torch.hub.load(repo_or_dir='snakers4/silero-models',
                                    model='silero_tts',
                                    language=language,
                                    speaker=model_id)
TTSmodel.to(deviceSilero) 
sample_rate = 48000
speaker = 'en_21' 
put_accent=True
put_yo=True

print("TTS Model Loaded")

imagelist = ["talkinggirl.gif","talkinggirl.gif"]
#Due to lack of alt animations this will just be the generic talking animation twice to avoid rewrites
idleimage = "thinking.gif"

soundlist= ["game-start.mp3","negative_beeps.mp3","ping.mp3"]
fillersounds = ["filleraudio0.mp3","filleraudio1.mp3","filleraudio2.mp3","filleraudio3.mp3","filleraudio4.mp3"]
#Placeholder set of sounds


gameAI = ["AIverApple","AIverSharing","AIverShark"]
game_words ={
    "AIverApple": "apple",
    "AIverSharing": "sharing",
    "AIverShark": "shark"
}
#Lists and Dictionaires for the list of game personas

data_queue = queue.Queue()
#Queue for communication between the tkinter GUI and the chat loop

stop_update = False
#Global flag to communicate between thread. 

async def transcribe_directly(duration=10):
    #This function transcribes tagalog audio and transcribes it to english
    file_name = "recorded_audio.wav"  # File to store recorded audio
    #Note this is necessary, whisper cannot be run off of a stream AFAIK

    try:      
        await play_asset(soundlist[0],blocking=False) #Start talking sound
        # Use ffmpeg to record audio from the default audio input device
        process = (
            ffmpeg.input('audio=Microphone (Realtek(R) Audio)', format='dshow')
            .output(file_name, format='wav', t=duration)
            .overwrite_output()
            .run_async(pipe_stdin=True)
        )

        await asyncio.sleep(duration)  # Wait for the specified duration
        
        # Stop ffmpeg process
        process.communicate(input=b'q')
        print("Recording completed.")
        await play_asset(soundlist[1]) #Stop talking sound 
        # Transcribe the audio to text
        
        options = whisper.DecodingOptions(task='translate', language='Tagalog', fp16=False)
        audio = whisper.load_audio(file_name)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(STTmodel.device)
        print("Audio processed for transcription.")
        result = whisper.decode(STTmodel, mel, options)
        print("Transcription completed.")

        print (result.text)
        return result.text
        

    except Exception as e:
        return f"An error occurred: {e}"


async def async_speak(toSpeak):
    skip_audio = False  # Flag to indicate to skip audio in case of error with silero
    #This takes text and transcribes it to audio. 
    try:
        audio = TTSmodel.apply_tts(text=toSpeak,
                            speaker=speaker,
                            sample_rate=sample_rate,
                            put_accent=put_accent,
                            put_yo=put_yo)
        print("audio recorded")
        numpy_array = audio.numpy()
        
        sd.play(numpy_array,sample_rate)
        sd.wait()
        print("Audio playback")
    except:
        print("Audio skipped")
        skip_audio = True
        
    return not skip_audio  # Return True for success, False for error
    
async def async_SpeakandSend(toSpeak,queuedArt,queuedTitle):
    #This takes text and transcribes it to audio. 
    #Alongside this, in order to deal with timing issues it sends the location of the relevant section AFTER silero creates the audio
    skip_audio = False  # Flag to indicate to skip audio in case of error with silero
    #TODO Use this functionality and test
    try:
        audio = TTSmodel.apply_tts(text=toSpeak,
                            speaker=speaker,
                            sample_rate=sample_rate,
                            put_accent=put_accent,
                            put_yo=put_yo)
        print("audio recorded")
        data_queue.put((queuedArt,toSpeak,queuedTitle))
        #This is done because otherwise the image and text and gets put to the GUI before audio plays making 'lag'
        numpy_array = audio.numpy()
        
        sd.play(numpy_array,sample_rate)
        sd.wait()
        print("Audio playback")
        data_queue.put((idleimage,toSpeak,queuedTitle))
    except:
        print("Audio Skipped due to Silero Issue")
        skip_audio = True
    return not skip_audio  # Return True for success, False for error
        
    
async def play_asset(sound_name,blocking= True):
    folder_name = "asset"
    try:
        sound_path = os.path.join(os.getcwd(), folder_name, sound_name)
        data, fs = sf.read(sound_path)
        if (blocking==True):
            sd.play(data,fs)
            sd.wait() 
        else:
            sd.play(data,fs)
              
    except FileNotFoundError:
        print("Error: Sound file not found at the specified path.")

def set_image():
    #Made into a function for future extendability
    return random.choice(imagelist)

def create_dynamic_gui(data_queue):
    def update_labels():
        global stop_update
        while not stop_update:
            try:
                image_name, text, title = data_queue.get(timeout=1)  # Wait for 1 second for new data

                # Clear previous GIF animation
                if image_name.lower().endswith('.gif'):
                    clear_gif()
                else:
                    clear_image()
                # Get image from folder
                image_path = get_image(image_name)

                # Display new message
                display_image(image_path)
                title_label.config(text=title)
                text_label.config(text=text)
                text_label.config(wraplength=700)  # Set the maximum width for the label
                root.update_idletasks()  # Update the window

                time.sleep(2)  # Display each message for 2 seconds minimum

                root.update_idletasks()  # Update the window again
            except queue.Empty:
                pass
        root.destroy()

    def clear_image():
        image_label.config(image="")
        image_label.image = None

    def display_image(image_path):
        if image_path.lower().endswith('.gif'):
            display_animated_gif(image_path)
        else:
            img = Image.open(image_path)
            photo = ImageTk.PhotoImage(img)
            image_label.config(image=photo)
            image_label.image = photo  # To prevent garbage collection
    
    def get_gif_duration(image_path):
        img = Image.open(image_path)
        try:
            # Get frame duration from metadata if available
            return img.info.get('duration', 100)  # Default to 100ms if not found
        except (AttributeError, KeyError):
            # Handle potential errors gracefully
            return 100

    def display_animated_gif(image_path):
        img = Image.open(image_path)
        frames = [ImageTk.PhotoImage(frame) for frame in ImageSequence.Iterator(img)]
        duration = get_gif_duration(image_path)
        min_delay = 200

        def update_frame(idx=0):
            nonlocal duration,min_delay  # Modify the variable inside the function
            
            image_label.config(image=frames[idx])
            image_label.image = frames[idx]
            idx = (idx + 1) % len(frames)  # Loop the frames
            delay = max(min_delay, int(duration / len(frames)))  # Ensure minimum delay
            frame_id = root.after(delay, update_frame, idx)
            image_label.frame_id = frame_id  # Save frame_id in the label

        # Display the first frame
        update_frame()

    def clear_gif():
        # Cancel the scheduled job for updating frames
        if hasattr(image_label, 'frame_id'):
            root.after_cancel(image_label.frame_id)

        # Manually clear the image
        clear_image()


    def get_image(file_name):
        folder_name = "asset"
        try:
            image_path = os.path.join(os.getcwd(), folder_name, file_name)
            return image_path
        except FileNotFoundError:
            print("Error: Image file not found at the specified path.")
    # Create the tkinter window
    root = tk.Tk()
    root.title("Alex the AI")
    # Set a fixed window size
    window_width = 800
    window_height = 700
    root.geometry(f"{window_width}x{window_height}")
    
    

    # Create labels for splash screen
    splashImg = Image.open("asset/titlescreen.png")
    splashPhoto = ImageTk.PhotoImage(splashImg)
    title_label = tk.Label(root, text="Alex the AI Agent", font=("Helvetica", 16, "bold"))
    title_label.pack(pady=10)

    image_label = tk.Label(root,image=splashPhoto)
    image_label.pack()

    text_label = tk.Label(root, text="For: Development of Computer Agent for Child-Robot Symbolic Anthropomorphism", wraplength=750)  # Set initial wraplength
    text_label.pack()

    # Start a thread to update labels dynamically
    update_thread = threading.Thread(target=update_labels)
    update_thread.daemon = True
    update_thread.start()

    root.mainloop()

def stop_gui():
    global stop_update  # Use the global flag variable
    stop_update = True
    print("It should stop now")

async def chat_loop():
    #Rename, use this function as the generic chat
    history = []
    chatTitle = "Just Chatting"
    exit_pattern = re.compile(r'(exit|quit)\b', re.IGNORECASE) 
    messageToSay = "Just ask any question, and I can answer it."
    await async_SpeakandSend(messageToSay,imagelist[1],chatTitle)
    while True:
        
        user_message = await transcribe_directly(duration=7)  # Recording for X seconds
        #user_message = input('> ') #Manual input for debugging
        if exit_pattern.search(user_message): #This can be changed later to implement logic
            # Get current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"chat_history_{timestamp}.txt"
            directory = "chathistory"
            file_path = os.path.join(os.getcwd(), directory,file_name)
            # Dump history to a file with timestamp in the filename
            with open(file_path, 'w') as file:
                json.dump(history, file, indent=4)
            break  # Exit the loop if user enters or says 'exit' or 'quit'
            
        #Sound for stopping is in 
        history.append({"role": "user", "content": user_message})
        
        data = {
        "mode": "chat-instruct",
        "preset":"Midnight Enigma",
        "instruction_template":"zephyr3b0",
        "character": "AIver1",
        "messages": history
        }
        
        randomfiller = random.choice(fillersounds)
        await play_asset(randomfiller,blocking=False)
        response = requests.post(url, headers=headers, json=data, verify=False)
        assistant_message = response.json()['choices'][0]['message']['content']
        history.append({"role": "assistant", "content": assistant_message})
        selectedimage = set_image() #Could maybe extend logic to picking images
        #Putting into data queue moved to function for timing
        print(assistant_message)
        success = await async_SpeakandSend(assistant_message,selectedimage, chatTitle)
        if success:
            continue
        else:
            data_queue.put((idleimage, selectedimage, chatTitle))
            print("AUDIO SKIPPED DUE TO LENGTH")
        #data_queue.put((assistant_message,idleimage,chatTitle))

async def game_loop(exitword,character):
    history = []
    print(exitword)
    print(character)
    gameTitle = 'Guessing Game'
    pattern = re.compile(r'(yes|okay)\b', re.IGNORECASE)
    intro = "I am thinking of a word... For our game, you will try to guess it while I give hints. You can also ask questions while you guess. Do you understand? Say yes or okay to continue."
    while True:
        
        data_queue.put((imagelist[1],intro,"Gameplay Introduction"))
        print(intro)
        await play_asset('gameintro.mp3') #prerecorded for response time
        data_queue.put((idleimage,intro,"Gameplay Introduction"))
        user_message = await transcribe_directly(duration=5)  # Recording for X seconds
        if pattern.search(user_message):
            break
    intro_Hint = "Insert hint here"
    if exitword == 'apple':
        intro_Hint = "smooth and can fit in your hand"
    elif exitword =='shark':
        intro_Hint = "something with sharp teeth and lives in the sea."
    elif exitword =='shar':
        intro_Hint =  "an act you do to those who have less than you."
    fullHint = "I'm thinking of a thing. Your goal is to guess it. Here's your first hint: What I'm thinking of is " + intro_Hint
    history.append({"role": "assistant", "content": fullHint})
    
    await async_SpeakandSend(fullHint, imagelist[1],gameTitle)
    exit_pattern = re.compile(r'(exit|quit|{})\b'.format(exitword), re.IGNORECASE)
    exitingWord = re.compile(r'({})'.format(exitword), re.IGNORECASE)
    while True:
        user_message = await transcribe_directly(duration=8)  # Recording for X seconds
        print(exitingWord)
        #user_message = input('> ') #Manual input for debugging
        if exit_pattern.search(user_message): 
            # Get current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"chat_history_{timestamp}.txt"
            directory = "chathistory"
            file_path = os.path.join(os.getcwd(), directory,file_name)
            # Dump history to a file with timestamp in the filename
            with open(file_path, 'w') as file:
                json.dump(history, file, indent=4)
            if exitingWord.search(user_message):
                return "WIN"
            else: 
                return "QUIT"
            
            

        history.append({"role": "user", "content": user_message})
        
        data = {
        "mode": "chat-instruct",
        "instruction_template":"zephyr3b0",
        "preset":"Big O",
        "character": character,
        "messages": history
        }
        randomfiller = random.choice(fillersounds)
        await play_asset(randomfiller,blocking=False)
        response = requests.post(url, headers=headers, json=data, verify=False)
        assistant_message = response.json()['choices'][0]['message']['content']
        if exitingWord.search(assistant_message):
            # Get current timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"chat_history_{timestamp}.txt"
            directory = "chathistory"
            file_path = os.path.join(os.getcwd(), directory,file_name)
            history.append({"role":"SYSTEM","content": "GENERATED TEXT HAS HIDDEN WORD IN IT. USER NEEDS TO GUESS NOW"})
            # Dump history to a file with timestamp in the filename
            with open(file_path, 'w') as file:
                json.dump(history, file, indent=4)
            result = await finalGuess(exitword)
            return result               
        history.append({"role": "assistant", "content": assistant_message})
        selectedimage = set_image()
        print(assistant_message)
        success = await async_SpeakandSend(assistant_message,selectedimage, gameTitle)
        if success:
            continue
        else:
            data_queue.put((idleimage, selectedimage, gameTitle))
            print("AUDIO SKIPPED DUE TO LENGTH")
                
async def finalGuess(toGuess):
    wordToGuess = re.compile(r'({})'.format(toGuess), re.IGNORECASE)
    selectedimage = set_image()
    finalSay = "Hmm. It seems like you're close enough to what I'm thinking of that I can't give anymore hints or answer anymore questions. Here's your last chance. What word was I thinking?"
    await async_SpeakandSend(finalSay,selectedimage, "Final Guess")
    user_message = await transcribe_directly(duration=8)  # Recording for X seconds
    
    if wordToGuess.search(user_message):
        userwins = "I think I heard you say {}, that's the word I was thinking of congratulations!".format(toGuess)
        await async_SpeakandSend(userwins,selectedimage,"WINNING GUESS")
        return "WIN"
    else:
        userwrong = "I'm sorry. That is not the word that I was thinking of. The right answer was {}".format(toGuess)
        await async_SpeakandSend(userwrong,selectedimage,"WRONG GUESS")
        return "QUIT"
    
    
async def introduction():
    #Prerecorded Introduction
    #This is the illusory agent that only responds with canned audio and logic
    pattern = re.compile(r'(yes|okay)\b', re.IGNORECASE)
    placeholder = imagelist[1]
    introtitle = "Introduction"
    
    #That's a wonderful name. It's great to meet you. I'm here to talk with you for a while.
    await async_SpeakandSend("Before we introduce ourselves you should know how to talk with me.",placeholder,introtitle)
    while True:
        data_queue.put((placeholder,'You will hear a series of sounds, this indicates that you can speak.', introtitle))
        await play_asset('test_1.mp3')
        #You will hear a series of sounds, this indicates that you can speak
        await play_asset("game-start.mp3")
        #SFX for starting
        data_queue.put((placeholder,'Meanwhile this is the sound for when you should stop talking.', introtitle))
        await play_asset('test_2.mp3')
        #Meanwhile this is the sound for when you should stop talking
        await play_asset("negative_beeps.mp3")
        #SFX For Stopping
        data_queue.put((placeholder,"Do you understand? Just say yes if you want to continue with the game. Otherwise I'll explain again", introtitle))
        await play_asset('test_3.mp3')
        data_queue.put((idleimage,"Do you understand? Just say yes if you want to continue with the game. Otherwise I'll explain again",introtitle))
        #Do you understand? Just say yes if you want to continue with the game. Otherwise I'll explain again
        user_message = await transcribe_directly(duration=5)  # Recording for X seconds
        if pattern.search(user_message):
            break
    await async_SpeakandSend("Anyway, Greetings my name is Alex, what's your name?", placeholder,introtitle)
    await transcribe_directly(duration=8)
    await async_SpeakandSend("That's a wonderful name. It's great to meet you. I'm here to talk with you for a while.",placeholder,introtitle)
    

# Run the chat loop asynchronously
async def main():
    #This is the skeleton for the 'illusion'. At first the system will just be the silero, and whisper pipeline
    #But when it comes to actual dynamic response an LLM can be used
    intro = "Hello. I am an A.I. program running inside of this computer. Let's talk and chat for a while."
    gamepattern = re.compile(r'game', re.IGNORECASE)
    chatpattern = re.compile(r'chat', re.IGNORECASE)
    quitpattern = re.compile(r'quit', re.IGNORECASE)
    await async_SpeakandSend(intro, imagelist[1], "Intro")
    await introduction() #TODO MAKE sure this is not commented out
    while True:
        tosay = "So, do you want to chat or play a game? Just say 'chat' if you just want to talk or say 'game' if you want to play."
        data_queue.put((imagelist[1],tosay,"Introduction"))
        await play_asset('thechoice.mp3') #Tosay prerecorded
        data_queue.put((idleimage,tosay,"Introduction"))
        userTalk = await transcribe_directly(duration=5)
        
        if re.search(gamepattern,userTalk):
            gametoPlay = random.choice(gameAI)
            gameword = game_words.get(gametoPlay)
            game_result = await game_loop(gameword,gametoPlay)
            if (game_result =="WIN"):
                print("You win")
                messageAfterWin = "You've won! Congratulations. Say 'quit' in the next screen if you're finished"
                await async_SpeakandSend(messageAfterWin,imagelist[1],"Thanks")
                continue
            elif(game_result =="QUIT"):
                print("Thanks for playing")
                messageForQuitting = "Thanks for playing, too bad you couldn't guess it. Say 'quit' on the next screen if you're finished"
                await async_SpeakandSend(messageForQuitting,imagelist[1],"Thanks")
                continue
        elif re.search(chatpattern,userTalk):            
            await chat_loop()
            chatEndMessage = "That was a nice chat. If you want to stop, just say quit on your next turn."
            data_queue.put((imagelist[1],chatEndMessage,"Thanks"))
            await play_asset("chatend.mp3")
        elif re.search(quitpattern,userTalk):
            break
    
    stop_gui()
  
    
tkinter_thread = threading.Thread(target=create_dynamic_gui, args=(data_queue,))
tkinter_thread.start()

asyncio.run(main())
