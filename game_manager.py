# game_manager.py
import re
from utils import async_SpeakandSend, set_image
from audio_manager import AudioManager
from llm_manager import LLMManager
from model_manager import ModelManager
from config import Config
import requests
import random

class GameManager:
    def __init__(self, config, data_queue, audio_manager, llm_manager, model_manager):
        self.config = config
        self.data_queue = data_queue
        self.audio_manager = audio_manager
        self.llm_manager = llm_manager
        self.model_manager = model_manager
        self.history = []

    async def game_loop(self, exitword, character):
        self.llm_manager.clear_history()  # Clear history before starting a new game
        self.history = []
        gameTitle = 'Guessing Game'
        pattern = re.compile(r'(yes|okay)\b', re.IGNORECASE)

        intro = "I am thinking of a word... For our game, you will try to guess it while I give hints. You can also ask questions while you guess. Do you understand? Say yes or okay to continue."
        await self.game_introduction(intro, pattern)

        intro_Hint = self.generate_hint(exitword)
        fullHint = "I'm thinking of a thing. Your goal is to guess it. Here's your first hint: What I'm thinking of is " + intro_Hint
        self.llm_manager.history.append({"role": "assistant", "content": fullHint})
        self.history.append({"role": "assistant", "content": fullHint})

        await async_SpeakandSend(fullHint, self.config.imagelist[1], gameTitle, self.data_queue, self.audio_manager, self.model_manager)
        return await self.guessing_loop(exitword,character,gameTitle)

    async def game_introduction(self, intro, pattern):
        while True:
            self.data_queue.put((self.config.imagelist[1], intro, "Gameplay Introduction"))
            print(intro)
            await self.audio_manager.play_audio('gameintro.mp3')  # prerecorded for response time
            self.data_queue.put((self.config.idleimage, intro, "Gameplay Introduction"))
            user_message_file = await self.audio_manager.record_audio(duration=5)  # Recording for 5 seconds
            transcribed_text = self.model_manager.transcribe_audio(user_message_file)
            if pattern.search(transcribed_text):
                break

    def generate_hint(self, exitword):
        if exitword == 'apple':
            return "smooth and can fit in your hand"
        elif exitword == 'shark':
            return "something with sharp teeth and lives in the sea."
        elif exitword == 'sharing':
            return "an act you do to those who have less than you."
        else:
            return "something interesting"

    async def guessing_loop(self, exitword, character,gameTitle):
      exit_pattern = re.compile(r'(exit|quit|{})\b'.format(exitword), re.IGNORECASE)
      exitingWord = re.compile(r'({})'.format(exitword), re.IGNORECASE)
      while True:
          user_message_file = await self.audio_manager.record_audio(duration=8)  # Recording for X seconds
          user_message = self.model_manager.transcribe_audio(user_message_file)
          if exit_pattern.search(user_message): 
              self.llm_manager.save_history()
              if exitingWord.search(user_message):
                  return "WIN"
              else: 
                  return "QUIT"
          self.history.append({"role": "user", "content": user_message})
          data = {
              "mode": "chat-instruct",
              "instruction_template":"zephyr3b0",
              "preset":"Big O",
              "character": character,
              "messages": self.history
          }
          await self.audio_manager.play_audio(random.choice(self.config.fillersounds),blocking=False)
          response = requests.post(self.config.llm_url, headers=self.config.llm_headers, json=data, verify=False)
          assistant_message = response.json()['choices'][0]['message']['content']
          if exitingWord.search(assistant_message):
                self.llm_manager.save_history()
                self.history.append({"role":"SYSTEM","content": "GENERATED TEXT HAS HIDDEN WORD IN IT. USER NEEDS TO GUESS NOW"})
                self.llm_manager.history.append({"role":"SYSTEM","content": "GENERATED TEXT HAS HIDDEN WORD IN IT. USER NEEDS TO GUESS NOW"})
                self.llm_manager.save_history()
                result = await self.final_guess(exitword)
                return result               
          self.history.append({"role": "assistant", "content": assistant_message})
          self.llm_manager.history.append({"role": "assistant", "content": assistant_message})
          selectedimage = set_image(self.config)
          print(assistant_message)
          success = await async_SpeakandSend(assistant_message,selectedimage, gameTitle, self.data_queue,self.audio_manager,self.model_manager)

    async def final_guess(self, toGuess):
        wordToGuess = re.compile(r'({})'.format(toGuess), re.IGNORECASE)
        selectedimage = set_image(self.config)
        finalSay = "Hmm. It seems like you're close enough to what I'm thinking of that I can't give anymore hints or answer anymore questions. Here's your last chance. What word was I thinking?"
        await async_SpeakandSend(finalSay,selectedimage, "Final Guess",self.data_queue,self.audio_manager,self.model_manager)
        user_message_file = await self.audio_manager.record_audio(duration=8)
        user_message = self.model_manager.transcribe_audio(user_message_file)
        
        if wordToGuess.search(user_message):
            userwins = "I think I heard you say {}, that's the word I was thinking of congratulations!".format(toGuess)
            await async_SpeakandSend(userwins,selectedimage,"WINNING GUESS",self.data_queue,self.audio_manager,self.model_manager)
            return "WIN"
        else:
            userwrong = "I'm sorry. That is not the word that I was thinking of. The right answer was {}".format(toGuess)
            await async_SpeakandSend(userwrong,selectedimage,"WRONG GUESS",self.data_queue,self.audio_manager,self.model_manager)
            return "QUIT"
