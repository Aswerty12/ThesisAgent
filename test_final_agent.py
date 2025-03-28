import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio
import queue
import re
import tempfile
from config import Config
from audio_manager import AudioManager
from model_manager import ModelManager
from gui_manager import GUIManager
from llm_manager import LLMManager
from game_manager import GameManager
from chat_manager import ChatManager
from utils import async_SpeakandSend
from FinalAgent import FinalAgent
import ffmpeg


class TestFinalAgent(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.config = Config()
        self.data_queue = queue.Queue()
        self.audio_manager = AudioManager(self.config)
        self.model_manager = ModelManager(self.config)
        self.llm_manager = LLMManager(self.config)

        # Mock GUIManager to avoid GUI interactions during tests
        self.gui_manager = MagicMock(spec=GUIManager)
        self.gui_manager.stop = MagicMock()

        self.game_manager = GameManager(self.config, self.data_queue, self.audio_manager, self.llm_manager,
                                        self.model_manager)
        self.chat_manager = ChatManager(self.config, self.data_queue, self.audio_manager, self.llm_manager,
                                        self.model_manager)
        self.agent = FinalAgent()
        self.agent.config = self.config
        self.agent.data_queue = self.data_queue
        self.agent.audio_manager = self.audio_manager
        self.agent.model_manager = self.model_manager
        self.agent.gui_manager = self.gui_manager
        self.agent.llm_manager = self.llm_manager
        self.agent.game_manager = self.game_manager
        self.agent.chat_manager = self.chat_manager

    @patch.object(ffmpeg, 'input')
    @patch.object(AudioManager, 'play_audio', new_callable=AsyncMock)
    @patch.object(AudioManager, 'record_audio', new_callable=AsyncMock)
    @patch.object(ModelManager, 'transcribe_audio')
    @patch('utils.async_SpeakandSend', new_callable=AsyncMock)
    async def test_introduction(self, mock_async_speak, mock_transcribe, mock_record, mock_play, mock_ffmpeg):
        mock_transcribe.return_value = "yes"  # Simulate user saying "yes"
        mock_record.return_value = "recorded_audio.wav"  # Return a dummy filename
        mock_process = MagicMock()
        mock_process.communicate = MagicMock()
        mock_ffmpeg.return_value.output.return_value.overwrite_output.return_value.run_async.return_value = mock_process
        await self.agent.introduction()
        self.assertEqual(mock_play.call_count, 8)
        self.assertEqual(mock_record.call_count, 2)
        self.assertEqual(mock_transcribe.call_count, 1)
        self.assertEqual(mock_async_speak.call_count, 4)

    @patch.object(ffmpeg, 'input')
    @patch.object(AudioManager, 'play_audio', new_callable=AsyncMock)
    @patch.object(AudioManager, 'record_audio', new_callable=AsyncMock)
    @patch.object(ModelManager, 'transcribe_audio')
    @patch.object(GameManager, 'game_loop', new_callable=AsyncMock)
    @patch.object(ChatManager, 'chat_loop', new_callable=AsyncMock)
    @patch('utils.async_SpeakandSend', new_callable=AsyncMock)
    async def test_main_game_flow(self, mock_async_speak, mock_chat_loop, mock_game_loop, mock_transcribe, mock_record,
                                  mock_play, mock_ffmpeg):
        mock_transcribe.side_effect = ["game", "exit"]
        mock_record.return_value = "recorded_audio.wav"
        mock_game_loop.return_value = "QUIT"
        mock_process = MagicMock()
        mock_process.communicate = MagicMock()
        mock_ffmpeg.return_value.output.return_value.overwrite_output.return_value.run_async.return_value = mock_process
        await self.agent.main()
        mock_game_loop.assert_called_once()
        self.assertEqual(mock_transcribe.call_count, 3)
        self.assertEqual(mock_async_speak.call_count, 5)
        self.gui_manager.stop.assert_called_once()

    @patch.object(ffmpeg, 'input')
    @patch.object(AudioManager, 'play_audio', new_callable=AsyncMock)
    @patch.object(AudioManager, 'record_audio', new_callable=AsyncMock)
    @patch.object(ModelManager, 'transcribe_audio')
    @patch.object(GameManager, 'game_loop', new_callable=AsyncMock)
    @patch.object(ChatManager, 'chat_loop', new_callable=AsyncMock)
    @patch('utils.async_SpeakandSend', new_callable=AsyncMock)
    async def test_main_chat_flow(self, mock_async_speak, mock_chat_loop, mock_game_loop, mock_transcribe, mock_record,
                                  mock_play, mock_ffmpeg):
        mock_transcribe.side_effect = ["chat", "quit"]
        mock_record.return_value = "recorded_audio.wav"
        mock_chat_loop.return_value = None
        mock_process = MagicMock()
        mock_process.communicate = MagicMock()
        mock_ffmpeg.return_value.output.return_value.overwrite_output.return_value.run_async.return_value = mock_process
        await self.agent.main()

        mock_chat_loop.assert_called_once()
        mock_game_loop.assert_not_called()
        self.assertEqual(mock_transcribe.call_count, 3)
        self.assertEqual(mock_async_speak.call_count, 5)
        self.gui_manager.stop.assert_called_once()

    @patch.object(ffmpeg, 'input')
    @patch.object(AudioManager, 'play_audio', new_callable=AsyncMock)
    @patch.object(AudioManager, 'record_audio', new_callable=AsyncMock)
    @patch.object(ModelManager, 'transcribe_audio')
    @patch.object(GameManager, 'game_loop', new_callable=AsyncMock)
    @patch.object(ChatManager, 'chat_loop', new_callable=AsyncMock)
    @patch('utils.async_SpeakandSend', new_callable=AsyncMock)
    async def test_main_quit_flow(self, mock_async_speak, mock_chat_loop, mock_game_loop, mock_transcribe, mock_record,
                                  mock_play, mock_ffmpeg):
        mock_transcribe.side_effect = ["quit"]
        mock_record.return_value = "recorded_audio.wav"
        mock_process = MagicMock()
        mock_process.communicate = MagicMock()
        mock_ffmpeg.return_value.output.return_value.overwrite_output.return_value.run_async.return_value = mock_process
        await self.agent.main()

        mock_chat_loop.assert_not_called()
        mock_game_loop.assert_not_called()
        self.assertEqual(mock_transcribe.call_count, 2)
        self.assertEqual(mock_async_speak.call_count, 4)
        self.gui_manager.stop.assert_called_once()

    @patch.object(ffmpeg, 'input')
    @patch.object(AudioManager, 'play_audio', new_callable=AsyncMock)
    @patch.object(AudioManager, 'record_audio', new_callable=AsyncMock)
    @patch.object(ModelManager, 'transcribe_audio')
    @patch.object(GameManager, 'game_loop', new_callable=AsyncMock)
    @patch.object(ChatManager, 'chat_loop', new_callable=AsyncMock)
    @patch('utils.async_SpeakandSend', new_callable=AsyncMock)
    async def test_main_game_win(self, mock_async_speak, mock_chat_loop, mock_game_loop, mock_transcribe, mock_record,
                                 mock_play, mock_ffmpeg):
        mock_transcribe.side_effect = ["game", "quit"]
        mock_record.return_value = "recorded_audio.wav"
        mock_game_loop.return_value = "WIN"
        mock_process = MagicMock()
        mock_process.communicate = MagicMock()
        mock_ffmpeg.return_value.output.return_value.overwrite_output.return_value.run_async.return_value = mock_process
        await self.agent.main()
        mock_game_loop.assert_called_once()
        self.assertEqual(mock_transcribe.call_count, 3)
        self.assertEqual(mock_async_speak.call_count, 5)
        self.gui_manager.stop.assert_called_once()


class TestUtils(unittest.IsolatedAsyncioTestCase):
    @patch('sounddevice.play')
    @patch('sounddevice.wait')
    @patch.object(ModelManager, 'generate_speech')
    @patch.object(queue.Queue, 'put')
    async def test_async_speak_and_send(self, mock_queue_put, mock_generate_speech, mock_sd_wait, mock_sd_play):
        # Arrange
        mock_config = MagicMock()
        mock_model_manager = ModelManager(mock_config)
        mock_audio_manager = MagicMock()
        mock_data_queue = queue.Queue()
        text_to_speak = "Hello, world!"
        queued_art = "test.png"
        queued_title = "Test Title"
        mock_generated_audio = [1, 2, 3]

        mock_generate_speech.return_value = mock_generated_audio
        mock_config.idleimage = "idle.gif"
        mock_config.tts_sample_rate = 48000
        # Act
        await async_SpeakandSend(text_to_speak, queued_art, queued_title, mock_data_queue, mock_audio_manager,
                                 mock_model_manager)

        # Assert
        mock_generate_speech.assert_called_once_with(text_to_speak)
        mock_queue_put.assert_called()
        self.assertEqual(mock_queue_put.call_count, 2)
        mock_sd_play.assert_called_once_with(mock_generated_audio, mock_config.tts_sample_rate)
        mock_sd_wait.assert_called_once()


if __name__ == '__main__':
    unittest.main()
