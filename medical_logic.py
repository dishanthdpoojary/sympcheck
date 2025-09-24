"""
Medical logic and conversation flow management for the chatbot
Handles the 3-question flow and diagnosis generation
"""

import re
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class MedicalLogic:
    """
    Handles the medical conversation logic and flow
    """
    
    def __init__(self):
        self.max_questions = 3
        
        # Common symptom patterns for better initial detection
        self.symptom_patterns = {
            'headache': ['headache', 'head pain', 'head ache', 'migraine'],
            'fever': ['fever', 'temperature', 'hot', 'burning up'],
            'cough': ['cough', 'coughing', 'hack'],
            'pain': ['pain', 'hurt', 'ache', 'sore'],
            'nausea': ['nausea', 'nauseous', 'sick to stomach', 'queasy'],
            'fatigue': ['tired', 'fatigue', 'exhausted', 'weak'],
            'dizziness': ['dizzy', 'dizziness', 'lightheaded', 'vertigo']
        }
    
    def process_message(self, user_message: str, conversation_state: Dict[str, Any], groq_client) -> Dict[str, Any]:
        """
        Process user message and return bot response with updated conversation state
        
        Args:
            user_message: The user's input message
            conversation_state: Current conversation state
            groq_client: Groq API client instance
            
        Returns:
            Dictionary containing bot_message and updated conversation_state
        """
        try:
            # Clean and normalize the message
            normalized_message = self._normalize_message(user_message)
            
            # Determine if this is the first message (initial symptom)
            if conversation_state['question_number'] == 0:
                return self._handle_initial_symptom(normalized_message, conversation_state, groq_client)
            else:
                return self._handle_follow_up_response(normalized_message, conversation_state, groq_client)
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return self._create_error_response(conversation_state)
    
    def _handle_initial_symptom(self, message: str, conversation_state: Dict[str, Any], groq_client) -> Dict[str, Any]:
        """
        Handle the initial symptom message and generate first follow-up question
        """
        # Extract and store the initial symptom
        symptom = self._extract_symptom(message)
        conversation_state['initial_symptom'] = symptom
        conversation_state['question_number'] = 1
        
        # Generate first follow-up question
        question = self._generate_follow_up_question(symptom, 1, [], groq_client)
        
        if not question:
            question = self._get_fallback_question(symptom, 1)
        
        return {
            'bot_message': question,
            'conversation_state': conversation_state
        }
    
    def _handle_follow_up_response(self, message: str, conversation_state: Dict[str, Any], groq_client) -> Dict[str, Any]:
        """
        Handle follow-up responses and determine next action
        """
        current_question = conversation_state['question_number']
        
        # Store the answer
        conversation_state['answers'].append(message)
        
        # Check if we've reached the maximum number of questions
        if current_question >= self.max_questions:
            # Generate diagnosis
            diagnosis = self._generate_diagnosis(conversation_state, groq_client)
            conversation_state['is_complete'] = True
            
            return {
                'bot_message': diagnosis,
                'conversation_state': conversation_state
            }
        else:
            # Generate next follow-up question
            next_question_num = current_question + 1
            question = self._generate_follow_up_question(
                conversation_state['initial_symptom'],
                next_question_num,
                conversation_state['answers'],
                groq_client
            )
            
            if not question:
                question = self._get_fallback_question(conversation_state['initial_symptom'], next_question_num)
            
            conversation_state['question_number'] = next_question_num
            
            return {
                'bot_message': question,
                'conversation_state': conversation_state
            }
    
    def _extract_symptom(self, message: str) -> str:
        """
        Extract the main symptom from the user's message
        """
        message_lower = message.lower()
        
        # Check for specific symptom patterns
        for symptom_type, patterns in self.symptom_patterns.items():
            for pattern in patterns:
                if pattern in message_lower:
                    return symptom_type
        
        # If no specific pattern found, return the original message (cleaned)
        return self._clean_symptom_text(message)
    
    def _clean_symptom_text(self, text: str) -> str:
        """
        Clean and normalize symptom text
        """
        # Remove common prefixes
        prefixes_to_remove = ['i have', 'i am experiencing', 'i feel', 'i got', 'i\'m having']
        
        text_lower = text.lower().strip()
        for prefix in prefixes_to_remove:
            if text_lower.startswith(prefix):
                text_lower = text_lower[len(prefix):].strip()
                break
        
        # Capitalize first letter
        return text_lower.capitalize() if text_lower else text
    
    def _normalize_message(self, message: str) -> str:
        """
        Normalize user message for processing
        """
        # Remove extra whitespace
        message = re.sub(r'\s+', ' ', message.strip())
        
        # Handle common variations
        message = message.replace('yes', 'yes').replace('no', 'no')
        message = message.replace('y', 'yes').replace('n', 'no')
        
        return message
    
    def _generate_follow_up_question(self, symptom: str, question_number: int, previous_answers: list, groq_client) -> Optional[str]:
        """
        Generate a follow-up question using Groq API
        """
        try:
            return groq_client.generate_follow_up_question(symptom, question_number, previous_answers)
        except Exception as e:
            logger.error(f"Error generating follow-up question: {str(e)}")
            return None
    
    def _generate_diagnosis(self, conversation_state: Dict[str, Any], groq_client) -> str:
        """
        Generate diagnosis using Groq API
        """
        try:
            diagnosis = groq_client.generate_diagnosis(
                conversation_state['initial_symptom'],
                conversation_state['answers']
            )
            
            if diagnosis:
                return diagnosis
            else:
                return self._get_fallback_diagnosis(conversation_state)
                
        except Exception as e:
            logger.error(f"Error generating diagnosis: {str(e)}")
            return self._get_fallback_diagnosis(conversation_state)
    
    def _get_fallback_question(self, symptom: str, question_number: int) -> str:
        """
        Get fallback questions when Groq API is unavailable
        """
        fallback_questions = {
            1: [
                "How long have you been experiencing this symptom?",
                "Can you describe the severity of your symptoms?",
                "When did you first notice this problem?"
            ],
            2: [
                "Are you experiencing any other symptoms along with this?",
                "Have you taken any medication or tried any treatments?",
                "What makes your symptoms better or worse?"
            ],
            3: [
                "How is this affecting your daily activities?",
                "Have you experienced something similar before?",
                "Is there anything else you'd like me to know about your condition?"
            ]
        }
        
        questions = fallback_questions.get(question_number, ["How are you feeling now?"])
        return questions[0]  # Return the first fallback question
    
    def _get_fallback_diagnosis(self, conversation_state: Dict[str, Any]) -> str:
        """
        Get fallback diagnosis when Groq API is unavailable
        """
        symptom = conversation_state['initial_symptom']
        answers = conversation_state['answers']
        
        return f"""Based on your symptoms of {symptom} and your responses ({', '.join(answers)}), 
        I recommend that you:
        
        1. Monitor your symptoms closely
        2. Get adequate rest and stay hydrated
        3. Consider over-the-counter pain relief if appropriate
        4. Consult with a healthcare professional if symptoms persist or worsen
        
        This is general advice only. Please seek professional medical attention for proper diagnosis and treatment."""
    
    def _create_error_response(self, conversation_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an error response when processing fails
        """
        return {
            'bot_message': "I'm sorry, I'm having trouble processing your message right now. Please try again or consult a healthcare professional for immediate assistance.",
            'conversation_state': conversation_state
        }
