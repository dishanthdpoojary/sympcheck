from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
from dotenv import load_dotenv
from twilio.rest import Client
import os
import json
from datetime import datetime, timezone
from groq_integration import GroqClient
from conversation_manager import ConversationManager
from medical_logic import MedicalLogic
from audio_conversation_service import AudioConversationService
import tempfile

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, origins=['*'], methods=['GET', 'POST'], allow_headers=['Content-Type', 'Authorization'])

# Initialize rate limiter (10 requests per minute per IP)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["10 per minute"]
)

# Initialize components
groq_client = GroqClient()
conversation_manager = ConversationManager()
medical_logic = MedicalLogic()
audio_conversation_service = AudioConversationService()

# Simple in-memory cache for common responses
response_cache = {}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'medical-chatbot'
    })

@app.route('/chat', methods=['GET'])
def chat_info():
    return jsonify({
        'message': 'This is a POST endpoint. Use POST method to send messages.',
        'endpoint': '/chat',
        'method': 'POST',
        'example': {
            'message': 'I have a headache',
            'session_id': 'optional'
        }
    })

@app.route('/api/ai-response', methods=['GET'])
def ai_response_info():
    return jsonify({
        'message': 'This is a POST endpoint. Use POST method to send messages.',
        'endpoint': '/api/ai-response',
        'method': 'POST',
        'example': {
            'message': 'I have a headache'
        }
    })

@app.route('/api/chat', methods=['POST'])
def chat_api():
    return chat()

