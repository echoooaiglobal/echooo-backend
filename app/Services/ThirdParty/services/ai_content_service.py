# app/Services/ThirdParty/services/ai_content_service.py

import json
import logging
from typing import List, Dict, Any, Optional, Union
from enum import Enum

from ..providers.openai.client import OpenAIClient
from ..providers.openai.config import OpenAIConfig
from ..providers.openai.models import ChatCompletionRequest, ChatMessage

from ..providers.gemini.client import GeminiClient  
from ..providers.gemini.config import GeminiConfig
from ..providers.gemini.models import GenerateContentRequest, Content, ContentPart, GenerationConfig

from ..exceptions import ThirdPartyAPIError, APIParsingError
from ..factory import AIProviderFactory

logger = logging.getLogger(__name__)

class AIProvider(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"  # Future

class FollowupTemplate(dict):
    """Structured followup template data"""
    def __init__(self, content: str, delay_hours: int, subject: str = None):
        super().__init__({
            "content": content,
            "delay_hours": delay_hours,
            "subject": subject
        })

class AIContentService:
    """High-level service for AI-powered content generation"""
    
    def __init__(self):
        self.factory = AIProviderFactory()
    
    async def generate_followup_messages(
        self,
        original_subject: str,
        original_message: str,
        provider: Union[AIProvider, str] = AIProvider.OPENAI,
        count: int = 5,
        custom_instructions: Optional[str] = None
    ) -> List[FollowupTemplate]:
        """
        Generate followup messages for email campaigns
        
        Args:
            original_subject: Original email subject
            original_message: Original email content
            provider: AI provider to use
            count: Number of followups to generate (default: 5)
            custom_instructions: Additional instructions for AI
            
        Returns:
            List of followup templates
        """
        
        if isinstance(provider, str):
            provider = AIProvider(provider)
        
        try:
            logger.info(f"Generating {count} followup messages using {provider.value}")
            
            # Generate followups based on provider
            if provider == AIProvider.OPENAI:
                followups = await self._generate_with_openai(
                    original_subject, original_message, count, custom_instructions
                )
            elif provider == AIProvider.GEMINI:
                followups = await self._generate_with_gemini(
                    original_subject, original_message, count, custom_instructions
                )
            else:
                raise ValueError(f"Unsupported AI provider: {provider}")
            
            logger.info(f"Successfully generated {len(followups)} followup messages")
            return followups
            
        except Exception as e:
            logger.error(f"Failed to generate followup messages: {str(e)}")
            raise
    
    async def _generate_with_openai(
        self, 
        subject: str, 
        message: str, 
        count: int,
        custom_instructions: Optional[str]
    ) -> List[FollowupTemplate]:
        """Generate followups using OpenAI"""
        
        config = OpenAIConfig.from_env()
        
        async with OpenAIClient(config) as client:
            prompt = self._build_followup_prompt(subject, message, count, custom_instructions)
            
            request = ChatCompletionRequest(
                model=config.default_model,
                messages=[
                    ChatMessage(
                        role="system", 
                        content="You are an expert copywriter specializing in influencer outreach campaigns. Always return valid JSON."
                    ),
                    ChatMessage(role="user", content=prompt)
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            response = await client.create_chat_completion(request)
            
            # Parse JSON response
            content = response.choices[0].message.content.strip()
            return self._parse_followup_response(content)
    
    async def _generate_with_gemini(
        self, 
        subject: str, 
        message: str, 
        count: int,
        custom_instructions: Optional[str]
    ) -> List[FollowupTemplate]:
        """Generate followups using Gemini"""
        
        config = GeminiConfig.from_env()
        
        async with GeminiClient(config) as client:
            prompt = self._build_followup_prompt(subject, message, count, custom_instructions)
            
            request = GenerateContentRequest(
                model=config.default_model,
                contents=[
                    Content(parts=[ContentPart(text=prompt)])
                ],
                generation_config=GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2000
                )
            )
            
            response = await client.generate_content(request)
            
            # Parse response
            if response.candidates and response.candidates[0].content.parts:
                content = response.candidates[0].content.parts[0].text.strip()
                return self._parse_followup_response(content)
            
            raise APIParsingError("No content generated", "Gemini")
    
    def _build_followup_prompt(
        self, 
        subject: str, 
        message: str, 
        count: int,
        custom_instructions: Optional[str]
    ) -> str:
        """Build the prompt for followup generation"""
        
        # Default delay schedules (in hours)
        default_delays = [24, 72, 168, 336, 504, 672, 840]  # 1d, 3d, 1w, 2w, 3w, 4w, 5w
        delays = default_delays[:count]
        
        base_prompt = f"""
Based on the following initial outreach message, create {count} follow-up messages for an influencer marketing campaign.

Original Subject: {subject}
Original Message: {message}

Requirements for each follow-up:
1. Different tone and approach for each message
2. Progressively more direct but maintain professionalism
3. Add unique value in each message (different angles, benefits, urgency)
4. Keep messages concise (under 200 words each)
5. Include compelling subject lines
6. Make them feel personal, not automated

Follow-up timing: {', '.join([f'{i+1}: {d}h' for i, d in enumerate(delays)])}

"""
        
        if custom_instructions:
            base_prompt += f"\nAdditional Instructions: {custom_instructions}\n"
        
        base_prompt += f"""
Return ONLY a valid JSON array with exactly this structure:
[
  {{"content": "follow-up message 1", "delay_hours": {delays[0]}, "subject": "compelling subject 1"}},
  {{"content": "follow-up message 2", "delay_hours": {delays[1] if len(delays) > 1 else delays[0]}, "subject": "compelling subject 2"}},
  ... (continue for all {count} follow-ups)
]

Important: Return ONLY the JSON array, no other text or formatting.
"""
        
        return base_prompt
    
    def _parse_followup_response(self, content: str) -> List[FollowupTemplate]:
        """Parse AI response and return structured followup templates"""
        
        try:
            # Clean the response (remove markdown, extra spaces, etc.)
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # Parse JSON
            followups_data = json.loads(content)
            
            if not isinstance(followups_data, list):
                raise ValueError("Response must be a JSON array")
            
            # Convert to structured templates
            followups = []
            for i, followup in enumerate(followups_data, 1):
                if not isinstance(followup, dict):
                    raise ValueError(f"Followup {i} must be an object")
                
                required_fields = ["content", "delay_hours"]
                for field in required_fields:
                    if field not in followup:
                        raise ValueError(f"Followup {i} missing required field: {field}")
                
                followups.append(FollowupTemplate(
                    content=followup["content"],
                    delay_hours=int(followup["delay_hours"]),
                    subject=followup.get("subject")
                ))
            
            return followups
            
        except json.JSONDecodeError as e:
            raise APIParsingError(f"Failed to parse JSON response: {str(e)}", "AI")
        except (ValueError, KeyError, TypeError) as e:
            raise APIParsingError(f"Invalid response format: {str(e)}", "AI")

    async def generate_subject_lines(
        self,
        content: str,
        count: int = 5,
        tone: str = "professional",
        provider: Union[AIProvider, str] = AIProvider.OPENAI
    ) -> List[str]:
        """Generate subject lines for given content"""
        
        # Implementation for subject line generation
        # This would follow similar pattern as followup generation
        pass
    
    async def improve_message_content(
        self,
        original_content: str,
        improvements: List[str],
        provider: Union[AIProvider, str] = AIProvider.OPENAI
    ) -> str:
        """Improve existing message content based on feedback"""
        
        # Implementation for content improvement  
        # This would follow similar pattern as followup generation
        pass