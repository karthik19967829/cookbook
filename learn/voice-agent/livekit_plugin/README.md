# Fireworks AI LiveKit Voice Agent Plugin

This plugin integrates the Fireworks AI Voice Agent with LiveKit's real-time communication infrastructure, enabling voice conversations in LiveKit rooms with advanced AI capabilities.

## 🌟 Features

- **Real-time Voice Conversations** - Bi-directional audio streaming between LiveKit and Fireworks AI
- **Function Calling** - Business automation with dental office receptionist functions
- **Multi-participant Support** - Handle multiple users in LiveKit rooms
- **Professional AI Persona** - Configured as a dental office receptionist
- **WebSocket Integration** - Direct connection to Fireworks AI voice agent API

## 🚀 Quick Start

### Step 1: Prerequisites

**LiveKit Server**
- Set up a LiveKit server (cloud or self-hosted)
- Get your API key and secret from LiveKit dashboard

**Fireworks AI**
- Get your API key from [fireworks.ai](https://fireworks.ai)

### Step 2: Installation

```bash
# Navigate to the plugin directory
cd learn/voice-agent/livekit_plugin

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configuration

```bash
# Copy environment template
cp env_template.txt .env

# Edit .env with your actual API keys:
# FIREWORKS_API_KEY=fw_your_actual_api_key
# LIVEKIT_API_KEY=your_livekit_api_key
# LIVEKIT_API_SECRET=your_livekit_api_secret  
# LIVEKIT_URL=wss://your-livekit-server.com
```

### Step 4: Run the Agent

```bash
# Start the LiveKit voice agent
python fireworks_voice_agent.py start

# For development/testing in console mode:
python fireworks_voice_agent.py console
```

## 🎯 How It Works

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   LiveKit       │    │   Plugin         │    │  Fireworks AI   │
│   Participants  │◄──►│   (This Code)    │◄──►│  Voice Agent    │
│                 │    │                  │    │                 │
│  • User Audio   │    │ • Audio Bridge   │    │ • STT/TTS       │
│  • Microphone   │    │ • Message Router │    │ • LLM           │
│  • Speakers     │    │ • Function Calls │    │ • Functions     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Data Flow

1. **Audio Input**: User speaks in LiveKit room
2. **Audio Forwarding**: Plugin captures audio and sends to Fireworks AI
3. **AI Processing**: Fireworks AI processes speech, generates response
4. **Function Execution**: Plugin executes business functions locally
5. **Audio Output**: AI response is streamed back to LiveKit room

## 🔧 Configuration Options

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FIREWORKS_API_KEY` | ✅ | Your Fireworks AI API key |
| `LIVEKIT_API_KEY` | ✅ | LiveKit API key |
| `LIVEKIT_API_SECRET` | ✅ | LiveKit API secret |
| `LIVEKIT_URL` | ✅ | LiveKit server WebSocket URL |
| `LOG_LEVEL` | ❌ | Logging level (default: INFO) |

### Agent Configuration

The agent is pre-configured as a dental office receptionist with these functions:

- **`enroll_new_patients`** - Register new patients
- **`schedule_appointment`** - Book appointments  
- **`cancel_appointment`** - Cancel existing appointments
- **`check_availability`** - Check available time slots

## 🎮 Usage Examples

### Basic Room Connection

```python
from livekit import rtc, api

# Connect to LiveKit room
url = "wss://your-livekit-server.com"
token = "your_room_token"

room = rtc.Room()
await room.connect(url, token)

# The agent will automatically join and start responding to voice
```

### Testing Voice Interactions

Once the agent is running in a LiveKit room, try these voice commands:

- *"Hi, I'm a new patient and would like to register"*
- *"I'd like to schedule an appointment for next Tuesday at 2 PM"*
- *"Can you check what times are available on Friday?"*
- *"I need to cancel my appointment"*

## 🛠️ Development

### Project Structure

```
livekit_plugin/
├── fireworks_voice_agent.py  # Main plugin code
├── requirements.txt          # Python dependencies
├── env_template.txt         # Environment variable template
└── README.md               # This file
```

### Key Classes

- **`FireworksVoiceAgent`** - Core agent with business functions
- **`FireworksAgentSession`** - LiveKit session management
- **Audio Processing** - Handles bidirectional audio streaming

### Extending Functionality

To add new business functions:

1. Add the function to `FireworksVoiceAgent` class
2. Include it in the `functions` dictionary
3. Add the function schema to the Fireworks AI configuration
4. Test with voice commands

Example:
```python
async def new_business_function(self, param1: str, param2: int) -> Dict[str, Any]:
    # Your business logic here
    return {"result": "success"}
```

## 🚨 Troubleshooting

### Common Issues

**1. Connection Failed to Fireworks AI**
```bash
# Check your API key
echo $FIREWORKS_API_KEY

# Verify network connectivity
curl -H "Authorization: Bearer $FIREWORKS_API_KEY" \
  https://api.fireworks.ai/inference/v1/models
```

**2. LiveKit Connection Issues**
```bash
# Test LiveKit connection
lk room list --url $LIVEKIT_URL --api-key $LIVEKIT_API_KEY --api-secret $LIVEKIT_API_SECRET
```

**3. Audio Not Working**
- Check microphone permissions
- Verify audio device settings
- Use headphones to prevent feedback
- Check LiveKit room audio settings

**4. Functions Not Executing**
- Check logs for function call errors
- Verify function signatures match configuration
- Test function calls in isolation

### Debug Mode

Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
python fireworks_voice_agent.py start
```

## 📚 API Reference

### Fireworks AI Integration

The plugin uses Fireworks AI's voice agent WebSocket API:
- **Endpoint**: `wss://audio-agent.link.fireworks.ai/v1/audio/agent`
- **Audio Format**: PCM16, 16kHz, mono
- **Protocol**: WebSocket with JSON control messages

### LiveKit Integration

Built on LiveKit's Agent SDK:
- **Audio Source**: 16kHz mono audio track
- **Track Publishing**: Microphone source type
- **Room Events**: Automatic track subscription handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with both LiveKit and Fireworks AI
5. Submit a pull request

## 📄 License

This plugin follows the same license as the main cookbook repository.

## 🔗 Related Resources

- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [Fireworks AI API Docs](https://docs.fireworks.ai/)
- [LiveKit Python SDK](https://github.com/livekit/python-sdks)
- [Original Voice Agent Example](../README.md)

---

*For more advanced configurations and production deployment, refer to the LiveKit and Fireworks AI documentation.*
