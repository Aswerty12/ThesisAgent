# config.py
class Config:
    def __init__(self):
      #API
      self.llm_url = "http://127.0.0.1:5001/v1/chat/completions"
      self.llm_headers = {
          "Content-Type": "application/json"
      }
      #Model
      self.stt_model_size = "small"
      self.stt_device = 'cpu'
      self.tts_language = 'en'
      self.tts_model_id = 'v3_en'
      self.tts_device = 'cpu'
      self.tts_sample_rate = 48000
      self.tts_speaker = 'en_21'
      self.tts_put_accent = True
      self.tts_put_yo = True
      #asset path
      self.asset_dir = "asset"
      #chathistory path
      self.chathistory_dir = "chathistory"
      #asset
      self.imagelist = ["talkinggirl.gif", "talkinggirl.gif"]
      self.idleimage = "thinking.gif"
      self.soundlist = ["game-start.mp3", "negative_beeps.mp3", "ping.mp3"]
      self.fillersounds = ["filleraudio0.mp3", "filleraudio1.mp3", "filleraudio2.mp3", "filleraudio3.mp3", "filleraudio4.mp3"]
      #Game related
      self.gameAI = ["AIverApple", "AIverSharing", "AIverShark"]
      self.game_words = {
          "AIverApple": "apple",
          "AIverSharing": "sharing",
          "AIverShark": "shark"
      }

