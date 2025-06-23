"""
Voice processing service for GRC Agent Squad.
Handles speech-to-text and text-to-speech operations using AWS services.
"""

import asyncio
import logging
import io
import base64
from typing import Dict, Any, Optional, Union, BinaryIO
from botocore.exceptions import ClientError, BotoCoreError

from src.utils.config import settings
from src.services.aws_config import AWSConfig

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """Voice processing service using AWS Transcribe and Polly."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the voice processor."""
        self.config = config or settings
        
        # Initialize AWS clients using shared AWSConfig implementation
        self.polly_client = AWSConfig.create_aws_vault_client('polly')
        self.transcribe_client = None  # Will initialize when needed
        
        # Default settings
        self.default_voice_id = getattr(self.config, 'polly_voice_id', 'Joanna')
        self.default_engine = getattr(self.config, 'polly_engine', 'neural')
        self.default_language = getattr(self.config, 'transcribe_language_code', 'en-US')
        
        logger.info(f"VoiceProcessor initialized with voice: {self.default_voice_id}")



    async def text_to_speech(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        engine: Optional[str] = None,
        output_format: str = "mp3",
        sample_rate: str = "22050"
    ) -> Dict[str, Any]:
        """
        Convert text to speech using Amazon Polly Neural TTS.
        
        Args:
            text: Text to convert to speech
            voice_id: Polly voice ID (e.g., 'Joanna', 'Matthew', 'Amy')
            engine: Polly engine ('neural' or 'standard')
            output_format: Audio format ('mp3', 'ogg_vorbis', 'pcm')
            sample_rate: Sample rate for audio
            
        Returns:
            Dict containing audio data and metadata
        """
        try:
            # Use defaults if not specified
            voice_id = voice_id or self.default_voice_id
            engine = engine or self.default_engine
            
            # Validate text length (Polly has limits)
            if len(text) > 3000:
                logger.warning(f"Text length {len(text)} exceeds recommended limit")
                text = text[:3000] + "..."
            
            # Prepare synthesis request
            synthesis_params = {
                'Text': text,
                'OutputFormat': output_format,
                'VoiceId': voice_id,
                'Engine': engine,
                'SampleRate': sample_rate
            }
            
            # Add SSML support for neural voices
            if engine == 'neural' and not text.strip().startswith('<speak>'):
                # Wrap in SSML for better neural voice processing
                synthesis_params['Text'] = f'<speak>{text}</speak>'
                synthesis_params['TextType'] = 'ssml'
            
            logger.info(f"Synthesizing speech with voice: {voice_id}, engine: {engine}")
            
            # Call Polly API
            response = self.polly_client.synthesize_speech(**synthesis_params)
            
            # Extract audio stream
            if 'AudioStream' in response:
                audio_data = response['AudioStream'].read()
                
                # Encode to base64 for API transport
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                return {
                    'success': True,
                    'audio_data': audio_base64,
                    'audio_format': output_format,
                    'voice_id': voice_id,
                    'engine': engine,
                    'sample_rate': sample_rate,
                    'text_length': len(text),
                    'audio_size': len(audio_data),
                    'content_type': f'audio/{output_format}'
                }
            else:
                raise Exception("No audio stream in Polly response")
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Polly ClientError: {error_code} - {error_message}")
            
            return {
                'success': False,
                'error': f"AWS Polly Error: {error_message}",
                'error_code': error_code
            }
            
        except BotoCoreError as e:
            logger.error(f"Polly BotoCoreError: {e}")
            return {
                'success': False,
                'error': f"AWS Connection Error: {str(e)}"
            }
            
        except Exception as e:
            logger.error(f"Unexpected error in text_to_speech: {e}")
            return {
                'success': False,
                'error': f"Speech synthesis failed: {str(e)}"
            }

    def get_available_voices(self, language_code: Optional[str] = None) -> Dict[str, Any]:
        """
        Get available Polly voices.
        
        Args:
            language_code: Filter by language (e.g., 'en-US')
            
        Returns:
            Dict containing available voices
        """
        try:
            params = {}
            if language_code:
                params['LanguageCode'] = language_code
                
            response = self.polly_client.describe_voices(**params)
            
            voices = []
            for voice in response.get('Voices', []):
                voices.append({
                    'id': voice['Id'],
                    'name': voice['Name'],
                    'gender': voice['Gender'],
                    'language': voice['LanguageCode'],
                    'language_name': voice['LanguageName'],
                    'supported_engines': voice.get('SupportedEngines', [])
                })
            
            return {
                'success': True,
                'voices': voices,
                'count': len(voices)
            }
            
        except Exception as e:
            logger.error(f"Error getting available voices: {e}")
            return {
                'success': False,
                'error': str(e),
                'voices': []
            }

    def get_neural_voices(self) -> Dict[str, Any]:
        """Get voices that support Neural TTS engine."""
        try:
            all_voices = self.get_available_voices()
            if not all_voices['success']:
                return all_voices
                
            neural_voices = [
                voice for voice in all_voices['voices'] 
                if 'neural' in voice.get('supported_engines', [])
            ]
            
            return {
                'success': True,
                'voices': neural_voices,
                'count': len(neural_voices)
            }
            
        except Exception as e:
            logger.error(f"Error getting neural voices: {e}")
            return {
                'success': False,
                'error': str(e),
                'voices': []
            }

    async def get_agent_voice_config(self, agent_personality: str) -> Dict[str, str]:
        """
        Get appropriate voice configuration for different agent personalities.
        
        Args:
            agent_personality: The agent personality type
            
        Returns:
            Dict with voice_id and engine settings
        """
        # Voice mapping for different GRC agent personalities
        voice_configs = {
            'empathetic_interviewer': {
                'voice_id': 'Joanna',  # Warm, professional female voice
                'engine': 'neural'
            },
            'authoritative_compliance': {
                'voice_id': 'Matthew',  # Authoritative male voice
                'engine': 'neural'
            },
            'analytical_risk_expert': {
                'voice_id': 'Amy',  # Clear, analytical female voice
                'engine': 'neural'
            },
            'strategic_governance': {
                'voice_id': 'Brian',  # Strategic, executive male voice
                'engine': 'neural'
            },
            'default': {
                'voice_id': self.default_voice_id,
                'engine': self.default_engine
            }
        }
        
        return voice_configs.get(agent_personality, voice_configs['default'])

    async def synthesize_agent_response(
        self, 
        text: str, 
        agent_personality: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesize speech for a specific agent personality.
        
        Args:
            text: Clean text optimized for voice synthesis (no Markdown formatting)
            agent_personality: Agent personality type
            session_id: Optional session ID for logging
            
        Returns:
            Dict containing synthesized audio and metadata
        """
        try:
            # Get voice config for this agent
            voice_config = await self.get_agent_voice_config(agent_personality)
            
            logger.info(f"Synthesizing for agent '{agent_personality}' using voice '{voice_config['voice_id']}'")
            
            # Synthesize speech directly with provided text (already clean for voice)
            result = await self.text_to_speech(
                text=text,
                voice_id=voice_config['voice_id'],
                engine=voice_config['engine']
            )
            
            # Add agent context to result
            if result['success']:
                result['agent_personality'] = agent_personality
                result['session_id'] = session_id
                result['text_length'] = len(text)
                
            return result
            
        except Exception as e:
            logger.error(f"Error synthesizing agent response: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_personality': agent_personality
            }

    async def test_voice_synthesis(self) -> Dict[str, Any]:
        """Test voice synthesis functionality."""
        test_text = "Hello! I'm your GRC compliance assistant. How can I help you today?"
        
        try:
            result = await self.text_to_speech(test_text)
            
            if result['success']:
                logger.info("Voice synthesis test successful")
                return {
                    'success': True,
                    'message': "Voice synthesis is working correctly",
                    'test_text': test_text,
                    'audio_size': result.get('audio_size', 0),
                    'voice_id': result.get('voice_id'),
                    'engine': result.get('engine')
                }
            else:
                return {
                    'success': False,
                    'message': "Voice synthesis test failed",
                    'error': result.get('error')
                }
                
        except Exception as e:
            logger.error(f"Voice synthesis test error: {e}")
            return {
                'success': False,
                'message': "Voice synthesis test failed with exception",
                'error': str(e)
            } 