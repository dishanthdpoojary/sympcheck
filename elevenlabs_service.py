"""
ElevenLabs Text-to-Speech service integration
"""

import os
import requests
import json
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ElevenLabsService:
    """
    Service for ElevenLabs Text-to-Speech integration
    """
    
    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        self.base_url = "https://api.elevenlabs.io/v1"
        self.default_voice_id = os.getenv('ELEVENLABS_VOICE_ID', 'pNInz6obpgDQGcFmaJgB')  # Default voice ID
        
        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY not found in environment variables")
    
    def text_to_speech(self, text: str, voice_id: Optional[str] = None, output_path: Optional[str] = None) -> Optional[bytes]:
        """
        Convert text to speech using ElevenLabs API
        
        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use (defaults to configured voice)
            output_path: Optional path to save the audio file
            
        Returns:
            Audio data as bytes or None if error
        """
        if not self.api_key:
            logger.error("ElevenLabs API key not available")
            return None
        
        if not text.strip():
            logger.error("Empty text provided for TTS")
            return None
        
        try:
            voice_id = voice_id or self.default_voice_id
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            headers = {
                'Accept': 'audio/mpeg',
                'Content-Type': 'application/json',
                'xi-api-key': self.api_key
            }
            
            payload = {
                'text': text,
                'model_id': 'eleven_monolingual_v1',
                'voice_settings': {
                    'stability': 0.5,
                    'similarity_boost': 0.5
                }
            }
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                audio_data = response.content
                
                # Save to file if output_path is provided
                if output_path:
                    with open(output_path, 'wb') as f:
                        f.write(audio_data)
                    logger.info(f"Audio saved to: {output_path}")
                
                return audio_data
            else:
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None
    
    def get_available_voices(self) -> Optional[list]:
        """
        Get list of available voices from ElevenLabs
        
        Returns:
            List of available voices or None if error
        """
        if not self.api_key:
            logger.error("ElevenLabs API key not available")
            return None
        
        try:
            url = f"{self.base_url}/voices"
            
            headers = {
                'Accept': 'application/json',
                'xi-api-key': self.api_key
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('voices', [])
            else:
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None
    
    def get_voice_info(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific voice
        
        Args:
            voice_id: Voice ID to get information for
            
        Returns:
            Voice information dictionary or None if error
        """
        if not self.api_key:
            logger.error("ElevenLabs API key not available")
            return None
        
        try:
            url = f"{self.base_url}/voices/{voice_id}"
            
            headers = {
                'Accept': 'application/json',
                'xi-api-key': self.api_key
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test if the ElevenLabs API connection is working
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Test with a simple text
            result = self.text_to_speech("Hello, this is a test.")
            return result is not None
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
