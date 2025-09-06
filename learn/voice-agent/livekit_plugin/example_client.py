"""
Example LiveKit Client for Testing the Fireworks Voice Agent

This script demonstrates how to connect to a LiveKit room and interact
with the Fireworks voice agent.
"""

import asyncio
import logging
import os
from livekit import rtc, api
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoiceAgentClient:
    """Example client for testing the Fireworks LiveKit voice agent"""
    
    def __init__(self):
        self.room = rtc.Room()
        self.audio_source = None
        self.audio_track = None
        self.is_connected = False
        
        # Setup room event handlers
        self.room.on("connected", self.on_connected)
        self.room.on("disconnected", self.on_disconnected)
        self.room.on("track_published", self.on_track_published)
        self.room.on("track_subscribed", self.on_track_subscribed)
        self.room.on("participant_connected", self.on_participant_connected)

    async def connect_to_room(self, room_name: str = "voice-agent-test"):
        """Connect to a LiveKit room"""
        try:
            # Get LiveKit configuration
            url = os.getenv("LIVEKIT_URL")
            api_key = os.getenv("LIVEKIT_API_KEY")
            api_secret = os.getenv("LIVEKIT_API_SECRET")
            
            if not all([url, api_key, api_secret]):
                raise ValueError("Missing LiveKit configuration. Check your .env file.")
            
            # Create room token
            token = (
                api.AccessToken(api_key, api_secret)
                .with_identity("test-user")
                .with_name("Test User")
                .with_grants(
                    api.VideoGrants(
                        room_join=True,
                        room=room_name,
                        can_publish=True,
                        can_subscribe=True,
                    )
                )
                .to_jwt()
            )
            
            logger.info(f"🔗 Connecting to room: {room_name}")
            await self.room.connect(url, token)
            
        except Exception as e:
            logger.error(f"Failed to connect to room: {e}")
            raise

    async def setup_audio(self):
        """Setup audio input/output"""
        try:
            # Create audio source for microphone input
            self.audio_source = rtc.AudioSource(16000, 1)  # 16kHz mono
            
            # Create local audio track
            self.audio_track = rtc.LocalAudioTrack.create_audio_track(
                "microphone", self.audio_source
            )
            
            # Publish the audio track
            options = rtc.TrackPublishOptions()
            options.source = rtc.TrackSource.SOURCE_MICROPHONE
            
            publication = await self.room.local_participant.publish_track(
                self.audio_track, options
            )
            
            logger.info(f"🎤 Published audio track: {publication.sid}")
            
            # Start capturing audio from microphone
            await self.start_microphone_capture()
            
        except Exception as e:
            logger.error(f"Failed to setup audio: {e}")
            raise

    async def start_microphone_capture(self):
        """Start capturing audio from microphone"""
        try:
            import sounddevice as sd
            import numpy as np
            
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio callback status: {status}")
                    return
                
                # Convert to int16 and create audio frame
                audio_data = (indata[:, 0] * 32767).astype(np.int16)
                frame = rtc.AudioFrame(
                    data=audio_data.tobytes(),
                    sample_rate=16000,
                    num_channels=1,
                    samples_per_channel=len(audio_data)
                )
                
                # Send to audio source (non-blocking)
                asyncio.create_task(self.audio_source.capture_frame(frame))
            
            # Start audio stream
            stream = sd.InputStream(
                channels=1,
                samplerate=16000,
                callback=audio_callback,
                dtype=np.float32
            )
            
            stream.start()
            logger.info("🎙️ Started microphone capture")
            
            # Keep the stream alive
            while self.is_connected:
                await asyncio.sleep(0.1)
                
        except ImportError:
            logger.error("sounddevice is required for microphone capture")
            logger.info("Install with: pip install sounddevice")
        except Exception as e:
            logger.error(f"Error in microphone capture: {e}")

    def on_connected(self):
        """Called when connected to room"""
        logger.info("✅ Connected to LiveKit room")
        self.is_connected = True

    def on_disconnected(self, reason):
        """Called when disconnected from room"""
        logger.info(f"❌ Disconnected from room: {reason}")
        self.is_connected = False

    def on_track_published(self, publication, participant):
        """Called when a track is published"""
        logger.info(f"📢 Track published: {publication.sid} by {participant.identity}")

    def on_track_subscribed(self, track, publication, participant):
        """Called when subscribing to a track"""
        logger.info(f"🔔 Subscribed to {track.kind} track from {participant.identity}")
        
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            # Handle incoming audio from the voice agent
            asyncio.create_task(self.handle_agent_audio(track))

    def on_participant_connected(self, participant):
        """Called when a participant joins"""
        logger.info(f"👤 Participant joined: {participant.identity}")
        
        if "agent" in participant.identity.lower():
            logger.info("🤖 Voice agent joined the room!")

    async def handle_agent_audio(self, track):
        """Handle audio from the voice agent"""
        try:
            import sounddevice as sd
            import numpy as np
            
            logger.info("🔊 Playing agent audio...")
            
            async for event in rtc.AudioStream(track):
                if isinstance(event, rtc.AudioFrameEvent):
                    # Convert frame to numpy array and play
                    audio_data = np.frombuffer(event.frame.data, dtype=np.int16)
                    audio_float = audio_data.astype(np.float32) / 32767.0
                    
                    # Play audio
                    sd.play(audio_float, samplerate=16000)
                    
        except ImportError:
            logger.error("sounddevice is required for audio playback")
        except Exception as e:
            logger.error(f"Error handling agent audio: {e}")

    async def run(self, room_name: str = "voice-agent-test"):
        """Run the client"""
        try:
            await self.connect_to_room(room_name)
            await self.setup_audio()
            
            logger.info("🎯 Client is ready! Start speaking to interact with the voice agent.")
            logger.info("💡 Try saying: 'Hi, I'm a new patient' or 'I'd like to schedule an appointment'")
            logger.info("🛑 Press Ctrl+C to disconnect")
            
            # Keep running until interrupted
            while self.is_connected:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")
        except Exception as e:
            logger.error(f"Error running client: {e}")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Clean up resources"""
        if self.room:
            await self.room.disconnect()
        logger.info("🧹 Cleaned up client resources")


async def main():
    """Main entry point"""
    print("🎙️ LiveKit Fireworks Voice Agent Client")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file and ensure all LiveKit variables are set.")
        return
    
    # Get room name from user input
    room_name = input("Enter room name (default: voice-agent-test): ").strip()
    if not room_name:
        room_name = "voice-agent-test"
    
    # Create and run client
    client = VoiceAgentClient()
    await client.run(room_name)


if __name__ == "__main__":
    asyncio.run(main())