@app.route('/api/ai-response', methods=['POST'])
@limiter.limit("5 per minute")
def ai_response():
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message'].strip()
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        cache_key = f"ai_response_{user_message.lower().strip()}"
        if cache_key in response_cache:
            cached_response = response_cache[cache_key]
            return jsonify({
                'response': cached_response,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'ai_generated': True,
                'cached': True
            })

        # Updated rural-friendly prompt
        prompt = f"""
You are a kind and simple health helper for people in villages and rural areas.
A person has told you their health problem: "{user_message}"

Please give your answer in very easy and simple words, like you are talking to a friend.
Do not use big or hard medical words.

Your answer should include:
1. A simple idea of what might be happening in their body
2. Easy home advice or small steps they can try to feel better
3. Clear signs of when they should go and see a doctor, health worker, or go to the hospital

Always remind them kindly that only a doctor can give a sure answer.
"""

        ai_response_text = groq_client.generate_response(prompt, max_tokens=300)
        
        if ai_response_text:
            response_cache[cache_key] = ai_response_text
            return jsonify({
                'response': ai_response_text,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'ai_generated': True
            })
        else:
            return jsonify({
                'response': f"Thank you for describing your symptoms: {user_message}. Please visit a health worker or doctor for proper advice.",
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'ai_generated': False
            })
        
    except Exception as e:
        app.logger.error(f"Error in AI response endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/chat', methods=['POST'])
@limiter.limit("5 per minute")
def chat():
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        user_message = data['message'].strip()
        session_id = data.get('session_id', 'default')
        
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        conversation_state = conversation_manager.get_conversation(session_id)
        
        response = medical_logic.process_message(
            user_message=user_message,
            conversation_state=conversation_state,
            groq_client=groq_client
        )
        
        conversation_manager.update_conversation(session_id, response['conversation_state'])
        
        return jsonify({
            'response': response['bot_message'],
            'session_id': session_id,
            'question_number': response['conversation_state']['question_number'],
            'is_complete': response['conversation_state']['is_complete'],
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/reset', methods=['POST'])
def reset_conversation():
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        conversation_manager.reset_conversation(session_id)
        
        return jsonify({
            'message': 'Conversation reset successfully',
            'session_id': session_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Error resetting conversation: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/status/<session_id>', methods=['GET'])
def get_conversation_status(session_id):
    try:
        conversation_state = conversation_manager.get_conversation(session_id)
        
        return jsonify({
            'session_id': session_id,
            'conversation_state': conversation_state,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Error getting conversation status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/audio-conversation', methods=['POST'])
@limiter.limit("3 per minute")
def audio_conversation():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'Audio file is required'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        language = request.form.get('language', 'en-US')
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.m4a') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            result = audio_conversation_service.process_audio_conversation(temp_path, language)
            
            if result['success']:
                audio_response_path = result['audio_response_path']
                with open(audio_response_path, 'rb') as f:
                    audio_data = f.read()
                
                os.unlink(temp_path)
                os.unlink(audio_response_path)
                
                return Response(
                    audio_data,
                    mimetype='audio/mpeg',
                    headers={
                        'Content-Disposition': 'attachment; filename=response.mp3',
                        'X-Transcribed-Text': result['transcribed_text'],
                        'X-AI-Response': result['ai_response']
                    }
                )
            else:
                os.unlink(temp_path)
                app.logger.error(f"Audio conversation failed: {result['error']}")
                return jsonify({
                    'error': result['error'],
                    'details': 'Audio processing failed. Please check audio quality and try again.'
                }), 500
                
        except Exception as e:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
        
    except Exception as e:
        app.logger.error(f"Error in audio conversation endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/speech-to-text', methods=['POST'])
@limiter.limit("10 per minute")
def speech_to_text():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'Audio file is required'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        language = request.form.get('language', 'en-US')
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.m4a') as temp_file:
            audio_file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            from azure_speech_service import AzureSpeechService
            azure_speech = AzureSpeechService()
            transcribed_text = azure_speech.transcribe_audio(temp_path, language)
            
            os.unlink(temp_path)
            
            if transcribed_text:
                return jsonify({
                    'transcribed_text': transcribed_text,
                    'language': language,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            else:
                return jsonify({'error': 'Failed to transcribe audio'}), 500
                
        except Exception as e:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
        
    except Exception as e:
        app.logger.error(f"Error in speech-to-text endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/text-to-speech', methods=['POST'])
@limiter.limit("10 per minute")
def text_to_speech():
    try:
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'error': 'Text cannot be empty'}), 400
        
        voice_id = data.get('voice_id')
        
        from elevenlabs_service import ElevenLabsService
        elevenlabs_service = ElevenLabsService()
        audio_data = elevenlabs_service.text_to_speech(text, voice_id)
        
        if audio_data:
            return Response(
                audio_data,
                mimetype='audio/mpeg',
                headers={
                    'Content-Disposition': 'attachment; filename=speech.mp3'
                }
            )
        else:
            return jsonify({'error': 'Failed to generate speech'}), 500
        
    except Exception as e:
        app.logger.error(f"Error in text-to-speech endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/audio-services/status', methods=['GET'])
def audio_services_status():
    try:
        test_results = audio_conversation_service.test_all_services()
        
        return jsonify({
            'services': test_results,
            'all_working': all(test_results.values()),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Error checking audio services status: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/test-connection', methods=['GET'])
def test_connection():
    return jsonify({
        'status': 'connected',
        'message': 'Backend is reachable',
        'timestamp': datetime.now(timezone.utc).isoformat()
    })

@app.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded(e):
    return jsonify({
        'error': 'Rate limit exceeded. Please wait a moment before trying again.',
        'retry_after': str(e.retry_after) if hasattr(e, 'retry_after') else '60'
    }), 429

def send_whatsapp_alert(tonumber):
    """Send WhatsApp alert to a phone number"""
    try:
        from twilio.rest import Client
        import os
        
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        
        if not account_sid or not auth_token:
            print("Twilio credentials not found")
            return False
            
        client = Client(account_sid, auth_token)
        
        to_number = 'whatsapp:' + tonumber
        from_number = os.getenv('SENDER_WHATSAPP_NUMBER')
        message_body = 'EMERGENCY'
        
        message = client.messages.create(
            from_=from_number,
            body=message_body,
            to=to_number
        )
        print(f"WhatsApp alert sent (SID: {message.sid})")
        return True
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return False

@app.route('/emergency', methods=['POST'])
def send_whatsapp_alert_route():
    data = request.get_json()
    family_numbers = data.get('family_numbers', [])
    
    if not family_numbers:
        return jsonify({'error': 'No family member numbers provided'}), 400
        
    results = []
    for number in family_numbers:
        success = send_whatsapp_alert(number)
        results.append({
            'number': number,
            'success': success
        })
    
    if any(r['success'] for r in results):
        return jsonify({
            'message': 'WhatsApp alerts sent',
            'results': results
        }), 200
    else:
        return jsonify({
            'error': 'Failed to send alerts to any family members',
            'results': results
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
