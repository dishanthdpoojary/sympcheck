"""
Groq API integration for AI-powered medical chatbot responses
"""

import os
import requests
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class GroqClient:
    """
    Client for interacting with Groq API
    """
    
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = "meta-llama/llama-4-scout-17b-16e-instruct"  # Using Llama 4 Scout model
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not found in environment variables")
    
    def generate_response(self, prompt: str, max_tokens: int = 150) -> Optional[str]:
        """
        Generate a response using Groq API
        
        Args:
            prompt: The input prompt for the AI
            max_tokens: Maximum number of tokens in the response
            
        Returns:
            Generated response text or None if error
        """
        if not self.api_key:
            logger.error("Groq API key not available")
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'system',
                        'content': self._get_system_prompt()
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': max_tokens,
                'temperature': 0.7,
                'top_p': 1,
                'stream': False
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
            else:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Response parsing error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None
    
    def generate_audio_conversation_response(self, transcribed_text: str, conversation_history: list = None) -> Optional[str]:
        """
        Generate a response for audio conversation based on transcribed text
        
        Args:
            transcribed_text: Text transcribed from patient's audio
            conversation_history: Previous conversation messages
            
        Returns:
            Generated response text or None if error
        """
        if not self.api_key:
            logger.error("Groq API key not available")
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Build conversation messages
            messages = [
                {
                    'role': 'system',
                    'content': self._get_audio_conversation_system_prompt()
                }
            ]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user message
            messages.append({
                'role': 'user',
                'content': transcribed_text
            })
            
            payload = {
                'model': self.model,
                'messages': messages,
                'max_tokens': 200,
                'temperature': 0.7,
                'top_p': 1,
                'stream': False
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
            else:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Response parsing error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None
    
    def generate_follow_up_question(self, symptom: str, question_number: int, previous_answers: list) -> Optional[str]:
        """
        Generate a follow-up question based on the initial symptom and previous answers
        
        Args:
            symptom: The initial symptom mentioned by the user
            question_number: Current question number (1, 2, or 3)
            previous_answers: List of previous answers
            
        Returns:
            Generated follow-up question or None if error
        """
        prompt = f"""
        You are a helpful medical assistant. The user mentioned they have: "{symptom}"
        
        Previous answers: {', '.join(previous_answers) if previous_answers else 'None'}
        
        Generate question #{question_number} to help assess their condition. 
        The question should be:
        - Natural and conversational (not yes/no format)
        - Open-ended to encourage detailed responses
        - Specific to their symptoms
        - Helpful for medical assessment
        - Easy to understand
        
        Examples of good questions:
        - "How long have you been experiencing this?"
        - "Can you describe what the pain feels like?"
        - "Are there any other symptoms you've noticed?"
        - "What makes it better or worse?"
        
        Return only the question, no additional text.
        """
        
        return self.generate_response(prompt, max_tokens=100)
    
    def generate_diagnosis(self, symptom: str, answers: list) -> Optional[str]:
        """
        Generate a diagnosis or health suggestion based on symptoms and answers
        
        Args:
            symptom: The initial symptom
            answers: List of all answers provided
            
        Returns:
            Generated diagnosis/suggestion or None if error
        """
        prompt = f"""
        You are a medical assistant. Based on the following information, provide a helpful diagnosis or health suggestion:
        
        Initial symptom: {symptom}
        Answers to follow-up questions: {', '.join(answers)}
        
        Provide:
        1. A possible diagnosis or condition
        2. General health advice
        3. When to seek medical attention
        
        Keep it concise, helpful, and always recommend consulting a healthcare professional for proper diagnosis.
        """
        
        return self.generate_response(prompt, max_tokens=200)
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the medical assistant
        """
        return """You are a helpful medical assistant chatbot. Your role is to:
        
        1. Ask relevant follow-up questions to understand symptoms better
        2. Provide general health information and suggestions
        3. Always recommend consulting healthcare professionals for proper diagnosis
        4. Be empathetic, clear, and concise in your responses
        5. Focus on common conditions and general health advice
        6. Never provide specific medical diagnoses or treatment recommendations
        
        Remember: You are not a replacement for professional medical advice."""
    
    def _get_audio_conversation_system_prompt(self) -> str:
        """
        Get the system prompt for audio conversation
        """
        return """You are a helpful medical assistant conducting an audio conversation with a patient. Your role is to:
        
1. Listen carefully to what the patient is saying about their symptoms
2. Ask relevant follow-up questions to understand their condition better
3. Provide empathetic and supportive responses
4. Give general health information and suggestions
5. Always recommend consulting healthcare professionals for proper diagnosis
6. Keep responses conversational and natural for audio interaction
7. Be concise but thorough in your responses
8. Never provide specific medical diagnoses or treatment recommendations

Remember: You are not a replacement for professional medical advice. Keep responses under 2-3 sentences for better audio experience."""

    def analyze_image_with_groq(self, image_base64: str) -> Optional[str]:
        """
        Analyze an image using Groq's vision capabilities
        
        Args:
            image_base64: Base64 encoded image data
            
        Returns:
            Image analysis text or None if error
        """
        if not self.api_key:
            logger.error("Groq API key not available")
            return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'system',
                        'content': """You are a medical assistant analyzing a patient's photo for visible symptoms. 
                        Look for any visible signs, rashes, swelling, discoloration, or other physical symptoms.
                        Provide a brief, helpful analysis of what you can observe in the image.
                        Be specific about what you see and focus on medically relevant observations."""
                    },
                    {
                        'role': 'user',
                        'content': [
                            {
                                'type': 'text',
                                'text': 'Please analyze this medical photo for any visible symptoms or signs that might be relevant for medical assessment.'
                            },
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f'data:image/jpeg;base64,{image_base64}'
                                }
                            }
                        ]
                    }
                ],
                'max_tokens': 200,
                'temperature': 0.7
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    analysis = result['choices'][0]['message']['content'].strip()
                    logger.info(f"Image analysis generated: {analysis[:100]}...")
                    return analysis
                else:
                    logger.error("No image analysis generated from Groq")
                    return None
            else:
                logger.error(f"Groq API error for image analysis: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error analyzing image with Groq: {str(e)}")
            return None

    def generate_photo_audio_response(self, image_analysis: str, audio_transcription: str) -> Optional[str]:
        """
        Generate a concise medical response based on both image analysis and audio transcription
        
        Args:
            image_analysis: Analysis of the uploaded image
            audio_transcription: Transcribed text from the audio
            
        Returns:
            Concise AI response or None if error
        """
        if not self.api_key:
            logger.warning("Groq API key not available or invalid, using fallback response")
            return self._generate_fallback_photo_audio_response(image_analysis, audio_transcription)
        
        try:
            system_prompt = self._get_photo_audio_system_prompt()
            
            user_message = f"""Based on the following information, provide a concise 2-3 line medical response:

IMAGE ANALYSIS:
{image_analysis}

AUDIO TRANSCRIPTION:
{audio_transcription}

Please provide a brief, helpful response that combines insights from both the visual and audio information. Keep it concise and actionable."""

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': "meta-llama/llama-4-scout-17b-16e-instruct",
                'messages': [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                'max_tokens': 150,  # Keep response concise
                'temperature': 0.7
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    ai_response = result['choices'][0]['message']['content'].strip()
                    logger.info(f"Photo+audio response generated: {ai_response[:100]}...")
                    return ai_response
                else:
                    logger.error("No response generated from Groq")
                    return self._generate_fallback_photo_audio_response(image_analysis, audio_transcription)
            else:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                return self._generate_fallback_photo_audio_response(image_analysis, audio_transcription)
                
        except Exception as e:
            logger.error(f"Error generating photo+audio response: {str(e)}")
            return self._generate_fallback_photo_audio_response(image_analysis, audio_transcription)

    def _generate_fallback_photo_audio_response(self, image_analysis: str, audio_transcription: str) -> str:
        """
        Generate a fallback response when Groq API is not available
        
        Args:
            image_analysis: Analysis of the uploaded image
            audio_transcription: Transcribed text from the audio
            
        Returns:
            Fallback medical response
        """
        # Simple rule-based response generation
        if "transcribed" in audio_transcription.lower() and "could not be" in audio_transcription.lower():
            # Audio transcription failed
            if "image received" in image_analysis.lower():
                return "I've received your photo and will consider it in the assessment. Please ensure your audio is clear and contains speech for better analysis. I recommend consulting a healthcare professional for proper evaluation."
            else:
                return "I've received your submission. Please ensure your audio is clear and contains speech for better analysis. I recommend consulting a healthcare professional for proper evaluation."
        else:
            # Audio transcription succeeded
            if "image received" in image_analysis.lower():
                return f"Based on your description: '{audio_transcription[:100]}...', I've also received your photo for consideration. I recommend consulting a healthcare professional for proper evaluation and guidance."
            else:
                return f"Based on your description: '{audio_transcription[:100]}...', I recommend consulting a healthcare professional for proper evaluation and guidance."

    def _get_photo_audio_system_prompt(self) -> str:
        """
        Get the system prompt for photo+audio analysis
        """
        return """You are a helpful medical assistant analyzing both visual and audio information from a patient. Your role is to:

1. Combine insights from both the image analysis and audio description
2. Provide a concise, helpful response (2-3 lines maximum)
3. Focus on the most relevant observations and recommendations
4. Always recommend consulting healthcare professionals for proper diagnosis
5. Be empathetic and supportive in your response
6. Never provide specific medical diagnoses or treatment recommendations
7. Keep the response actionable and easy to understand

Remember: You are not a replacement for professional medical advice. Provide a brief, helpful response that combines both visual and audio information."""
    
    def test_connection(self) -> bool:
        """
        Test if the Groq API connection is working
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            response = self.generate_response("Hello, are you working?", max_tokens=10)
            return response is not None
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
