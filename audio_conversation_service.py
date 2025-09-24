"""
Audio Conversation Service - Orchestrates the complete audio conversation flow
"""

import os
import tempfile
import logging
from typing import Optional, Dict, Any, Tuple
from azure_speech_service import AzureSpeechService
from groq_integration import GroqClient
from elevenlabs_service import ElevenLabsService

logger = logging.getLogger(__name__)

class AudioConversationService:
    """
    Service that orchestrates the complete audio conversation flow:
    1. Azure Speech-to-Text (transcribe patient audio)
    2. Groq Llama (process transcription and generate response)
    3. ElevenLabs Text-to-Speech (convert response to audio)
    """
    
    def __init__(self):
        self.azure_speech = AzureSpeechService()
        self.groq_client = GroqClient()
        self.elevenlabs_service = ElevenLabsService()
        self.conversation_history = []
    
    def process_audio_conversation(self, audio_file_path: str, language: str = "en-US") -> Dict[str, Any]:
        """
        Process a complete audio conversation cycle
        
        Args:
            audio_file_path: Path to the patient's audio file
            language: Language code for speech recognition
            
        Returns:
            Dictionary containing:
            - success: bool
            - transcribed_text: str
            - ai_response: str
            - audio_response_path: str (path to generated audio)
            - error: str (if any)
        """
        result = {
            'success': False,
            'transcribed_text': '',
            'ai_response': '',
            'audio_response_path': '',
            'error': ''
        }
        
        try:
            # Step 1: Transcribe audio to text using Azure Speech-to-Text
            logger.info("Step 1: Transcribing audio to text...")
            transcribed_text = self.azure_speech.transcribe_audio(audio_file_path, language)
            
            if not transcribed_text:
                result['error'] = "Failed to transcribe audio"
                return result
            
            result['transcribed_text'] = transcribed_text
            logger.info(f"Transcribed text: {transcribed_text}")
            
            # Step 2: Generate AI response using Groq Llama
            logger.info("Step 2: Generating AI response...")
            ai_response = self.groq_client.generate_audio_conversation_response(
                transcribed_text, 
                self.conversation_history
            )
            
            if not ai_response:
                result['error'] = "Failed to generate AI response"
                return result
            
            result['ai_response'] = ai_response
            logger.info(f"AI response: {ai_response}")
            
            # Step 3: Convert AI response to audio using ElevenLabs
            logger.info("Step 3: Converting response to audio...")
            audio_response_path = self._generate_audio_response(ai_response)
            
            if not audio_response_path:
                result['error'] = "Failed to generate audio response"
                return result
            
            result['audio_response_path'] = audio_response_path
            logger.info(f"Audio response saved to: {audio_response_path}")
            
            # Update conversation history
            self._update_conversation_history(transcribed_text, ai_response)
            
            result['success'] = True
            return result
            
        except Exception as e:
            logger.error(f"Error in audio conversation processing: {str(e)}")
            result['error'] = f"Processing error: {str(e)}"
            return result
    
    def process_audio_conversation_from_bytes(self, audio_bytes: bytes, language: str = "en-US") -> Dict[str, Any]:
        """
        Process a complete audio conversation cycle from audio bytes
        
        Args:
            audio_bytes: Audio data as bytes
            language: Language code for speech recognition
            
        Returns:
            Dictionary containing:
            - success: bool
            - transcribed_text: str
            - ai_response: str
            - audio_response_bytes: bytes (generated audio data)
            - error: str (if any)
        """
        result = {
            'success': False,
            'transcribed_text': '',
            'ai_response': '',
            'audio_response_bytes': b'',
            'error': ''
        }
        
        try:
            # Step 1: Transcribe audio to text using Azure Speech-to-Text
            logger.info("Step 1: Transcribing audio to text...")
            transcribed_text = self.azure_speech.transcribe_audio_from_bytes(audio_bytes, language)
            
            if not transcribed_text:
                result['error'] = "Failed to transcribe audio"
                return result
            
            result['transcribed_text'] = transcribed_text
            logger.info(f"Transcribed text: {transcribed_text}")
            
            # Step 2: Generate AI response using Groq Llama
            logger.info("Step 2: Generating AI response...")
            ai_response = self.groq_client.generate_audio_conversation_response(
                transcribed_text, 
                self.conversation_history
            )
            
            if not ai_response:
                result['error'] = "Failed to generate AI response"
                return result
            
            result['ai_response'] = ai_response
            logger.info(f"AI response: {ai_response}")
            
            # Step 3: Convert AI response to audio using ElevenLabs
            logger.info("Step 3: Converting response to audio...")
            audio_response_bytes = self.elevenlabs_service.text_to_speech(ai_response)
            
            if not audio_response_bytes:
                result['error'] = "Failed to generate audio response"
                return result
            
            result['audio_response_bytes'] = audio_response_bytes
            logger.info("Audio response generated successfully")
            
            # Update conversation history
            self._update_conversation_history(transcribed_text, ai_response)
            
            result['success'] = True
            return result
            
        except Exception as e:
            logger.error(f"Error in audio conversation processing: {str(e)}")
            result['error'] = f"Processing error: {str(e)}"
            return result
    
    def _generate_audio_response(self, text: str) -> Optional[str]:
        """
        Generate audio file from text response
        
        Args:
            text: Text to convert to audio
            
        Returns:
            Path to generated audio file or None if error
        """
        try:
            # Create temporary file for audio output
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # Generate audio
            audio_data = self.elevenlabs_service.text_to_speech(text, output_path=temp_path)
            
            if audio_data:
                return temp_path
            else:
                # Clean up temp file if generation failed
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                return None
                
        except Exception as e:
            logger.error(f"Error generating audio response: {str(e)}")
            return None
    
    def _update_conversation_history(self, user_input: str, ai_response: str):
        """
        Update conversation history with new exchange
        
        Args:
            user_input: User's transcribed text
            ai_response: AI's response text
        """
        self.conversation_history.append({
            'role': 'user',
            'content': user_input
        })
        self.conversation_history.append({
            'role': 'assistant',
            'content': ai_response
        })
        
        # Keep only last 10 exchanges to prevent context from getting too long
        if len(self.conversation_history) > 20:  # 10 exchanges = 20 messages
            self.conversation_history = self.conversation_history[-20:]
    
    def clear_conversation_history(self):
        """Clear the conversation history"""
        self.conversation_history = []
    
    def get_conversation_history(self) -> list:
        """Get the current conversation history"""
        return self.conversation_history.copy()
    
    def test_all_services(self) -> Dict[str, bool]:
        """
        Test all integrated services
        
        Returns:
            Dictionary with test results for each service
        """
        results = {
            'azure_speech': False,
            'groq_client': False,
            'elevenlabs_service': False
        }
        
        try:
            results['azure_speech'] = self.azure_speech.test_connection()
            results['groq_client'] = self.groq_client.test_connection()
            results['elevenlabs_service'] = self.elevenlabs_service.test_connection()
        except Exception as e:
            logger.error(f"Error testing services: {str(e)}")
        
        return results
