# gui_manager.py - Modified
import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import threading
import queue
import time
import os
import asyncio

class GUIManager:
    def __init__(self, config, data_queue):
        self.config = config
        self.data_queue = data_queue
        self.root = None
        self.window_width = 800
        self.window_height = 700
        self.stop_update = False
        self.title_label = None
        self.image_label = None
        self.text_label = None
        self.splashPhoto = None
        self.frame_id = None
        
    def setup(self):
        """Setup the GUI elements but don't start mainloop"""
        self.root = tk.Tk()
        self.root.title("Alex the AI")
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        
        self.title_label = tk.Label(self.root, text="Alex the AI Agent", font=("Helvetica", 16, "bold"))
        self.title_label.pack(pady=10)

        self.splashImg = Image.open(os.path.join(self.config.asset_dir, "titlescreen.png"))
        self.splashPhoto = ImageTk.PhotoImage(self.splashImg)

        self.image_label = tk.Label(self.root, image=self.splashPhoto)
        self.image_label.pack()

        self.text_label = tk.Label(self.root, text="For: Development of Computer Agent for Child-Robot Symbolic Anthropomorphism", wraplength=750)
        self.text_label.pack()
        
        # Don't schedule update here - will be done in update_gui async function

    async def update_gui(self):
        """Asynchronous function to update the GUI"""
        while not self.stop_update:
            # Process all messages in the queue
            try:
                while True:
                    image_name, text, title = self.data_queue.get_nowait()
                    if image_name.lower().endswith('.gif'):
                        self.clear_gif()
                    else:
                        self.clear_image()
                    image_path = self.get_image(image_name)
                    self.display_image(image_path)
                    self.title_label.config(text=title)
                    self.text_label.config(text=text)
                    self.text_label.config(wraplength=700)
            except queue.Empty:
                pass  # No messages, continue
            except Exception as e:
                print(f"Error in updating labels {e}")
            
            # Update tkinter - this is the key to make it work with asyncio
            self.root.update()
            # Small delay to prevent hogging the CPU
            await asyncio.sleep(0.1)
            
    def start(self):
        """Setup the GUI - this doesn't block"""
        self.setup()

    def stop(self):
        self.stop_update = True
        if self.root:
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