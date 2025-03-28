# Improved GUI Manager with Error Handling
import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import threading
import queue
import time
import os
import asyncio
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_log.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("GUIManager")

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
        try:
            self.root = tk.Tk()
            self.root.title("Alex the AI")
            self.root.geometry(f"{self.window_width}x{self.window_height}")
            
            # Add error handler for unexpected window closures
            self.root.protocol("WM_DELETE_WINDOW", self.handle_window_close)
            
            self.title_label = tk.Label(self.root, text="Alex the AI Agent", font=("Helvetica", 16, "bold"))
            self.title_label.pack(pady=10)

            splash_image_path = os.path.join(self.config.asset_dir, "titlescreen.png")
            if not os.path.exists(splash_image_path):
                logger.error(f"Splash image not found at {splash_image_path}")
                # Use a fallback image or create a blank one
                self.splashImg = Image.new('RGB', (400, 300), color='white')
                logger.info("Using fallback blank image")
            else:
                self.splashImg = Image.open(splash_image_path)
            
            self.splashPhoto = ImageTk.PhotoImage(self.splashImg)

            self.image_label = tk.Label(self.root, image=self.splashPhoto)
            self.image_label.pack()

            self.text_label = tk.Label(self.root, text="For: Development of Computer Agent for Child-Robot Symbolic Anthropomorphism", wraplength=750)
            self.text_label.pack()
            
            logger.info("GUI setup completed successfully")
            
        except tk.TclError as e:
            logger.error(f"Tkinter error during setup: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during GUI setup: {e}")
            raise

    def handle_window_close(self):
        """Handle when user closes the window"""
        logger.info("Window close requested by user")
        self.stop_update = True
        self.root.destroy()
        # You might want to signal to the main program that GUI has been closed
        self.data_queue.put(("", "GUI_CLOSED", ""))

    async def update_gui(self):
        """Asynchronous function to update the GUI"""
        logger.info("Starting GUI update loop")
        update_count = 0
        last_error_time = 0
        error_threshold = 5  # Max consecutive errors
        error_count = 0
        
        while not self.stop_update:
            try:
                # Process all messages in the queue
                processed = 0
                while not self.data_queue.empty() and processed < 10:  # Limit processing to avoid blocking
                    try:
                        image_name, text, title = self.data_queue.get_nowait()
                        # Check for special control message
                        if text == "GUI_CLOSED":
                            logger.info("Received GUI_CLOSED signal")
                            return
                            
                        if image_name.lower().endswith('.gif'):
                            self.clear_gif()
                        else:
                            self.clear_image()
                        
                        image_path = self.get_image(image_name)
                        if image_path:
                            self.display_image(image_path)
                        else:
                            logger.warning(f"Image {image_name} not found")
                            # Use a default image
                            default_image = self.get_image(self.config.imagelist[0])
                            if default_image:
                                self.display_image(default_image)
                                
                        self.title_label.config(text=title)
                        self.text_label.config(text=text)
                        self.text_label.config(wraplength=700)
                        processed += 1
                    except queue.Empty:
                        break
                    except Exception as e:
                        logger.error(f"Error processing queue item: {e}")
                        # Continue processing other items
                        continue
                
                # Update tkinter - this is the key to make it work with asyncio
                if self.root:
                    self.root.update()
                    update_count += 1
                    if update_count % 100 == 0:  # Log every 100 updates (about every 10 seconds)
                        logger.debug(f"GUI updated {update_count} times")
                    # Reset error count on successful update
                    error_count = 0
                else:
                    logger.error("Root window is None, stopping update loop")
                    break
                    
            except tk.TclError as e:
                if "application has been destroyed" in str(e):
                    logger.info("GUI has been destroyed, stopping update loop")
                    break
                else:
                    error_count += 1
                    current_time = time.time()
                    # Only log errors if they're not too frequent
                    if current_time - last_error_time > 5:
                        logger.error(f"Tkinter error during update: {e}")
                        last_error_time = current_time
                    
                    if error_count > error_threshold:
                        logger.critical(f"Too many consecutive errors ({error_count}), stopping GUI")
                        break
            except Exception as e:
                logger.error(f"Unexpected error in GUI update: {e}")
                error_count += 1
                if error_count > error_threshold:
                    logger.critical(f"Too many errors ({error_count}), stopping GUI")
                    break
            
            # Small delay to prevent hogging the CPU
            await asyncio.sleep(0.1)
        
        logger.info("GUI update loop ended")

    def start(self):
        """Setup the GUI - this doesn't block"""
        try:
            self.setup()
            logger.info("GUI started successfully")
        except Exception as e:
            logger.error(f"Failed to start GUI: {e}")
            # Create a simple error message window instead
            try:
                error_root = tk.Tk()
                error_root.title("Error Starting Application")
                error_label = tk.Label(error_root, text=f"Error starting application: {e}", wraplength=400)
                error_label.pack(padx=20, pady=20)
                error_root.mainloop()
            except:
                logger.critical("Failed to create error window, giving up on GUI")

    def stop(self):
        logger.info("GUI stop requested")
        self.stop_update = True
        if self.root:
            try:
                self.root.destroy()
                logger.info("GUI destroyed successfully")
            except tk.TclError:
                logger.warning("GUI was already destroyed")
            except Exception as e:
                logger.error(f"Error destroying GUI: {e}")

    def clear_image(self):
        try:
            self.image_label.config(image="")
            self.image_label.image = None
        except Exception as e:
            logger.error(f"Error clearing image: {e}")

    def display_image(self, image_path):
        try:
            if not image_path:
                logger.warning("Attempted to display None image_path")
                return
                
            if image_path.lower().endswith('.gif'):
                self.display_animated_gif(image_path)
            else:
                img = Image.open(image_path)
                photo = ImageTk.PhotoImage(img)
                self.image_label.config(image=photo)
                self.image_label.image = photo
        except FileNotFoundError:
            logger.error(f"Image file not found: {image_path}")
        except Exception as e:
            logger.error(f"Error displaying image {image_path}: {e}")

    def get_gif_duration(self, image_path):
        try:
            img = Image.open(image_path)
            return img.info.get('duration', 100)
        except (AttributeError, KeyError):
            return 100
        except Exception as e:
            logger.error(f"Error getting GIF duration: {e}")
            return 100

    def display_animated_gif(self, image_path):
        try:
            img = Image.open(image_path)
            frames = [ImageTk.PhotoImage(frame) for frame in ImageSequence.Iterator(img)]
            duration = self.get_gif_duration(image_path)
            min_delay = 200

            def update_frame(idx=0):
                try:
                    nonlocal duration, min_delay
                    if self.stop_update or not self.root:
                        return  # Don't schedule more frames if stopping
                    
                    self.image_label.config(image=frames[idx])
                    self.image_label.image = frames[idx]
                    idx = (idx + 1) % len(frames)
                    delay = max(min_delay, int(duration / len(frames)))
                    frame_id = self.root.after(delay, update_frame, idx)
                    self.image_label.frame_id = frame_id
                except Exception as e:
                    logger.error(f"Error updating GIF frame: {e}")

            update_frame()
        except Exception as e:
            logger.error(f"Error displaying animated GIF {image_path}: {e}")

    def clear_gif(self):
        try:
            if hasattr(self.image_label, 'frame_id'):
                self.root.after_cancel(self.image_label.frame_id)
            self.clear_image()
        except Exception as e:
            logger.error(f"Error clearing GIF: {e}")
    
    def get_image(self, file_name):
        try:
            image_path = os.path.join(os.getcwd(), self.config.asset_dir, file_name)
            if not os.path.exists(image_path):
                logger.warning(f"Image file not found: {image_path}")
                return None
            return image_path
        except Exception as e:
            logger.error(f"Error getting image path for {file_name}: {e}")
            return None