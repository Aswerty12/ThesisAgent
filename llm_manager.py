# llm_manager.py
import requests
import json
import os
from datetime import datetime

class LLMManager:
    def __init__(self, config):
        self.config = config
        self.history = []

    def send_prompt(self, user_message, character,preset="Midnight Enigma",instruction_template="zephyr3b0",mode="chat-instruct"):
        self.history.append({"role": "user", "content": user_message})
        data = {
            "mode": mode,
            "preset":preset,
            "instruction_template":instruction_template,
            "character": character,
            "messages": self.history
        }
        response = requests.post(self.config.llm_url, headers=self.config.llm_headers, json=data, verify=False)
        assistant_message = response.json()['choices'][0]['message']['content']
        self.history.append({"role": "assistant", "content": assistant_message})
        return assistant_message

    def save_history(self):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"chat_history_{timestamp}.txt"
        file_path = os.path.join(os.getcwd(), self.config.chathistory_dir, file_name)
        with open(file_path, 'w') as file:
            json.dump(self.history, file, indent=4)

    def clear_history(self):
      self.history = []
