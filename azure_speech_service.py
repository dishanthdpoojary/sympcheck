"""
Azure Speech-to-Text service integration (Fixed version)
"""

import os
import requests
import json
from typing import Optional, Dict, Any
import logging
from audio_converter import AudioConverter

logger = logging.getLogger(__name__)

class AzureSpeechService:
    """
    Service for Azure Speech-to-Text integration
    """
    
    def __init__(self):
        self.api_key = os.getenv('AZURE_SPEECH_API_KEY')
        self.region = os.getenv('AZURE_SPEECH_REGION', 'eastus2')
        self.base_url = f"https://{self.region}.stt.speech.microsoft.com"
        
        if not self.api_key:
            logger.warning("AZURE_SPEECH_API_KEY not found in environment variables")
    
    def transcribe_audio(self, audio_file_path: str, language: str = "en-US") -> Optional[str]:
        """
        Transcribe audio file to text using Azure Speech-to-Text
        
        Args:
            audio_file_path: Path to the audio file
            language: Language code (default: en-US)
            
        Returns:
            Transcribed text or None if error
        """
        if not self.api_key:
            logger.error("Azure Speech API key not available")
            return None
        
        try:
            # Convert audio to WAV format if needed
            logger.info(f"Processing audio file: {audio_file_path}")
            audio_info = AudioConverter.get_audio_info(audio_file_path)
            logger.info(f"Audio file info: {audio_info}")
            
            # Convert to WAV format for Azure Speech-to-Text
            wav_path = AudioConverter.convert_to_wav(audio_file_path)
            if not wav_path:
                logger.error("Failed to convert audio to WAV format")
                return None
            
            # Azure Speech-to-Text REST API endpoint
            url = f"{self.base_url}/speech/recognition/conversation/cognitiveservices/v1"
            
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key,
                'Content-Type': 'audio/wav; codecs=audio/pcm; samplerate=16000',
                'Accept': 'application/json'
            }
            
            params = {
                'language': language,
                'format': 'detailed'
            }
            
            # Read converted audio file
            with open(wav_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            response = requests.post(
                url,
                headers=headers,
                params=params,
                data=audio_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Azure API response: {result}")
                transcribed_text = None
                
                if 'DisplayText' in result:
                    transcribed_text = result['DisplayText'].strip()
                elif 'NBest' in result and len(result['NBest']) > 0:
                    transcribed_text = result['NBest'][0]['Display'].strip()
                else:
                    logger.error(f"Unexpected response format: {result}")
                
                # Clean up temporary WAV file if it was created
                if wav_path != audio_file_path and os.path.exists(wav_path):
                    os.unlink(wav_path)
                
                return transcribed_text
            else:
                logger.error(f"Azure Speech API error: {response.status_code} - {response.text}")
                
                # Clean up temporary WAV file if it was created
                if wav_path != audio_file_path and os.path.exists(wav_path):
                    os.unlink(wav_path)
                
                return None
                
        except FileNotFoundError:
            logger.error(f"Audio file not found: {audio_file_path}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            # Clean up temporary WAV file if it was created
            if 'wav_path' in locals() and wav_path != audio_file_path and os.path.exists(wav_path):
                os.unlink(wav_path)
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            # Clean up temporary WAV file if it was created
            if 'wav_path' in locals() and wav_path != audio_file_path and os.path.exists(wav_path):
                os.unlink(wav_path)
            return None
    
    def transcribe_audio_from_bytes(self, audio_bytes: bytes, language: str = "en-US") -> Optional[str]:
        """
        Transcribe audio from bytes to text using Azure Speech-to-Text
        
        Args:
            audio_bytes: Audio data as bytes
            language: Language code (default: en-US)
            
        Returns:
            Transcribed text or None if error
        """
        if not self.api_key:
            logger.error("Azure Speech API key not available")
            return None
        
        try:
            # Save audio bytes to temporary file for conversion
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.m4a', delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name
            
            try:
                # Convert to WAV format
                wav_path = AudioConverter.convert_to_wav(temp_path)
                if not wav_path:
                    logger.error("Failed to convert audio bytes to WAV format")
                    return None
                
                # Read converted audio
                with open(wav_path, 'rb') as f:
                    wav_data = f.read()
                
                # Azure Speech-to-Text REST API endpoint
                url = f"{self.base_url}/speech/recognition/conversation/cognitiveservices/v1"
                
                headers = {
                    'Ocp-Apim-Subscription-Key': self.api_key,
                    'Content-Type': 'audio/wav; codecs=audio/pcm; samplerate=16000',
                    'Accept': 'application/json'
                }
                
                params = {
                    'language': language,
                    'format': 'detailed'
                }
                
                response = requests.post(
                    url,
                    headers=headers,
                    params=params,
                    data=wav_data,
                    timeout=30
                )
            finally:
                # Clean up temporary files
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                if 'wav_path' in locals() and wav_path != temp_path and os.path.exists(wav_path):
                    os.unlink(wav_path)
            
            if response.status_code == 200:
                result = response.json()
                if 'DisplayText' in result:
                    return result['DisplayText'].strip()
                elif 'NBest' in result and len(result['NBest']) > 0:
                    return result['NBest'][0]['Display'].strip()
                else:
                    logger.error(f"Unexpected response format: {result}")
                    return None
            else:
                logger.error(f"Azure Speech API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test if the Azure Speech API connection is working
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Test with a simple request to check if the endpoint is accessible
            url = f"{self.base_url}/speech/recognition/conversation/cognitiveservices/v1"
            
            headers = {
                'Ocp-Apim-Subscription-Key': self.api_key,
                'Accept': 'application/json'
            }
            
            # Make a simple GET request to test connectivity
            response = requests.get(url, headers=headers, timeout=10)
            
            # Even if we get an error, if it's not a 404, the endpoint exists
            return response.status_code != 404
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
