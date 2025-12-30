"""
AiGentsy Graphics Engine
Intelligent routing and execution for graphics generation tasks

Author: Wade
Date: December 30, 2024
Status: Production Ready
"""

import os
import httpx
import base64
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import re


class GraphicsDetector:
    """Detects if opportunity requires graphics work"""
    
    GRAPHICS_KEYWORDS = {
        'logo': 0.95,
        'design': 0.85,
        'banner': 0.90,
        'graphic': 0.95,
        'image': 0.70,
        'illustration': 0.90,
        'icon': 0.85,
        'mockup': 0.80,
        'visual': 0.75,
        'branding': 0.85,
        'poster': 0.90,
        'flyer': 0.90,
        'social media': 0.80,
        'thumbnail': 0.85,
        'cover': 0.75,
        'header': 0.80,
        'ui design': 0.70,
        'artwork': 0.85
    }
    
    def is_graphics_task(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Determine if this is a graphics opportunity"""
        
        title = opportunity.get('title', '').lower()
        description = opportunity.get('description', '').lower()
        text = f"{title} {description}"
        
        confidence = 0
        matches = []
        
        for keyword, weight in self.GRAPHICS_KEYWORDS.items():
            if keyword in text:
                confidence = max(confidence, weight)
                matches.append(keyword)
        
        # Reduce confidence if code-related
        if 'code' in text or 'programming' in text or 'function' in text:
            confidence *= 0.3
        
        # Increase confidence for design tools
        if 'photoshop' in text or 'illustrator' in text or 'figma' in text:
            confidence = max(confidence, 0.9)
        
        return {
            'is_graphics': confidence > 0.6,
            'confidence': confidence,
            'matched_keywords': matches,
            'reasoning': f"Detected {len(matches)} graphics keywords with {confidence:.0%} confidence"
        }


class TaskTypeClassifier:
    """Classifies type of graphics work"""
    
    TASK_TYPES = {
        'logo': {
            'keywords': ['logo', 'brand mark', 'identity', 'logotype'],
            'typical_deliverables': 3,
            'formats': ['PNG', 'SVG'],
            'complexity': 'medium'
        },
        'banner': {
            'keywords': ['banner', 'header', 'cover', 'hero image'],
            'typical_deliverables': 2,
            'formats': ['PNG', 'JPG'],
            'complexity': 'low'
        },
        'social_media': {
            'keywords': ['instagram', 'facebook', 'twitter', 'social', 'post', 'story'],
            'typical_deliverables': 5,
            'formats': ['PNG', 'JPG'],
            'complexity': 'low'
        },
        'product_mockup': {
            'keywords': ['mockup', 'product photo', 'packaging'],
            'typical_deliverables': 3,
            'formats': ['PNG', 'JPG'],
            'complexity': 'medium'
        },
        'illustration': {
            'keywords': ['illustration', 'artwork', 'drawing', 'custom art'],
            'typical_deliverables': 1,
            'formats': ['PNG', 'JPG'],
            'complexity': 'high'
        },
        'icon_set': {
            'keywords': ['icon', 'icon set', 'symbols', 'icons'],
            'typical_deliverables': 10,
            'formats': ['PNG', 'SVG'],
            'complexity': 'medium'
        },
        'marketing': {
            'keywords': ['flyer', 'poster', 'brochure', 'ad', 'advertisement', 'promotional'],
            'typical_deliverables': 2,
            'formats': ['PNG', 'PDF'],
            'complexity': 'medium'
        }
    }
    
    def classify_task(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Determine specific type of graphics work"""
        
        text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}".lower()
        
        scores = {}
        for task_type, config in self.TASK_TYPES.items():
            score = sum(1 for keyword in config['keywords'] if keyword in text)
            if score > 0:
                scores[task_type] = score
        
        if not scores:
            return {
                'type': 'generic',
                'confidence': 0.5,
                'config': {'typical_deliverables': 1, 'formats': ['PNG'], 'complexity': 'medium'}
            }
        
        best_type = max(scores, key=scores.get)
        
        return {
            'type': best_type,
            'confidence': min(scores[best_type] / 2, 1.0),
            'config': self.TASK_TYPES[best_type],
            'all_scores': scores
        }


