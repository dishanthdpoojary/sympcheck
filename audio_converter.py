"""
Audio format conversion utilities for Azure Speech-to-Text compatibility
"""

import os
import tempfile
import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class AudioConverter:
    """
    Utility class for converting audio formats to Azure Speech-to-Text compatible formats
    """
    
    @staticmethod
    def convert_to_wav(input_path: str, output_path: Optional[str] = None) -> Optional[str]:
        """
        Convert audio file to WAV format compatible with Azure Speech-to-Text
        
        Args:
            input_path: Path to input audio file
            output_path: Optional output path (if None, creates temp file)
            
        Returns:
            Path to converted WAV file or None if conversion failed
        """
        try:
            if output_path is None:
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                output_path = temp_file.name
                temp_file.close()
            
            # Try using ffmpeg if available
            try:
                cmd = [
                    'ffmpeg', '-i', input_path,
                    '-ar', '16000',  # Sample rate 16kHz
                    '-ac', '1',      # Mono
                    '-acodec', 'pcm_s16le',  # 16-bit PCM
                    '-y',            # Overwrite output file
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and os.path.exists(output_path):
                    logger.info(f"Audio converted successfully: {input_path} -> {output_path}")
                    return output_path
                else:
                    logger.error(f"FFmpeg conversion failed: {result.stderr}")
                    
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                logger.warning(f"FFmpeg not available or timeout: {e}")
            
            # Fallback: try to use the original file if it's already WAV
            if input_path.lower().endswith('.wav'):
                logger.info("Input file is already WAV format, using as-is")
                return input_path
            
            # If no conversion method available, return None
            logger.error("No audio conversion method available")
            return None
            
        except Exception as e:
            logger.error(f"Audio conversion error: {str(e)}")
            return None
    
    @staticmethod
    def is_wav_format(file_path: str) -> bool:
        """
        Check if file is in WAV format
        
        Args:
            file_path: Path to audio file
            
        Returns:
            True if file is WAV format
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(12)
                # Check for WAV file signature
                return header[:4] == b'RIFF' and header[8:12] == b'WAVE'
        except Exception:
            return False
    
    @staticmethod
    def get_audio_info(file_path: str) -> dict:
        """
        Get basic audio file information
        
        Args:
            file_path: Path to audio file
            
        Returns:
            Dictionary with audio file information
        """
        info = {
            'format': 'unknown',
            'size': 0,
            'exists': False
        }
        
        try:
            if os.path.exists(file_path):
                info['exists'] = True
                info['size'] = os.path.getsize(file_path)
                
                # Check file extension
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.wav', '.m4a', '.mp3', '.aac', '.ogg']:
                    info['format'] = ext[1:]  # Remove the dot
                    
        except Exception as e:
            logger.error(f"Error getting audio info: {str(e)}")
            
        return info
