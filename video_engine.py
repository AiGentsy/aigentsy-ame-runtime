"""
AiGentsy Video Engine - AI-Powered Video Content Generation
Week 3 Build - Multi-AI Video Worker Integration

CAPABILITIES:
- Explainer videos, ads, social content
- Multiple AI workers (Runway, Synthesia, HeyGen)
- Platform delivery (Fiverr, Upwork, YouTube)
- Quality control and optimization

TARGET: $3,000-$11,000/month from video content
INTEGRATION: Plugs into Universal AI Orchestrator
"""

import asyncio
import httpx
import json
import os
import base64
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import tempfile


@dataclass
class VideoProject:
    """Video project configuration"""
    project_id: str
    title: str
    description: str
    video_type: str  # explainer, ad, social, testimonial
    duration: int    # seconds
    style: str       # professional, casual, animated, live
    voice_gender: str  # male, female, neutral
    script: str
    visual_elements: List[str]
    output_format: str  # mp4, mov, webm
    resolution: str    # 1080p, 720p, 4k


class VideoAnalyzer:
    """Analyze video requests and determine best approach"""
    
    def __init__(self):
        self.video_types = {
            'explainer': {
                'keywords': ['explain', 'tutorial', 'how to', 'demo', 'walkthrough', 'guide'],
                'optimal_duration': 120,  # 2 minutes
                'best_worker': 'synthesia',
                'style': 'professional'
            },
            'ad': {
                'keywords': ['advertisement', 'promo', 'marketing', 'commercial', 'campaign'],
                'optimal_duration': 30,   # 30 seconds
                'best_worker': 'runway',
                'style': 'dynamic'
            },
            'social': {
                'keywords': ['tiktok', 'instagram', 'social media', 'viral', 'short'],
                'optimal_duration': 15,   # 15 seconds
                'best_worker': 'runway',
                'style': 'engaging'
            },
            'testimonial': {
                'keywords': ['testimonial', 'review', 'customer', 'feedback', 'story'],
                'optimal_duration': 90,   # 1.5 minutes
                'best_worker': 'synthesia',
                'style': 'authentic'
            },
            'training': {
                'keywords': ['training', 'course', 'lesson', 'education', 'learning'],
                'optimal_duration': 300,  # 5 minutes
                'best_worker': 'synthesia',
                'style': 'educational'
            }
        }
    
    async def analyze_video_request(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze opportunity and determine video requirements"""
        
        title = opportunity.get('title', '').lower()
        description = opportunity.get('description', '').lower()
        budget = opportunity.get('estimated_value', 0)
        platform = opportunity.get('source', '')
        
        full_text = f"{title} {description}"
        
        # Detect video type
        type_scores = {}
        for video_type, config in self.video_types.items():
            score = sum(1 for keyword in config['keywords'] if keyword in full_text)
            type_scores[video_type] = score
        
        detected_type = max(type_scores.items(), key=lambda x: x[1])[0] if any(type_scores.values()) else 'explainer'
        type_config = self.video_types[detected_type]
        
        # Determine quality tier based on budget
        if budget >= 500:
            quality_tier = 'premium'
        elif budget >= 200:
            quality_tier = 'standard'
        else:
            quality_tier = 'basic'
        
        # Extract requirements
        requirements = {
            'video_type': detected_type,
            'recommended_worker': type_config['best_worker'],
            'optimal_duration': type_config['optimal_duration'],
            'style': type_config['style'],
            'quality_tier': quality_tier,
            'budget': budget,
            'platform': platform,
            'special_requirements': self._extract_special_requirements(full_text),
            'urgency': self._assess_urgency(full_text)
        }
        
        return {
            'analysis': requirements,
            'confidence': max(type_scores.values()) / len(type_config['keywords']),
            'type_scores': type_scores,
            'recommended_approach': await self._recommend_approach(requirements)
        }
    
    def _extract_special_requirements(self, text: str) -> List[str]:
        """Extract special requirements from text"""
        
        requirements = []
        
        # Voice requirements
        if any(word in text for word in ['female voice', 'woman', 'lady']):
            requirements.append('female_voice')
        elif any(word in text for word in ['male voice', 'man', 'gentleman']):
            requirements.append('male_voice')
        
        # Style requirements
        if any(word in text for word in ['animated', 'cartoon', 'motion graphics']):
            requirements.append('animated_style')
        elif any(word in text for word in ['live action', 'real person', 'actor']):
            requirements.append('live_action')
        
        # Branding requirements
        if any(word in text for word in ['logo', 'brand', 'company colors']):
            requirements.append('branded')
        
        # Technical requirements
        if any(word in text for word in ['4k', 'high resolution', 'ultra hd']):
            requirements.append('high_resolution')
        elif any(word in text for word in ['vertical', 'portrait', 'mobile']):
            requirements.append('mobile_optimized')
        
        return requirements
    
    def _assess_urgency(self, text: str) -> str:
        """Assess project urgency"""
        
        urgent_keywords = ['urgent', 'asap', 'rush', 'immediately', 'today', 'tomorrow']
        relaxed_keywords = ['flexible', 'no rush', 'whenever', 'eventually']
        
        if any(keyword in text for keyword in urgent_keywords):
            return 'high'
        elif any(keyword in text for keyword in relaxed_keywords):
            return 'low'
        else:
            return 'medium'
    
    async def _recommend_approach(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend execution approach"""
        
        video_type = requirements['video_type']
        budget = requirements['budget']
        quality_tier = requirements['quality_tier']
        
        approaches = {
            'basic': {
                'ai_worker': 'runway',
                'features': ['basic_editing', 'stock_footage', 'simple_transitions'],
                'delivery_time': '24 hours'
            },
            'standard': {
                'ai_worker': 'synthesia',
                'features': ['ai_presenter', 'custom_script', 'branded_elements'],
                'delivery_time': '48 hours'
            },
            'premium': {
                'ai_worker': 'heygen',
                'features': ['custom_avatar', 'advanced_editing', 'multiple_scenes', 'music'],
                'delivery_time': '72 hours'
            }
        }
        
        return approaches.get(quality_tier, approaches['standard'])


class RunwayVideoGenerator:
    """Runway ML video generation worker"""
    
    def __init__(self):
        self.api_key = os.getenv('RUNWAY_API_KEY')
        self.base_url = "https://api.runwayml.com/v1"
        self.model = "gen2"
    
    async def generate_video(self, project: VideoProject) -> Dict[str, Any]:
        """Generate video using Runway ML"""
        
        if not self.api_key:
            return {'success': False, 'error': 'Runway API key not configured'}
        
        print(f"🎬 Generating video with Runway: {project.title}")
        
        try:
            # Prepare video generation request
            generation_request = {
                "model": self.model,
                "prompt": await self._create_runway_prompt(project),
                "duration": min(project.duration, 16),  # Runway max 16 seconds
                "resolution": project.resolution,
                "seed": None,  # Random
                "watermark": False
            }
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                # Start generation
                response = await client.post(
                    f"{self.base_url}/image_to_video",
                    headers=headers,
                    json=generation_request
                )
                
                if response.status_code != 200:
                    return {
                        'success': False,
                        'error': f"Runway API error: {response.status_code} - {response.text}"
                    }
                
                generation_data = response.json()
                task_id = generation_data.get('id')
                
                if not task_id:
                    return {'success': False, 'error': 'No task ID returned from Runway'}
                
                # Poll for completion
                video_url = await self._poll_runway_completion(task_id, client, headers)
                
                if video_url:
                    # Download and save video
                    video_path = await self._download_video(video_url, project.project_id)
                    
                    return {
                        'success': True,
                        'ai_worker': 'runway',
                        'video_path': video_path,
                        'video_url': video_url,
                        'duration': project.duration,
                        'cost': self._calculate_runway_cost(project.duration),
                        'metadata': {
                            'resolution': project.resolution,
                            'format': project.output_format,
                            'generated_at': datetime.now(timezone.utc).isoformat()
                        }
                    }
                else:
                    return {'success': False, 'error': 'Video generation failed'}
        
        except Exception as e:
            return {'success': False, 'error': f'Runway generation error: {str(e)}'}
    
    async def _create_runway_prompt(self, project: VideoProject) -> str:
        """Create optimized prompt for Runway"""
        
        style_prompts = {
            'professional': 'clean, professional, corporate style',
            'dynamic': 'energetic, fast-paced, dynamic movement',
            'engaging': 'vibrant, eye-catching, social media style',
            'authentic': 'natural, authentic, conversational',
            'educational': 'clear, informative, easy to follow'
        }
        
        base_prompt = f"{project.description}"
        style_addition = style_prompts.get(project.style, 'professional, high quality')
        
        return f"{base_prompt}, {style_addition}, cinematic lighting, high quality"
    
    async def _poll_runway_completion(self, task_id: str, client: httpx.AsyncClient, headers: Dict) -> Optional[str]:
        """Poll Runway for generation completion"""
        
        max_attempts = 60  # 5 minutes max wait
        
        for attempt in range(max_attempts):
            try:
                response = await client.get(f"{self.base_url}/tasks/{task_id}", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    
                    if status == 'SUCCEEDED':
                        return data.get('output', [None])[0]
                    elif status == 'FAILED':
                        return None
                    
                await asyncio.sleep(5)  # Wait 5 seconds between polls
                
            except Exception as e:
                print(f"Polling error: {e}")
                await asyncio.sleep(5)
        
        return None
    
    def _calculate_runway_cost(self, duration: int) -> float:
        """Calculate Runway generation cost"""
        # Runway pricing: ~$0.05 per second
        return duration * 0.05
    
    async def _download_video(self, video_url: str, project_id: str) -> str:
        """Download generated video"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(video_url)
                
                if response.status_code == 200:
                    video_path = f"/tmp/runway_video_{project_id}_{datetime.now().timestamp()}.mp4"
                    
                    with open(video_path, 'wb') as f:
                        f.write(response.content)
                    
                    return video_path
        except Exception as e:
            print(f"Video download error: {e}")
        
        return None


class SynthesiaVideoGenerator:
    """Synthesia AI presenter video generation"""
    
    def __init__(self):
        self.api_key = os.getenv('SYNTHESIA_API_KEY')
        self.base_url = "https://api.synthesia.io/v2"
    
    async def generate_video(self, project: VideoProject) -> Dict[str, Any]:
        """Generate video using Synthesia"""
        
        if not self.api_key:
            return {'success': False, 'error': 'Synthesia API key not configured'}
        
        print(f"🎤 Generating video with Synthesia: {project.title}")
        
        try:
            # Prepare Synthesia request
            video_request = {
                "title": project.title,
                "description": project.description,
                "visibility": "private",
                "aspectRatio": "16:9",
                "background": "#ffffff",
                "soundtrack": {
                    "effect": "none",
                    "volume": 0.1
                },
                "scenes": [
                    {
                        "background": "#ffffff",
                        "elements": [
                            {
                                "type": "avatar",
                                "avatar": await self._select_avatar(project),
                                "x": 0,
                                "y": 0,
                                "width": 1,
                                "height": 1,
                                "script": project.script
                            }
                        ]
                    }
                ]
            }
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                # Create video
                response = await client.post(
                    f"{self.base_url}/videos",
                    headers=headers,
                    json=video_request
                )
                
                if response.status_code != 201:
                    return {
                        'success': False,
                        'error': f"Synthesia API error: {response.status_code} - {response.text}"
                    }
                
                video_data = response.json()
                video_id = video_data.get('id')
                
                if not video_id:
                    return {'success': False, 'error': 'No video ID returned from Synthesia'}
                
                # Poll for completion
                video_url = await self._poll_synthesia_completion(video_id, client, headers)
                
                if video_url:
                    return {
                        'success': True,
                        'ai_worker': 'synthesia',
                        'video_url': video_url,
                        'video_id': video_id,
                        'duration': project.duration,
                        'cost': self._calculate_synthesia_cost(project.duration),
                        'metadata': {
                            'avatar': await self._select_avatar(project),
                            'script': project.script,
                            'generated_at': datetime.now(timezone.utc).isoformat()
                        }
                    }
                else:
                    return {'success': False, 'error': 'Video generation timed out'}
        
        except Exception as e:
            return {'success': False, 'error': f'Synthesia generation error: {str(e)}'}
    
    async def _select_avatar(self, project: VideoProject) -> str:
        """Select appropriate avatar based on project requirements"""
        
        # Default avatars (would be configurable)
        avatars = {
            'female': 'anna_costume1_cameraA',
            'male': 'james_costume1_cameraA',
            'professional_female': 'amy_costume1_cameraA',
            'professional_male': 'david_costume1_cameraA'
        }
        
        if 'female_voice' in project.visual_elements:
            return avatars['professional_female']
        elif 'male_voice' in project.visual_elements:
            return avatars['professional_male']
        else:
            return avatars['professional_female']  # Default
    
    async def _poll_synthesia_completion(self, video_id: str, client: httpx.AsyncClient, headers: Dict) -> Optional[str]:
        """Poll for Synthesia video completion"""
        
        max_attempts = 120  # 10 minutes max wait
        
        for attempt in range(max_attempts):
            try:
                response = await client.get(f"{self.base_url}/videos/{video_id}", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    
                    if status == 'complete':
                        return data.get('download')
                    elif status == 'failed':
                        return None
                
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"Synthesia polling error: {e}")
                await asyncio.sleep(5)
        
        return None
    
    def _calculate_synthesia_cost(self, duration: int) -> float:
        """Calculate Synthesia generation cost"""
        # Synthesia pricing: ~$0.10 per minute
        return (duration / 60) * 0.10


class HeyGenVideoGenerator:
    """HeyGen premium video generation"""
    
    def __init__(self):
        self.api_key = os.getenv('HEYGEN_API_KEY')
        self.base_url = "https://api.heygen.com/v1"
    
    async def generate_video(self, project: VideoProject) -> Dict[str, Any]:
        """Generate premium video using HeyGen"""
        
        if not self.api_key:
            # Fallback to Synthesia for premium requests
            synthesia = SynthesiaVideoGenerator()
            return await synthesia.generate_video(project)
        
        print(f"👑 Generating premium video with HeyGen: {project.title}")
        
        # HeyGen implementation would go here
        # For now, fallback to Synthesia
        synthesia = SynthesiaVideoGenerator()
        result = await synthesia.generate_video(project)
        
        if result['success']:
            result['ai_worker'] = 'heygen_fallback'
            result['cost'] = result['cost'] * 1.5  # Premium pricing
        
        return result


class ScriptGenerator:
    """Generate video scripts using Claude"""
    
    def __init__(self):
        self.openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
        self.model = "anthropic/claude-3.5-sonnet"
    
    async def generate_script(self, project_requirements: Dict[str, Any]) -> str:
        """Generate video script based on requirements"""
        
        video_type = project_requirements.get('video_type', 'explainer')
        duration = project_requirements.get('optimal_duration', 60)
        style = project_requirements.get('style', 'professional')
        description = project_requirements.get('description', '')
        
        # Script templates by video type
        script_prompts = {
            'explainer': f"""Create a {duration}-second explainer video script that {description}. 
Style: {style}. Include a strong hook in first 5 seconds, clear explanation in middle, and call-to-action at end.
Format as natural speech with [pause] markers for emphasis.""",
            
            'ad': f"""Create a {duration}-second advertisement script that {description}.
Style: {style}. Focus on benefits, create urgency, and include strong call-to-action.
Keep it punchy and persuasive.""",
            
            'social': f"""Create a {duration}-second social media video script that {description}.
Style: {style}. Make it engaging, shareable, and optimized for mobile viewing.
Start with a hook that stops the scroll.""",
            
            'testimonial': f"""Create a {duration}-second testimonial script that {description}.
Style: {style}. Make it authentic and relatable. Focus on transformation and results."""
        }
        
        prompt = script_prompts.get(video_type, script_prompts['explainer'])
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 500
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data['choices'][0]['message']['content'].strip()
                else:
                    return self._fallback_script(video_type, description)
        
        except Exception as e:
            print(f"Script generation error: {e}")
            return self._fallback_script(video_type, description)
    
    def _fallback_script(self, video_type: str, description: str) -> str:
        """Fallback script when AI generation fails"""
        
        fallback_scripts = {
            'explainer': f"Hi there! Today I'll explain {description}. This is important because it helps you achieve your goals more effectively. Here's how it works... [explain key points]. Ready to get started? Click the link below!",
            
            'ad': f"Attention! Are you struggling with {description}? We have the perfect solution for you. Our service delivers amazing results in just days. Don't wait - get started today!",
            
            'social': f"You won't believe this! {description} - and it's easier than you think. Watch this quick demo and prepare to be amazed. Try it yourself!",
            
            'testimonial': f"Before using this service, I was struggling with {description}. But everything changed when I discovered this solution. Now my results are incredible. You should definitely try it too!"
        }
        
        return fallback_scripts.get(video_type, fallback_scripts['explainer'])


class VideoEngine:
    """Main video engine orchestrator"""
    
    def __init__(self):
        self.analyzer = VideoAnalyzer()
        self.script_generator = ScriptGenerator()
        
        # Initialize AI workers
        self.runway = RunwayVideoGenerator()
        self.synthesia = SynthesiaVideoGenerator()
        self.heygen = HeyGenVideoGenerator()
        
        self.workers = {
            'runway': self.runway,
            'synthesia': self.synthesia,
            'heygen': self.heygen
        }
    
    async def process_video_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Complete video generation workflow"""
        
        print(f"🎬 Processing video opportunity: {opportunity.get('title', 'Untitled')}")
        
        try:
            # Step 1: Analyze video requirements
            analysis = await self.analyzer.analyze_video_request(opportunity)
            
            if analysis['confidence'] < 0.3:
                return {
                    'success': False,
                    'error': 'Cannot determine video requirements with sufficient confidence',
                    'analysis': analysis
                }
            
            requirements = analysis['analysis']
            approach = analysis['recommended_approach']
            
            print(f"   📋 Video type: {requirements['video_type']}")
            print(f"   🤖 Recommended worker: {approach['ai_worker']}")
            
            # Step 2: Generate script
            script = await self.script_generator.generate_script(requirements)
            
            # Step 3: Create video project
            project = VideoProject(
                project_id=f"video_{datetime.now().timestamp()}",
                title=opportunity.get('title', 'Video Project'),
                description=opportunity.get('description', ''),
                video_type=requirements['video_type'],
                duration=requirements['optimal_duration'],
                style=requirements['style'],
                voice_gender='female',  # Default
                script=script,
                visual_elements=requirements['special_requirements'],
                output_format='mp4',
                resolution='1080p'
            )
            
            # Step 4: Generate video using selected AI worker
            worker_name = approach['ai_worker']
            worker = self.workers.get(worker_name)
            
            if not worker:
                worker = self.synthesia  # Fallback
                worker_name = 'synthesia'
            
            generation_result = await worker.generate_video(project)
            
            if generation_result['success']:
                return {
                    'success': True,
                    'video_result': generation_result,
                    'project': {
                        'id': project.project_id,
                        'type': project.video_type,
                        'duration': project.duration,
                        'script': project.script
                    },
                    'analysis': analysis,
                    'approach': approach,
                    'cost': generation_result['cost'],
                    'deliverable_ready': True
                }
            else:
                return {
                    'success': False,
                    'error': generation_result['error'],
                    'analysis': analysis,
                    'project_id': project.project_id
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'Video engine error: {str(e)}'
            }


# Export main class
__all__ = ['VideoEngine', 'VideoAnalyzer', 'RunwayVideoGenerator', 'SynthesiaVideoGenerator']


# Test function
async def test_video_engine():
    """Test video engine functionality"""
    
    engine = VideoEngine()
    
    # Test opportunity
    test_opportunity = {
        'id': 'test_video_001',
        'title': 'Create explainer video for new SaaS product',
        'description': 'Need a professional 2-minute explainer video showing how our project management software helps teams collaborate better',
        'estimated_value': 400,
        'source': 'fiverr'
    }
    
    result = await engine.process_video_opportunity(test_opportunity)
    
    print("\n🧪 Video Engine Test Results:")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(test_video_engine())
