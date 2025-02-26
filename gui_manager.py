# gui_manager.py
import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import threading
import queue
import time
import os

class GUIManager:
    def __init__(self, config, data_queue):
        self.config = config
        self.data_queue = data_queue
        self.root = tk.Tk()
        self.root.title("Alex the AI")
        self.window_width = 800
        self.window_height = 700
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.stop_update = False

        self.title_label = tk.Label(self.root, text="Alex the AI Agent", font=("Helvetica", 16, "bold"))
        self.title_label.pack(pady=10)

        self.splashImg = Image.open(os.path.join(self.config.asset_dir, "titlescreen.png"))
        self.splashPhoto = ImageTk.PhotoImage(self.splashImg)

        self.image_label = tk.Label(self.root, image=self.splashPhoto)
        self.image_label.pack()

        self.text_label = tk.Label(self.root, text="For: Development of Computer Agent for Child-Robot Symbolic Anthropomorphism", wraplength=750)
        self.text_label.pack()
        
        self.frame_id = None
        
        self.update_thread = threading.Thread(target=self.update_labels)
        self.update_thread.daemon = True
        self.update_thread.start()

    def start(self):
      self.root.mainloop()

    def stop(self):
      self.stop_update = True
      self.root.destroy()
    
    def update_labels(self):
      while not self.stop_update:
        try:
          image_name, text, title = self.data_queue.get(timeout=1)
          if image_name.lower().endswith('.gif'):
            self.clear_gif()
          else:
            self.clear_image()
          image_path = self.get_image(image_name)
          self.display_image(image_path)
          self.title_label.config(text=title)
          self.text_label.config(text=text)
          self.text_label.config(wraplength=700)
          self.root.update_idletasks()
          time.sleep(2)
          self.root.update_idletasks()
        except queue.Empty:
          pass
      self.root.destroy()

    def clear_image(self):
      self.image_label.config(image="")
      self.image_label.image = None

    def display_image(self, image_path):
        if image_path.lower().endswith('.gif'):
            self.display_animated_gif(image_path)
        else:
            img = Image.open(image_path)
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo)
            self.image_label.image = photo

    def get_gif_duration(self, image_path):
        img = Image.open(image_path)
        try:
            return img.info.get('duration', 100)
        except (AttributeError, KeyError):
            return 100

    def display_animated_gif(self, image_path):
        img = Image.open(image_path)
        frames = [ImageTk.PhotoImage(frame) for frame in ImageSequence.Iterator(img)]
        duration = self.get_gif_duration(image_path)
        min_delay = 200

        def update_frame(idx=0):
            nonlocal duration, min_delay
            self.image_label.config(image=frames[idx])
            self.image_label.image = frames[idx]
            idx = (idx + 1) % len(frames)
            delay = max(min_delay, int(duration / len(frames)))
            frame_id = self.root.after(delay, update_frame, idx)
            self.image_label.frame_id = frame_id

        update_frame()

    def clear_gif(self):
        if hasattr(self.image_label, 'frame_id'):
            self.root.after_cancel(self.image_label.frame_id)
        self.clear_image()
    
    def get_image(self, file_name):
      try:
          image_path = os.path.join(os.getcwd(), self.config.asset_dir, file_name)
          return image_path
      except FileNotFoundError:
          print("Error: Image file not found at the specified path.")
          return None
