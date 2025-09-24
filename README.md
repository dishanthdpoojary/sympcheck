# 🏥 Healthcare AI Consultation App

A comprehensive healthcare consultation application with AI-powered medical assistance for text and voice interactions.

## ✨ Features

### 💬 Text Doctor (Simple Chat)
- Text-based medical consultation
- AI-powered symptom analysis using Groq Llama
- Rural-friendly, simple language responses
- Conversation history management
- Rate limiting protection

### 🎤 Voice Doctor (Audio-Only)
- Voice-based medical consultation
- Azure Speech-to-Text transcription
- AI-generated medical responses
- ElevenLabs text-to-speech conversion
- Audio playback in mobile app

### 🚨 Emergency SOS
- Emergency contact management
- WhatsApp emergency alerts via Twilio
- Location-based emergency assistance
- Quick access to emergency services

## 🚀 Quick Start

### Backend Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables (copy from `env.example`):
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

3. Start the Flask server:
   ```bash
   python app.py
   ```

### Frontend Setup
1. Navigate to the React Native app:
   ```bash
   cd healthcare-app
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

## 🔧 Technical Stack

### Backend (Python/Flask)
- **Flask** - Web framework
- **Groq Llama** - AI medical responses
- **Azure Speech-to-Text** - Audio transcription
- **ElevenLabs** - Text-to-speech conversion
- **Twilio** - WhatsApp emergency alerts
- **Flask-CORS** - Cross-origin resource sharing
- **Flask-Limiter** - Rate limiting

### Frontend (React Native/Expo)
- **React Native** - Mobile app framework
- **Expo** - Development platform
- **expo-av** - Audio recording and playback
- **expo-image-picker** - Photo capture/selection
- **axios** - HTTP client

## 📱 Usage

### Text Doctor
1. Open the "Simple Chat" screen
2. Type your symptoms
3. Receive AI medical advice in simple, rural-friendly language

### Voice Doctor
1. Open the "Audio Only" screen
2. Record your symptoms
3. Hear AI medical advice

### Emergency SOS
1. Open the "Emergency" screen
2. Add emergency contacts
3. Press Emergency SOS button to send WhatsApp alerts

## 🛡️ Error Handling

- **API Failures**: Graceful fallbacks for all services
- **Network Issues**: Multiple URL fallback system
- **Audio Issues**: Format conversion and multiple playback strategies
- **Rate Limiting**: 10 requests per minute per IP

## 📋 API Endpoints

- `GET /health` - Health check
- `POST /chat` - Text-based consultation
- `POST /api/audio-conversation` - Voice-based consultation
- `POST /emergency` - Emergency WhatsApp alerts
- `POST /api/speech-to-text` - Speech-to-text conversion
- `POST /api/text-to-speech` - Text-to-speech conversion

## 🔑 Required API Keys

- **Groq API Key** - For AI medical responses
- **Azure Speech API Key** - For speech-to-text
- **ElevenLabs API Key** - For text-to-speech
- **Twilio Credentials** - For WhatsApp emergency alerts

## 📁 Project Structure

```
├── app.py                              # Flask backend server
├── audio_conversation_service.py       # Voice consultation service
├── groq_integration.py                 # Groq AI integration
├── azure_speech_service.py             # Azure Speech-to-Text
├── elevenlabs_service.py               # ElevenLabs TTS
├── audio_converter.py                  # Audio format conversion
├── conversation_manager.py             # Conversation history
├── medical_logic.py                    # Medical logic processing
├── requirements.txt                    # Python dependencies
├── env.example                         # Environment variables template
└── healthcare-app/                     # React Native frontend
    ├── app/                            # App screens
    ├── config/                         # Configuration
    ├── package.json                    # Node dependencies
    └── README.md                       # Frontend documentation
```

## 🎯 Status

✅ **All systems operational:**
- Text Doctor: Working
- Voice Doctor: Working  
- Emergency SOS: Working

## 📞 Support

For issues or questions, check the error logs in the Flask server console or React Native development tools.