class RequirementsExtractor:
    """Extracts specific requirements from opportunity"""
    
    def extract_requirements(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Pull out key requirements"""
        
        text = f"{opportunity.get('title', '')} {opportunity.get('description', '')}"
        
        return {
            'dimensions': self._extract_dimensions(text),
            'colors': self._extract_colors(text),
            'style': self._extract_style(text),
            'quantity': self._extract_quantity(text),
            'formats': self._extract_formats(text),
            'deadline': self._extract_deadline(text),
            'budget': self._extract_budget(text)
        }
    
    def _extract_dimensions(self, text: str) -> Optional[Dict[str, int]]:
        """Find dimension specifications"""
        
        patterns = [
            r'(\d+)\s*[xX×]\s*(\d+)',
            r'(\d+)\s*by\s*(\d+)',
            r'(\d+)px\s*[xX×]\s*(\d+)px'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return {
                    'width': int(match.group(1)),
                    'height': int(match.group(2))
                }
        
        text_lower = text.lower()
        if 'instagram' in text_lower:
            return {'width': 1080, 'height': 1080}
        elif 'facebook cover' in text_lower:
            return {'width': 820, 'height': 312}
        elif 'twitter header' in text_lower:
            return {'width': 1500, 'height': 500}
        
        return None
    
    def _extract_colors(self, text: str) -> List[str]:
        """Find color specifications"""
        text_lower = text.lower()
        
        colors = []
        color_keywords = ['blue', 'red', 'green', 'yellow', 'purple', 'orange', 
                         'black', 'white', 'gray', 'grey', 'pink', 'brown']
        
        for color in color_keywords:
            if color in text_lower:
                colors.append(color)
        
        hex_colors = re.findall(r'#[0-9A-Fa-f]{6}', text)
        colors.extend(hex_colors)
        
        return colors
    
    def _extract_style(self, text: str) -> List[str]:
        """Identify design style preferences"""
        text_lower = text.lower()
        
        styles = {
            'minimalist': ['minimalist', 'minimal', 'clean', 'simple'],
            'modern': ['modern', 'contemporary', 'sleek'],
            'vintage': ['vintage', 'retro', 'classic', 'old'],
            'professional': ['professional', 'corporate', 'business'],
            'playful': ['playful', 'fun', 'colorful', 'vibrant'],
            'elegant': ['elegant', 'sophisticated', 'luxury'],
            'bold': ['bold', 'striking', 'dramatic'],
            'artistic': ['artistic', 'creative', 'unique']
        }
        
        detected_styles = []
        for style_name, keywords in styles.items():
            if any(kw in text_lower for kw in keywords):
                detected_styles.append(style_name)
        
        return detected_styles if detected_styles else ['modern']
    
    def _extract_quantity(self, text: str) -> int:
        """How many deliverables?"""
        numbers = re.findall(r'\b(\d+)\s*(?:variations?|versions?|concepts?|designs?)\b', text.lower())
        
        if numbers:
            return int(numbers[0])
        
        if 'social media' in text.lower():
            return 5
        elif 'logo' in text.lower():
            return 3
        else:
            return 1
    
    def _extract_formats(self, text: str) -> List[str]:
        """Required file formats"""
        text_upper = text.upper()
        
        formats = []
        format_types = ['PNG', 'JPG', 'JPEG', 'SVG', 'PDF', 'AI', 'PSD', 'GIF']
        
        for fmt in format_types:
            if fmt in text_upper:
                formats.append(fmt)
        
        return formats if formats else ['PNG']
    
    def _extract_deadline(self, text: str) -> str:
        """Extract deadline info"""
        text_lower = text.lower()
        
        if 'asap' in text_lower or 'urgent' in text_lower:
            return 'urgent'
        elif 'rush' in text_lower:
            return 'rush'
        elif '24 hours' in text_lower or '1 day' in text_lower:
            return '1_day'
        elif '48 hours' in text_lower or '2 days' in text_lower:
            return '2_days'
        
        return 'normal'
    
    def _extract_budget(self, text: str) -> Optional[float]:
        """Extract budget info"""
        amounts = re.findall(r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)', text)
        
        if amounts:
            return float(amounts[0].replace(',', ''))
        
        return None


class PromptEngineer:
    """Generates optimal prompts for image generation"""
    
    def generate_prompt(self, analysis: Dict[str, Any], opportunity: Dict[str, Any]) -> Dict[str, str]:
        """Create AI-ready prompt"""
        
        task_type = analysis['task_type']['type']
        requirements = analysis['requirements']
        
        components = []
        
        # Subject
        subject = self._extract_subject(opportunity)
        components.append(subject)
        
        # Style
        styles = requirements.get('style', ['modern'])
        if styles:
            components.append(', '.join(styles) + ' style')
        
        # Colors
        colors = requirements.get('colors')
        if colors:
            components.append(f"{' and '.join(colors[:3])} colors")  # Limit to 3 colors
        
        # Task-specific keywords
        if task_type == 'logo':
            components.append('vector style, simple, iconic, professional')
        elif task_type == 'illustration':
            components.append('detailed illustration, artistic')
        elif task_type == 'social_media':
            components.append('eye-catching, vibrant, attention-grabbing')
        elif task_type == 'marketing':
            components.append('professional, polished, commercial')
        
        # Quality
        components.append('high quality, professional, 4k')
        
        prompt = ', '.join(components)
        negative_prompt = 'blurry, low quality, watermark, text, signature, distorted, ugly, deformed'
        
        return {
            'prompt': prompt,
            'negative_prompt': negative_prompt,
            'reasoning': f'Generated prompt for {task_type} task with {len(components)} components'
        }
    
    def _extract_subject(self, opportunity: Dict[str, Any]) -> str:
        """Extract main subject"""
        title = opportunity.get('title', '')
        
        # Clean up title
        cleaned = title.lower()
        for word in ['need', 'looking for', 'want', 'design', 'create', 'make']:
            cleaned = cleaned.replace(word, '')
        
        return cleaned.strip() or 'professional design'


class GraphicsRouter:
    """Intelligently routes graphics tasks to best AI worker"""
    
    def __init__(self):
        self.detector = GraphicsDetector()
        self.classifier = TaskTypeClassifier()
        self.extractor = RequirementsExtractor()
        self.prompt_engineer = PromptEngineer()
    
    def route_task(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Main routing logic"""
        
        # Step 1: Analyze task
        analysis = {
            'is_graphics': self.detector.is_graphics_task(opportunity),
            'task_type': self.classifier.classify_task(opportunity),
            'requirements': self.extractor.extract_requirements(opportunity)
        }
        
        # Step 2: Select AI worker
        worker_decision = self._select_ai_worker(analysis, opportunity)
        
        # Step 3: Generate execution plan
        execution_plan = self._create_execution_plan(worker_decision, analysis)
        
        # Step 4: Generate prompt
        prompt_data = self.prompt_engineer.generate_prompt(analysis, opportunity)
        
        return {
            'analysis': analysis,
            'selected_worker': worker_decision['worker'],
            'reasoning': worker_decision['reasoning'],
            'execution_plan': execution_plan,
            'prompt': prompt_data,
            'estimated_cost': execution_plan['estimated_cost'],
            'estimated_time': execution_plan['estimated_time']
        }
    
    def _select_ai_worker(self, analysis: Dict[str, Any], opportunity: Dict[str, Any]) -> Dict[str, str]:
        """Select best AI worker"""
        
        task_type = analysis['task_type']['type']
        requirements = analysis['requirements']
        budget = requirements.get('budget', 0)
        deadline = requirements.get('deadline', 'normal')
        
        scores = {
            'stable_diffusion': 10,  # Start with SD as default
            'dalle3': 5
        }
        
        # Speed requirements
        if deadline in ['urgent', 'rush', '1_day']:
            scores['stable_diffusion'] += 10
        
        # Budget
        if budget and budget > 500:
            scores['dalle3'] += 8  # Premium work
        
        # Text integration
        if 'text' in opportunity.get('description', '').lower():
            scores['dalle3'] += 10
        
        # Quality requirements
        if 'professional' in opportunity.get('description', '').lower() or 'high-quality' in opportunity.get('description', '').lower():
            scores['dalle3'] += 5
        
        winner = max(scores, key=scores.get)
        
        return {
            'worker': winner,
            'scores': scores,
            'reasoning': f"Selected {winner} (score: {scores[winner]}) - Best for this task type and requirements"
        }
    
    def _create_execution_plan(self, worker_decision: Dict, analysis: Dict) -> Dict[str, Any]:
        """Create detailed execution plan"""
        
        worker = worker_decision['worker']
        requirements = analysis['requirements']
        
        quantity = requirements.get('quantity', 3)
        dimensions = requirements.get('dimensions', {'width': 1024, 'height': 1024})
        
        plan = {
            'worker': worker,
            'parameters': {},
            'estimated_cost': 0,
            'estimated_time': 0
        }
        
        if worker == 'stable_diffusion':
            plan['parameters'] = {
                'model': 'stable-diffusion-xl-1024-v1-0',
                'samples': quantity,
                'steps': 30,
                'cfg_scale': 7,
                'width': dimensions.get('width', 1024),
                'height': dimensions.get('height', 1024)
            }
            plan['estimated_cost'] = 0.004 * quantity
            plan['estimated_time'] = 10 * quantity
            
        elif worker == 'dalle3':
            plan['parameters'] = {
                'model': 'dall-e-3',
                'size': '1024x1024',
                'quality': 'standard',
                'n': 1
            }
            plan['estimated_cost'] = 0.04 * quantity
            plan['estimated_time'] = 15 * quantity
        
        return plan


class StableDiffusionExecutor:
    """Executes graphics generation via Stable Diffusion"""
    
    def __init__(self):
        self.api_key = os.getenv('STABILITY_API_KEY')
        if not self.api_key:
            raise ValueError("STABILITY_API_KEY environment variable not set")
        
        self.base_url = "https://api.stability.ai/v1/generation"
    
    async def generate(self, prompt: str, negative_prompt: str, parameters: Dict) -> Dict[str, Any]:
        """Generate images via Stable Diffusion API"""
        
        engine_id = parameters.get('model', 'stable-diffusion-xl-1024-v1-0')
        
        payload = {
            "text_prompts": [
                {"text": prompt, "weight": 1},
                {"text": negative_prompt, "weight": -1}
            ],
            "cfg_scale": parameters.get('cfg_scale', 7),
            "height": parameters.get('height', 1024),
            "width": parameters.get('width', 1024),
            "samples": parameters.get('samples', 3),
            "steps": parameters.get('steps', 30),
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/{engine_id}/text-to-image",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json=payload
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"API Error: {response.status_code} - {response.text}"
                }
            
            data = response.json()
            
            # Save images
            images = []
            for i, artifact in enumerate(data.get('artifacts', [])):
                image_data = artifact['base64']
                filename = f"/tmp/generated_{datetime.now().timestamp()}_{i}.png"
                
                with open(filename, 'wb') as f:
                    f.write(base64.b64decode(image_data))
                
                images.append({
                    'filename': filename,
                    'base64': image_data,
                    'seed': artifact.get('seed')
                })
            
            return {
                'success': True,
                'ai_worker': 'stable_diffusion',
                'images': images,
                'count': len(images),
                'prompt': prompt,
                'parameters': parameters,
                'cost': 0.004 * len(images)
            }


class GraphicsEngine:
    """Main graphics engine orchestrator"""
    
    def __init__(self):
        self.router = GraphicsRouter()
        self.sd_executor = StableDiffusionExecutor()
    
    async def process_graphics_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Complete graphics workflow"""
        
        # Step 1: Route task
        routing = self.router.route_task(opportunity)
        
        # Step 2: Check if graphics task
        if not routing['analysis']['is_graphics']['is_graphics']:
            return {
                'success': False,
                'error': 'Not a graphics task',
                'analysis': routing['analysis']
            }
        
        # Step 3: Execute based on selected worker
        if routing['selected_worker'] == 'stable_diffusion':
            result = await self.sd_executor.generate(
                prompt=routing['prompt']['prompt'],
                negative_prompt=routing['prompt']['negative_prompt'],
                parameters=routing['execution_plan']['parameters']
            )
        else:
            # DALL-E 3 not implemented yet
            result = {
                'success': False,
                'error': 'DALL-E 3 not implemented yet'
            }
        
        if result['success']:
            return {
                'success': True,
                'routing': routing,
                'generation': result,
                'deliverable_ready': True
            }
        else:
            return {
                'success': False,
                'error': result.get('error'),
                'routing': routing
            }


# Export main class
__all__ = ['GraphicsEngine', 'GraphicsRouter', 'StableDiffusionExecutor']
