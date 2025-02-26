# chat_manager.py
import re
import random
from utils import async_SpeakandSend, set_image
from audio_manager import AudioManager
from llm_manager import LLMManager
from model_manager import ModelManager
from config import Config
import requests
class ChatManager:
    def __init__(self, config, data_queue, audio_manager, llm_manager, model_manager):
        self.config = config
        self.data_queue = data_queue
        self.audio_manager = audio_manager
        self.llm_manager = llm_manager
        self.model_manager = model_manager

    async def chat_loop(self):
        chatTitle = "Just Chatting"
        exit_pattern = re.compile(r'(exit|quit)\b', re.IGNORECASE)
        messageToSay = "Just ask any question, and I can answer it."
        await async_SpeakandSend(messageToSay, self.config.imagelist[1], chatTitle, self.data_queue, self.audio_manager, self.model_manager)

        while True:
            user_message_file = await self.audio_manager.record_audio(duration=7)
            user_message = self.model_manager.transcribe_audio(user_message_file)

            if exit_pattern.search(user_message):
                self.llm_manager.save_history()
                break

            self.llm_manager.history.append({"role": "user", "content": user_message})

            data = {
                "mode": "chat-instruct",
                "preset": "Midnight Enigma",
                "instruction_template": "zephyr3b0",
                "character": "AIver1",
                "messages": self.llm_manager.history
            }

            await self.audio_manager.play_audio(random.choice(self.config.fillersounds), blocking=False)
            response = requests.post(self.config.llm_url, headers=self.config.llm_headers, json=data, verify=False)
            assistant_message = response.json()['choices'][0]['message']['content']
            self.llm_manager.history.append({"role": "assistant", "content": assistant_message})
            selectedimage = set_image(self.config)
            print(assistant_message)
            success = await async_SpeakandSend(assistant_message, selectedimage, chatTitle, self.data_queue, self.audio_manager, self.model_manager)

