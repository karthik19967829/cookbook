"""
LiveKit Plugin for Fireworks AI Voice Agent

This plugin integrates the Fireworks AI Voice Agent with LiveKit's real-time
communication infrastructure, enabling voice interactions in LiveKit rooms.
"""

import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any
import numpy as np
import websockets
from datetime import datetime

from livekit import rtc
from livekit.agents import (
    Agent,
    AgentSession,
    RoomInputOptions,
    entrypoint,
    WorkerOptions,
    WorkerType,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Audio configuration
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
TTS_SAMPLE_RATE = 44100

# Fireworks AI configuration
FIREWORKS_ENDPOINT = "wss://audio-agent.link.fireworks.ai/v1/audio/agent"


class FireworksVoiceAgent(Agent):
    """
    A LiveKit agent that uses Fireworks AI for voice processing.
    
    This agent connects to Fireworks AI voice agent WebSocket and handles
    real-time voice conversations within LiveKit rooms.
    """
    
    def __init__(self):
        super().__init__()
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.audio_queue = asyncio.Queue()
        self.is_speaking = False
        self.session_active = False
        
        # Business functions for the dental office receptionist
        self.functions = {
            "enroll_new_patients": self.enroll_new_patients,
            "schedule_appointment": self.schedule_appointment,
            "cancel_appointment": self.cancel_appointment,
            "check_availability": self.check_availability,
        }
        
        # Agent prompt
        self.prompt = f"""
        You are a professional dental office receptionist at Sonrisas Dental Center. You can help patients with:

        1. ENROLL NEW PATIENTS - Collect name and phone number
        2. SCHEDULE APPOINTMENTS - Book appointments for existing patients, ask for preferred date and time
        3. CANCEL APPOINTMENTS - Cancel appointments for existing patients
        4. CHECK AVAILABILITY - Show available appointment slots

        Use the available functions to help patients. Be friendly and professional. Keep responses brief and conversational.

        The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M")}.
        """

    async def enroll_new_patients(self, name: str, phone_number: str) -> Dict[str, Any]:
        """Mock patient enrollment function"""
        logger.info(f"Enrolling new patient: {name}, {phone_number}")
        return {"message": f"{name} has been enrolled as a new patient."}

    async def schedule_appointment(self, name: str, date: str, time: str, service: str = "General Checkup") -> Dict[str, Any]:
        """Mock appointment scheduling function"""
        try:
            appointment_date = datetime.strptime(date, "%Y-%m-%d").date()
            appointment_id = f"APT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            logger.info(f"Scheduling appointment for {name} on {date} at {time}")
            return {
                "appointment_id": appointment_id,
                "name": name,
                "date": appointment_date.strftime("%Y-%m-%d"),
                "time": time,
                "service": service,
                "message": f"Appointment scheduled for {name} on {appointment_date.strftime('%B %d, %Y')} at {time} for {service}."
            }
        except ValueError:
            return {"error": "Invalid date format. Please use YYYY-MM-DD format."}

    async def cancel_appointment(self, name: str, appointment_id: str) -> Dict[str, Any]:
        """Mock appointment cancellation function"""
        logger.info(f"Cancelling appointment {appointment_id} for {name}")
        return {
            "appointment_id": appointment_id,
            "name": name,
            "status": "cancelled",
            "message": f"Appointment {appointment_id} for {name} has been cancelled."
        }

    async def check_availability(self, date: str) -> Dict[str, Any]:
        """Mock availability checking function"""
        try:
            check_date = datetime.strptime(date, "%Y-%m-%d").date()
            
            # Mock available times
            available_times = [
                "9:00 AM", "10:30 AM", "2:00 PM", "3:30 PM", "4:45 PM"
            ]
            
            logger.info(f"Checking availability for {date}")
            return {
                "date": check_date.strftime("%Y-%m-%d"),
                "available_times": available_times,
                "message": f"Available times on {check_date.strftime('%B %d, %Y')}: {', '.join(available_times)}"
            }
        except ValueError:
            return {"error": "Invalid date format. Please use YYYY-MM-DD format."}

    async def connect_to_fireworks(self) -> bool:
        """Connect to Fireworks AI voice agent WebSocket"""
        try:
            api_key = os.getenv("FIREWORKS_API_KEY")
            if not api_key:
                logger.error("FIREWORKS_API_KEY environment variable not set")
                return False

            headers = {"Authorization": f"Bearer {api_key}"}
            
            self.websocket = await websockets.connect(
                FIREWORKS_ENDPOINT,
                extra_headers=headers
            )
            
            # Send initial configuration
            config = {
                "type": "session.update",
                "session": {
                    "modalities": ["text", "audio"],
                    "instructions": self.prompt,
                    "voice": "alloy",
                    "input_audio_format": "pcm16",
                    "output_audio_format": "pcm16",
                    "input_audio_transcription": {"model": "whisper-1"},
                    "turn_detection": {
                        "type": "server_vad",
                        "threshold": 0.5,
                        "prefix_padding_ms": 300,
                        "silence_duration_ms": 500
                    },
                    "tools": [
                        {
                            "type": "function",
                            "name": "enroll_new_patients",
                            "description": "Enroll a new patient with name and phone number",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "description": "Patient's full name"},
                                    "phone_number": {"type": "string", "description": "Patient's phone number"}
                                },
                                "required": ["name", "phone_number"]
                            }
                        },
                        {
                            "type": "function",
                            "name": "schedule_appointment",
                            "description": "Schedule an appointment for a patient",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "description": "Patient's name"},
                                    "date": {"type": "string", "description": "Appointment date (YYYY-MM-DD)"},
                                    "time": {"type": "string", "description": "Appointment time"},
                                    "service": {"type": "string", "description": "Type of service", "default": "General Checkup"}
                                },
                                "required": ["name", "date", "time"]
                            }
                        },
                        {
                            "type": "function",
                            "name": "cancel_appointment",
                            "description": "Cancel an existing appointment",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string", "description": "Patient's name"},
                                    "appointment_id": {"type": "string", "description": "Appointment ID to cancel"}
                                },
                                "required": ["name", "appointment_id"]
                            }
                        },
                        {
                            "type": "function",
                            "name": "check_availability",
                            "description": "Check available appointment slots for a specific date",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "date": {"type": "string", "description": "Date to check (YYYY-MM-DD)"}
                                },
                                "required": ["date"]
                            }
                        }
                    ]
                }
            }
            
            await self.websocket.send(json.dumps(config))
            logger.info("🔗 Connected to Fireworks AI voice agent")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Fireworks AI: {e}")
            return False

    async def handle_fireworks_messages(self):
        """Handle incoming messages from Fireworks AI WebSocket"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self.process_fireworks_message(data)
                except json.JSONDecodeError:
                    # Handle binary audio data
                    await self.handle_audio_output(message)
                except Exception as e:
                    logger.error(f"Error processing Fireworks message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Fireworks WebSocket connection closed")
        except Exception as e:
            logger.error(f"Error in Fireworks message handler: {e}")

    async def process_fireworks_message(self, data: Dict[str, Any]):
        """Process structured messages from Fireworks AI"""
        message_type = data.get("type")
        
        if message_type == "session.created":
            logger.info("✅ Fireworks session created")
            self.session_active = True
            
        elif message_type == "response.audio.delta":
            # Handle streaming audio response
            if "delta" in data:
                audio_data = data["delta"]
                await self.handle_audio_output(audio_data)
                
        elif message_type == "response.function_call_arguments.done":
            # Handle function call
            function_name = data.get("name")
            arguments = json.loads(data.get("arguments", "{}"))
            
            if function_name in self.functions:
                result = await self.functions[function_name](**arguments)
                
                # Send function result back to Fireworks
                response = {
                    "type": "conversation.item.create",
                    "item": {
                        "type": "function_call_output",
                        "call_id": data.get("call_id"),
                        "output": json.dumps(result)
                    }
                }
                await self.websocket.send(json.dumps(response))
                
        elif message_type == "input_audio_buffer.speech_started":
            logger.info("👤 User started speaking")
            self.is_speaking = False
            
        elif message_type == "input_audio_buffer.speech_stopped":
            logger.info("👤 User stopped speaking")
            
        elif message_type == "response.audio.done":
            logger.info("🤖 Assistant finished speaking")
            self.is_speaking = False

    async def handle_audio_output(self, audio_data: bytes):
        """Handle audio output from Fireworks AI"""
        try:
            # Convert audio data to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Add to queue for LiveKit audio track
            await self.audio_queue.put(audio_array)
            
        except Exception as e:
            logger.error(f"Error handling audio output: {e}")

    async def send_audio_to_fireworks(self, audio_data: np.ndarray):
        """Send audio data to Fireworks AI"""
        try:
            if self.websocket and self.session_active:
                # Convert numpy array to bytes
                audio_bytes = audio_data.astype(np.int16).tobytes()
                
                # Send as binary WebSocket message
                await self.websocket.send(audio_bytes)
                
        except Exception as e:
            logger.error(f"Error sending audio to Fireworks: {e}")

    async def cleanup(self):
        """Clean up resources"""
        if self.websocket:
            await self.websocket.close()
        logger.info("🧹 Cleaned up Fireworks voice agent")


class FireworksAgentSession(AgentSession):
    """
    Custom agent session that integrates Fireworks AI with LiveKit
    """
    
    def __init__(self, room: rtc.Room):
        super().__init__()
        self.room = room
        self.agent = FireworksVoiceAgent()
        self.audio_source = rtc.AudioSource(SAMPLE_RATE, 1)
        self.audio_track = None
        self.is_connected = False

    async def start(self):
        """Start the agent session"""
        try:
            # Connect to Fireworks AI
            if not await self.agent.connect_to_fireworks():
                logger.error("Failed to connect to Fireworks AI")
                return
            
            # Create audio track for output
            self.audio_track = rtc.LocalAudioTrack.create_audio_track(
                "fireworks-agent-audio", self.audio_source
            )
            
            # Publish the audio track
            options = rtc.TrackPublishOptions()
            options.source = rtc.TrackSource.SOURCE_MICROPHONE
            
            publication = await self.room.local_participant.publish_track(
                self.audio_track, options
            )
            
            logger.info(f"📢 Published audio track: {publication.sid}")
            
            # Start message handling
            asyncio.create_task(self.agent.handle_fireworks_messages())
            
            # Start audio processing
            asyncio.create_task(self.process_audio_output())
            
            # Handle room events
            self.room.on("track_subscribed", self.on_track_subscribed)
            
            self.is_connected = True
            logger.info("🎙️ Fireworks LiveKit agent started successfully")
            
        except Exception as e:
            logger.error(f"Error starting agent session: {e}")
            await self.cleanup()

    async def process_audio_output(self):
        """Process audio output from Fireworks and send to LiveKit"""
        try:
            while self.is_connected:
                try:
                    # Get audio data from queue (with timeout)
                    audio_data = await asyncio.wait_for(
                        self.agent.audio_queue.get(), timeout=0.1
                    )
                    
                    # Convert to LiveKit audio frame
                    frame = rtc.AudioFrame(
                        data=audio_data.tobytes(),
                        sample_rate=SAMPLE_RATE,
                        num_channels=1,
                        samples_per_channel=len(audio_data)
                    )
                    
                    # Send to audio source
                    await self.audio_source.capture_frame(frame)
                    
                except asyncio.TimeoutError:
                    # No audio data available, continue
                    continue
                except Exception as e:
                    logger.error(f"Error processing audio output: {e}")
                    
        except Exception as e:
            logger.error(f"Error in audio output processing: {e}")

    def on_track_subscribed(
        self,
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        """Handle incoming audio tracks from other participants"""
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            logger.info(f"🎤 Subscribed to audio track from {participant.identity}")
            
            # Create task to handle incoming audio
            asyncio.create_task(self.handle_incoming_audio(track))

    async def handle_incoming_audio(self, track: rtc.AudioTrack):
        """Handle incoming audio from LiveKit participants"""
        try:
            async for event in rtc.AudioStream(track):
                if isinstance(event, rtc.AudioFrameEvent):
                    # Convert audio frame to numpy array
                    audio_data = np.frombuffer(event.frame.data, dtype=np.int16)
                    
                    # Send to Fireworks AI
                    await self.agent.send_audio_to_fireworks(audio_data)
                    
        except Exception as e:
            logger.error(f"Error handling incoming audio: {e}")

    async def cleanup(self):
        """Clean up the session"""
        self.is_connected = False
        await self.agent.cleanup()
        logger.info("🧹 Cleaned up agent session")


@entrypoint
async def main(ctx):
    """
    Main entry point for the LiveKit Fireworks Voice Agent
    """
    logger.info("🚀 Starting Fireworks LiveKit Voice Agent")
    
    try:
        # Create and start the agent session
        session = FireworksAgentSession(ctx.room)
        await session.start()
        
        # Keep the session running
        try:
            while session.is_connected:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal")
        finally:
            await session.cleanup()
            
    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    # Run the agent
    from livekit.agents import run_app
    
    # Configure worker options
    worker_options = WorkerOptions(
        entrypoint_fnc=main,
        prewarm_fnc=None,
        worker_type=WorkerType.ROOM,
    )
    
    run_app(worker_options)
