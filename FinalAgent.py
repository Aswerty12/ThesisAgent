# FinalAgent.py - Improved error handling
import asyncio
import re
import random
import queue
import logging
import time
import sys
import traceback
from config import Config
from audio_manager import AudioManager
from model_manager import ModelManager
from gui_manager import GUIManager
from llm_manager import LLMManager
from game_manager import GameManager
from chat_manager import ChatManager
from utils import async_Speak, async_Send

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_log.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("FinalAgent")

class FinalAgent:
    def __init__(self):
        try:
            logger.info("Initializing Final Agent")
            self.config = Config()
            self.data_queue = queue.Queue()  # Queue for communication with GUI
            self.audio_manager = AudioManager(self.config)
            self.model_manager = ModelManager(self.config)
            self.gui_manager = GUIManager(self.config, self.data_queue)
            self.llm_manager = LLMManager(self.config)
            self.game_manager = GameManager(self.config, self.data_queue, self.audio_manager, self.llm_manager, self.model_manager)
            self.chat_manager = ChatManager(self.config, self.data_queue, self.audio_manager, self.llm_manager, self.model_manager)
            logger.info("Final Agent initialized successfully")
        except Exception as e:
            logger.critical(f"Failed to initialize FinalAgent: {e}")
            traceback.print_exc()
            sys.exit(1)
    
    async def introduction(self):
        try:
            logger.info("Starting introduction sequence")
            # Prerecorded Introduction
            # This is the illusory agent that only responds with canned audio and logic
            pattern = re.compile(r'(yes|okay)\b', re.IGNORECASE)
            placeholder = self.config.imagelist[1]
            introtitle = "Introduction"

            # That's a wonderful name. It's great to meet you. I'm here to talk with you for a while.
            # Split the async calls into async speak and send
            try:
                audio = self.model_manager.generate_speech("Before we introduce ourselves you should know how to talk with me.")
                await async_Speak(audio, self.model_manager.config.tts_sample_rate)
                await async_Send(placeholder, "Before we introduce ourselves you should know how to talk with me.", introtitle, self.data_queue)
            except Exception as e:
                logger.error(f"Error in introduction initial speech: {e}")
                # Continue with default text if speech fails
                await async_Send(placeholder, "Before we introduce ourselves you should know how to talk with me.", introtitle, self.data_queue)
            
            attempts = 0
            max_attempts = 3
            
            while attempts < max_attempts:
                try:
                    await async_Send(placeholder, 'You will hear a series of sounds, this indicates that you can speak.', introtitle, self.data_queue)
                    await self.audio_manager.play_audio('test_1.mp3')
                    # You will hear a series of sounds, this indicates that you can speak
                    await self.audio_manager.play_audio("game-start.mp3")
                    # SFX for starting
                    await async_Send(placeholder, 'Meanwhile this is the sound for when you should stop talking.', introtitle, self.data_queue)
                    await self.audio_manager.play_audio('test_2.mp3')
                    # Meanwhile this is the sound for when you should stop talking
                    await self.audio_manager.play_audio("negative_beeps.mp3")
                    # SFX For Stopping
                    await async_Send(placeholder, "Do you understand? Just say yes if you want to continue with the game. Otherwise I'll explain again", introtitle, self.data_queue)
                    await self.audio_manager.play_audio('test_3.mp3')
                    await async_Send(self.config.idleimage, "Do you understand? Just say yes if you want to continue with the game. Otherwise I'll explain again", introtitle, self.data_queue)
                    # Do you understand? Just say yes if you want to continue with the game. Otherwise I'll explain again
                    
                    try:
                        user_message_file = await self.audio_manager.record_audio(duration=5)  # Recording for X seconds
                        if user_message_file:
                            user_message = self.model_manager.transcribe_audio(user_message_file)
                            logger.info(f"User response: {user_message}")
                            if pattern.search(user_message):
                                break
                    except Exception as e:
                        logger.error(f"Error in audio recording or transcription: {e}")
                        # If recording fails, give the user another chance
                        await async_Send(placeholder, "I didn't catch that. Let's try again.", introtitle, self.data_queue)
                    
                    attempts += 1
                    
                except Exception as e:
                    logger.error(f"Error in introduction explanation loop: {e}")
                    attempts += 1
                    # Brief pause before retry
                    await asyncio.sleep(1)
            
            try:
                audio = self.model_manager.generate_speech("Anyway, Greetings my name is Alex, what's your name?")
                await async_Speak(audio, self.model_manager.config.tts_sample_rate)
                await async_Send(placeholder, "Anyway, Greetings my name is Alex, what's your name?", introtitle, self.data_queue)
                await self.audio_manager.record_audio(duration=8)
                audio = self.model_manager.generate_speech("That's a wonderful name. It's great to meet you. I'm here to talk with you for a while.")
                await async_Speak(audio, self.model_manager.config.tts_sample_rate)
                await async_Send(placeholder, "That's a wonderful name. It's great to meet you. I'm here to talk with you for a while.", introtitle, self.data_queue)
            except Exception as e:
                logger.error(f"Error in introduction name exchange: {e}")
                # Fallback if speech generation fails
                await async_Send(placeholder, "That's a wonderful name. It's great to meet you. I'm here to talk with you for a while.", introtitle, self.data_queue)
                
            logger.info("Introduction sequence completed")
            
        except Exception as e:
            logger.error(f"Error in introduction: {e}")
            # Display error message to user
            await async_Send(self.config.imagelist[0], "Sorry, I encountered an issue during introduction. Let's continue anyway.", "Error", self.data_queue)
    
    async def main(self):
        try:
            logger.info("Starting main application loop")
            # Start the GUI update coroutine
            gui_task = asyncio.create_task(self.gui_manager.update_gui())
            
            # Add a simple watchdog task to monitor the GUI
            watchdog_task = asyncio.create_task(self.gui_watchdog())
            
            intro = "Hello. I am an A.I. program running inside of this computer. Let's talk and chat for a while."
            gamepattern = re.compile(r'game', re.IGNORECASE)
            chatpattern = re.compile(r'chat', re.IGNORECASE)
            quitpattern = re.compile(r'quit', re.IGNORECASE)
            
            try:
                audio = self.model_manager.generate_speech(intro)
                await async_Speak(audio, self.model_manager.config.tts_sample_rate)
                await async_Send(self.config.imagelist[1], intro, "Intro", self.data_queue)
            except Exception as e:
                logger.error(f"Error in initial greeting: {e}")
                # Continue without audio if it fails
                await async_Send(self.config.imagelist[1], intro, "Intro", self.data_queue)
            
            try:
                await self.introduction()
            except Exception as e:
                logger.error(f"Introduction sequence failed: {e}")
                # Try to recover and continue
                await async_Send(self.config.imagelist[1], 
                                "Let's continue with our conversation.", 
                                "Moving forward", 
                                self.data_queue)
            
            # Main interaction loop
            max_errors = 3
            consecutive_errors = 0
            
            while consecutive_errors < max_errors:
                try:
                    tosay = "So, do you want to chat or play a game? Just say 'chat' if you just want to talk or say 'game' if you want to play."
                    await async_Send(self.config.imagelist[1], tosay, "Introduction", self.data_queue)
                    
                    try:
                        await self.audio_manager.play_audio('thechoice.mp3')  # Tosay prerecorded
                    except Exception as e:
                        logger.error(f"Failed to play audio: {e}")
                        # Try to use TTS as fallback
                        try:
                            audio = self.model_manager.generate_speech(tosay)
                            await async_Speak(audio, self.model_manager.config.tts_sample_rate)
                        except:
                            logger.error("Both audio playback methods failed")
                    
                    await async_Send(self.config.idleimage, tosay, "Introduction", self.data_queue)
                    
                    # Handle possible recording failure
                    try:
                        user_message_file = await self.audio_manager.record_audio(duration=5)
                        if not user_message_file:
                            raise Exception("Failed to record audio")
                            
                        userTalk = self.model_manager.transcribe_audio(user_message_file)
                        logger.info(f"User said: {userTalk}")
                        
                        # Reset error counter on successful interaction
                        consecutive_errors = 0
                    except Exception as e:
                        logger.error(f"Error recording or transcribing user input: {e}")
                        await async_Send(self.config.imagelist[1], 
                                      "I didn't catch that. Let's try again.", 
                                      "Error", 
                                      self.data_queue)
                        consecutive_errors += 1
                        continue

                    if re.search(gamepattern, userTalk):
                        try:
                            gametoPlay = random.choice(self.config.gameAI)
                            gameword = self.config.game_words.get(gametoPlay)
                            logger.info(f"Starting game: {gametoPlay} with word: {gameword}")
                            game_result = await self.game_manager.game_loop(gameword, gametoPlay)
                            
                            if game_result == "WIN":
                                logger.info("User won the game")
                                messageAfterWin = "You've won! Congratulations. Say 'quit' in the next screen if you're finished"
                                try:
                                    audio = self.model_manager.generate_speech(messageAfterWin)
                                    await async_Speak(audio, self.model_manager.config.tts_sample_rate)
                                except Exception as e:
                                    logger.error(f"Error generating win speech: {e}")
                                    
                                await async_Send(self.config.imagelist[1], messageAfterWin, "Thanks", self.data_queue)
                                continue
                            elif game_result == "QUIT":
                                logger.info("User quit the game")
                                messageForQuitting = "Thanks for playing, too bad you couldn't guess it. Say 'quit' on the next screen if you're finished"
                                try:
                                    audio = self.model_manager.generate_speech(messageForQuitting)
                                    await async_Speak(audio, self.model_manager.config.tts_sample_rate)
                                except Exception as e:
                                    logger.error(f"Error generating quit speech: {e}")
                                    
                                await async_Send(self.config.imagelist[1], messageForQuitting, "Thanks", self.data_queue)
                                continue
                        except Exception as e:
                            logger.error(f"Error in game loop: {e}")
                            await async_Send(self.config.imagelist[1], 
                                         "Sorry, there was a problem with the game. Let's try something else.", 
                                         "Game Error", 
                                         self.data_queue)
                            consecutive_errors += 1
                            
                    elif re.search(chatpattern, userTalk):
                        try:
                            logger.info("Starting chat loop")
                            await self.chat_manager.chat_loop()
                            chatEndMessage = "That was a nice chat. If you want to stop, just say quit on your next turn."
                            await async_Send(self.config.imagelist[1], chatEndMessage, "Thanks", self.data_queue)
                            
                            try:
                                await self.audio_manager.play_audio("chatend.mp3")
                            except Exception as e:
                                logger.error(f"Failed to play chat end audio: {e}")
                                # Try TTS fallback
                                try:
                                    audio = self.model_manager.generate_speech(chatEndMessage)
                                    await async_Speak(audio, self.model_manager.config.tts_sample_rate)
                                except:
                                    pass
                        except Exception as e:
                            logger.error(f"Error in chat loop: {e}")
                            await async_Send(self.config.imagelist[1], 
                                         "Sorry, we had a problem with our chat. Let's try again.", 
                                         "Chat Error", 
                                         self.data_queue)
                            consecutive_errors += 1
                            
                    elif re.search(quitpattern, userTalk):
                        logger.info("User requested to quit")
                        break
                    else:
                        await async_Send(self.config.imagelist[1], 
                                     "I didn't understand. Please say 'chat' to talk or 'game' to play a game.", 
                                     "Unclear Input", 
                                     self.data_queue)
                
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    consecutive_errors += 1
                    # Brief pause before continuing
                    await asyncio.sleep(1)
            
            # If we exited due to too many errors
            if consecutive_errors >= max_errors:
                logger.critical(f"Too many consecutive errors ({consecutive_errors}), shutting down")
                await async_Send(self.config.imagelist[0], 
                             "I'm having some technical difficulties. Let's try again later.", 
                             "System Error", 
                             self.data_queue)
                await asyncio.sleep(3)  # Give user time to read the message
            
            # Cleanup tasks
            logger.info("Shutting down tasks")
            for task in [gui_task, watchdog_task]:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            self.gui_manager.stop()
            logger.info("Main loop completed")
            
        except Exception as e:
            logger.critical(f"Critical error in main function: {e}")
            traceback.print_exc()
            # Try to display error message if GUI is still working
            try:
                await async_Send(self.config.imagelist[0], 
                             "A system error occurred. The program needs to restart.", 
                             "System Error", 
                             self.data_queue)
                await asyncio.sleep(3)
            except:
                pass
            # Make sure GUI is stopped
            try:
                self.gui_manager.stop()
            except:
                pass
    
    async def gui_watchdog(self):
        """Monitor the GUI and restart if necessary"""
        while True:
            try:
                # Check if GUI is responding
                if self.gui_manager.root is None or not self.gui_manager.root.winfo_exists():
                    logger.warning("GUI window no longer exists, attempting to restart")
                    try:
                        self.gui_manager.stop()
                        await asyncio.sleep(1)
                        self.gui_manager.start()
                        logger.info("GUI restarted successfully")
                    except Exception as e:
                        logger.error(f"Failed to restart GUI: {e}")
                        # If we can't restart GUI, put a message in the queue anyway
                        # The main loop will see this and know to exit
                        self.data_queue.put(("", "GUI_CLOSED", ""))
                        break
            except Exception as e:
                logger.error(f"Error in GUI watchdog: {e}")
            
            await asyncio.sleep(5)  # Check every 5 seconds

    def run(self):
        try:
            logger.info("Starting application")
            # Setup the GUI but don't start mainloop
            self.gui_manager.start()
            # Run everything in asyncio
            asyncio.run(self.main())
            logger.info("Application completed normally")
        except Exception as e:
            logger.critical(f"Fatal error in run method: {e}")
            traceback.print_exc()
            # Ensure GUI is cleaned up
            try:
                self.gui_manager.stop()
            except:
                pass
            sys.exit(1)

if __name__ == "__main__":
    try:
        logger.info("Application starting")
        agent = FinalAgent()
        agent.run()
    except Exception as e:
        logger.critical(f"Unhandled exception at application root: {e}")
        traceback.print_exc()
        sys.exit(1)