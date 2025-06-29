"""
Voice processing service for GRC Agent Squad.
Handles speech-to-text and text-to-speech operations using AWS services.
"""

import asyncio
import logging
import io
import base64
import re
from typing import Dict, Any, Optional, Union, BinaryIO
from botocore.exceptions import ClientError, BotoCoreError

from src.utils.settings import settings
from src.services.aws_config import AWSConfig

import structlog

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
        
        # Initialize logger
        self.logger = structlog.get_logger(__name__)
        self.logger.info(f"VoiceProcessor initialized with voice: {self.default_voice_id}")



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
                self.logger.warning(f"Text length {len(text)} exceeds recommended limit")
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
            
            self.logger.info(f"Synthesizing speech with voice: {voice_id}, engine: {engine}")
            
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
            self.logger.error(f"Polly ClientError: {error_code} - {error_message}")
            
            return {
                'success': False,
                'error': f"AWS Polly Error: {error_message}",
                'error_code': error_code
            }
            
        except BotoCoreError as e:
            self.logger.error(f"Polly BotoCoreError: {e}")
            return {
                'success': False,
                'error': f"AWS Connection Error: {str(e)}"
            }
            
        except Exception as e:
            self.logger.error(f"Unexpected error in text_to_speech: {e}")
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
            self.logger.error(f"Error getting available voices: {e}")
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
            self.logger.error(f"Error getting neural voices: {e}")
            return {
                'success': False,
                'error': str(e),
                'voices': []
            }

    async def get_agent_voice_config(self, agent_id: str) -> Dict[str, str]:
        """
        Get appropriate voice configuration for different agent personalities.
        
        Args:
            agent_id: The agent ID from the YAML configuration
            
        Returns:
            Dict with voice_id and engine settings
        """
        try:
            from ..agents.agent_config_loader import get_default_config_registry
            
            # Get agent configuration from registry
            config_registry = get_default_config_registry()
            agent_config = config_registry.get_config(agent_id)
            
            if agent_config:
                # Get voice settings directly from the agent's YAML configuration
                voice_settings = agent_config.get_voice_settings()
                if voice_settings and "voice_id" in voice_settings:
                    self.logger.info(f"Using voice settings from agent config: {voice_settings}")
                    return {
                        'voice_id': voice_settings.get('voice_id'),
                        'engine': voice_settings.get('engine', 'neural')
                    }
            
            # If no config found or no voice settings in config, use default
            self.logger.warning(f"No voice settings found for agent ID: {agent_id}, using defaults")
            return {
                'voice_id': self.default_voice_id,
                'engine': self.default_engine
            }
            
        except Exception as e:
            self.logger.error(f"Error getting agent voice config: {e}")
            # Return default voice settings
            return {
                'voice_id': self.default_voice_id,
                'engine': self.default_engine
            }

    async def synthesize_agent_response(self, text: str, agent_id: str) -> Dict[str, Any]:
        """
        Synthesize speech for an agent response.
        
        Args:
            text: The text to synthesize
            agent_id: The agent ID to get voice settings
            
        Returns:
            Dictionary with audio data and metadata
        """
        try:
            from ..agents.agent_config_loader import get_default_config_registry
            
            self.logger.info(f"Synthesizing voice for agent: {agent_id}")
            
            # Get agent configuration
            config_registry = get_default_config_registry()
            agent_config = config_registry.get_config(agent_id)
            
            if not agent_config:
                self.logger.error(f"Agent configuration not found for agent_id: {agent_id}")
                self.logger.info(f"Available agent IDs: {config_registry.list_agent_ids()}")
                return {
                    'success': False,
                    'error': f"Agent configuration not found for agent_id: {agent_id}",
                    'agent_id': agent_id
                }
            
            # Get voice settings from agent configuration
            voice_settings = agent_config.get_voice_settings()
            self.logger.info(f"Voice settings for agent {agent_id}: {voice_settings}")
            
            if not voice_settings or not voice_settings.get('voice_id'):
                self.logger.error(f"Voice settings not found or missing voice_id for agent: {agent_id}")
                return {
                    'success': False,
                    'error': f"Voice settings not found or missing voice_id for agent: {agent_id}",
                    'agent_id': agent_id
                }
            
            voice_id = voice_settings.get('voice_id')
            self.logger.info(f"Using voice_id: {voice_id} for agent: {agent_id}")
            
            # Clean and prepare text for TTS
            cleaned_text = self._clean_text_for_tts(text)
            
            # Generate audio
            self.logger.info(f"Generating audio with voice_id: {voice_id}")
            tts_result = await self.text_to_speech(cleaned_text, voice_id=voice_id)
            
            if not tts_result.get('success'):
                self.logger.error(f"Failed to generate audio data: {tts_result.get('error', 'Unknown error')}")
                return {
                    'success': False,
                    'error': tts_result.get('error', "Failed to generate audio data"),
                    'agent_id': agent_id,
                    'voice_id': voice_id
                }
            
            # Extract the audio data from the TTS result
            audio_data = tts_result.get('audio_data')
            audio_size = tts_result.get('audio_size', 0)
            
            self.logger.info(f"Successfully generated audio for agent {agent_id}, size: {audio_size} bytes")
            
            # Return audio data and metadata
            return {
                'success': True,
                'audio_data': audio_data,
                'audio_format': 'mp3',
                'voice_id': voice_id,
                'agent_id': agent_id,
                'audio_size': audio_size
            }
            
        except Exception as e:
            self.logger.error(f"Error synthesizing agent response: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'agent_id': agent_id
            }

    async def test_voice_synthesis(self) -> Dict[str, Any]:
        """Test voice synthesis functionality."""
        test_text = "Hello! I'm your GRC compliance assistant. How can I help you today?"
        
        try:
            result = await self.text_to_speech(test_text)
            
            if result['success']:
                self.logger.info("Voice synthesis test successful")
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
            self.logger.error(f"Voice synthesis test error: {e}")
            return {
                'success': False,
                'message': "Voice synthesis test failed with exception",
                'error': str(e)
            }

    def _clean_text_for_tts(self, text: str) -> str:
        """
        Clean and prepare text for TTS.
        
        Args:
            text: Raw text that may contain markdown or other formatting
            
        Returns:
            Cleaned text suitable for TTS
        """
        try:
            # Remove markdown formatting
            cleaned = text
            
            # Remove markdown headers
            cleaned = re.sub(r'#+\s+', '', cleaned)
            
            # Remove markdown bold/italic
            cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)
            cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)
            
            # Remove markdown links
            cleaned = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', cleaned)
            
            # Remove code blocks
            cleaned = re.sub(r'```.*?```', '', cleaned, flags=re.DOTALL)
            cleaned = re.sub(r'`(.*?)`', r'\1', cleaned)
            
            # Remove bullet points and numbered lists
            cleaned = re.sub(r'^\s*[-*+]\s+', '', cleaned, flags=re.MULTILINE)
            cleaned = re.sub(r'^\s*\d+\.\s+', '', cleaned, flags=re.MULTILINE)
            
            # Remove horizontal rules
            cleaned = re.sub(r'---+', '', cleaned)
            
            # Remove excessive whitespace
            cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
            cleaned = cleaned.strip()
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error cleaning text for TTS: {e}")
            # Return original text if cleaning fails
            return text 