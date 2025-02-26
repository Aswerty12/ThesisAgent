# FinalAgent.py
import asyncio
import re
import random
import threading
import queue
from config import Config
from audio_manager import AudioManager
from model_manager import ModelManager
from gui_manager import GUIManager
from llm_manager import LLMManager
from game_manager import GameManager
from chat_manager import ChatManager
from utils import async_SpeakandSend
import time


class FinalAgent:
    def __init__(self):
        self.config = Config()
        self.data_queue = queue.Queue()  # Queue for communication with GUI
        self.audio_manager = AudioManager(self.config)
        self.model_manager = ModelManager(self.config)
        self.gui_manager = GUIManager(self.config, self.data_queue)
        self.llm_manager = LLMManager(self.config)
        self.game_manager = GameManager(self.config, self.data_queue, self.audio_manager, self.llm_manager, self.model_manager)
        self.chat_manager = ChatManager(self.config, self.data_queue, self.audio_manager, self.llm_manager, self.model_manager)
        

    async def introduction(self):
        # Prerecorded Introduction
        # This is the illusory agent that only responds with canned audio and logic
        pattern = re.compile(r'(yes|okay)\b', re.IGNORECASE)
        placeholder = self.config.imagelist[1]
        introtitle = "Introduction"

        # That's a wonderful name. It's great to meet you. I'm here to talk with you for a while.
        await async_SpeakandSend("Before we introduce ourselves you should know how to talk with me.", placeholder, introtitle,self.data_queue,self.audio_manager,self.model_manager)
        while True:
            self.data_queue.put((placeholder, 'You will hear a series of sounds, this indicates that you can speak.', introtitle))
            await self.audio_manager.play_audio('test_1.mp3')
            # You will hear a series of sounds, this indicates that you can speak
            await self.audio_manager.play_audio("game-start.mp3")
            # SFX for starting
            self.data_queue.put((placeholder, 'Meanwhile this is the sound for when you should stop talking.', introtitle))
            await self.audio_manager.play_audio('test_2.mp3')
            # Meanwhile this is the sound for when you should stop talking
            await self.audio_manager.play_audio("negative_beeps.mp3")
            # SFX For Stopping
            self.data_queue.put((placeholder, "Do you understand? Just say yes if you want to continue with the game. Otherwise I'll explain again", introtitle))
            await self.audio_manager.play_audio('test_3.mp3')
            self.data_queue.put((self.config.idleimage, "Do you understand? Just say yes if you want to continue with the game. Otherwise I'll explain again", introtitle))
            # Do you understand? Just say yes if you want to continue with the game. Otherwise I'll explain again
            user_message_file = await self.audio_manager.record_audio(duration=5)  # Recording for X seconds
            user_message = self.model_manager.transcribe_audio(user_message_file)
            if pattern.search(user_message):
                break
        await async_SpeakandSend("Anyway, Greetings my name is Alex, what's your name?", placeholder, introtitle,self.data_queue,self.audio_manager,self.model_manager)
        await self.audio_manager.record_audio(duration=8)
        await async_SpeakandSend("That's a wonderful name. It's great to meet you. I'm here to talk with you for a while.", placeholder, introtitle,self.data_queue,self.audio_manager,self.model_manager)

    async def main(self):
        intro = "Hello. I am an A.I. program running inside of this computer. Let's talk and chat for a while."
        gamepattern = re.compile(r'game', re.IGNORECASE)
        chatpattern = re.compile(r'chat', re.IGNORECASE)
        quitpattern = re.compile(r'quit', re.IGNORECASE)
        await async_SpeakandSend(intro, self.config.imagelist[1], "Intro",self.data_queue,self.audio_manager,self.model_manager)
        await self.introduction()  # TODO MAKE sure this is not commented out
        while True:
            tosay = "So, do you want to chat or play a game? Just say 'chat' if you just want to talk or say 'game' if you want to play."
            self.data_queue.put((self.config.imagelist[1], tosay, "Introduction"))
            await self.audio_manager.play_audio('thechoice.mp3')  # Tosay prerecorded
            self.data_queue.put((self.config.idleimage, tosay, "Introduction"))
            user_message_file = await self.audio_manager.record_audio(duration=5)
            userTalk = self.model_manager.transcribe_audio(user_message_file)

            if re.search(gamepattern, userTalk):
                gametoPlay = random.choice(self.config.gameAI)
                gameword = self.config.game_words.get(gametoPlay)
                game_result = await self.game_manager.game_loop(gameword, gametoPlay)
                if game_result == "WIN":
                    print("You win")
                    messageAfterWin = "You've won! Congratulations. Say 'quit' in the next screen if you're finished"
                    await async_SpeakandSend(messageAfterWin, self.config.imagelist[1], "Thanks",self.data_queue,self.audio_manager,self.model_manager)
                    continue
                elif game_result == "QUIT":
                    print("Thanks for playing")
                    messageForQuitting = "Thanks for playing, too bad you couldn't guess it. Say 'quit' on the next screen if you're finished"
                    await async_SpeakandSend(messageForQuitting, self.config.imagelist[1], "Thanks",self.data_queue,self.audio_manager,self.model_manager)
                    continue
            elif re.search(chatpattern, userTalk):
                await self.chat_manager.chat_loop()
                chatEndMessage = "That was a nice chat. If you want to stop, just say quit on your next turn."
                self.data_queue.put((self.config.imagelist[1], chatEndMessage, "Thanks"))
                await self.audio_manager.play_audio("chatend.mp3")
            elif re.search(quitpattern, userTalk):
                break

        self.gui_manager.stop()

    def run(self):
        # Start the GUI in a separate thread
        tkinter_thread = threading.Thread(target=self.gui_manager.start)
        tkinter_thread.start()

        # Start the main loop in the main thread
        asyncio.run(self.main())

if __name__ == "__main__":
    agent = FinalAgent()
    agent.run()
