"""
IMAGE GENERATION: Stability AI + Runway API Integration

Purpose: Generate images for content creation (portfolio showcases, case studies, etc.)
Used by: content_engine.py for Instagram/Twitter visual content

APIs:
- Stability AI (stability.ai) - Text-to-image generation
- Runway (runwayml.com) - Advanced image/video generation

Voice: All prompts follow billionaire-calm aesthetic
- Clean, minimal, professional
- Dark mode preferred
- No flashy/gimmicky elements
"""

import os
import logging
import base64
import httpx
from typing import Dict, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# =============================================================================
# STABILITY AI - Text to Image
# =============================================================================

STABILITY_API_BASE = "https://api.stability.ai"

# Default style for AiGentsy brand aesthetic
AIGENTSY_STYLE_PREFIX = """
Professional, minimal, clean design. Dark mode UI.
Modern tech aesthetic. High contrast. No text overlays.
Photorealistic quality. Corporate professional style.
"""


async def generate_image_stability(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    style_preset: str = "digital-art",
    steps: int = 30,
    add_brand_style: bool = True
) -> Dict:
    """
    Generate an image using Stability AI's SDXL model.

    Args:
        prompt: Text description of the image
        width: Image width (default 1024)
        height: Image height (default 1024)
        style_preset: Style preset (digital-art, photographic, etc.)
        steps: Generation steps (more = higher quality)
        add_brand_style: Add AiGentsy brand style to prompt

    Returns:
        Dict with image data or error
    """
    api_key = os.getenv('STABILITY_API_KEY')
    if not api_key:
        return {'success': False, 'error': 'STABILITY_API_KEY not configured'}

    # Add brand style prefix
    if add_brand_style:
        full_prompt = f"{AIGENTSY_STYLE_PREFIX}\n\n{prompt}"
    else:
        full_prompt = prompt

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            # SDXL 1.0 endpoint
            response = await client.post(
                f"{STABILITY_API_BASE}/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json={
                    "text_prompts": [
                        {"text": full_prompt, "weight": 1.0}
                    ],
                    "cfg_scale": 7,
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "samples": 1,
                    "style_preset": style_preset
                }
            )

            if response.status_code == 200:
                data = response.json()
                artifacts = data.get('artifacts', [])

                if artifacts:
                    image_data = artifacts[0].get('base64')
                    return {
                        'success': True,
                        'provider': 'stability',
                        'image_base64': image_data,
                        'prompt': prompt,
                        'width': width,
                        'height': height,
                        'generated_at': datetime.now(timezone.utc).isoformat()
                    }

                return {'success': False, 'error': 'No image artifacts returned'}

            else:
                error_text = response.text
                logger.warning(f"Stability API error: {response.status_code} - {error_text}")
                return {
                    'success': False,
                    'error': f"API error: {response.status_code}",
                    'details': error_text
                }

    except Exception as e:
        logger.error(f"Stability generation error: {e}")
        return {'success': False, 'error': str(e)}


async def upscale_image_stability(
    image_base64: str,
    width: int = 2048
) -> Dict:
    """
    Upscale an image using Stability AI.

    Args:
        image_base64: Base64 encoded image
        width: Target width

    Returns:
        Dict with upscaled image or error
    """
    api_key = os.getenv('STABILITY_API_KEY')
    if not api_key:
        return {'success': False, 'error': 'STABILITY_API_KEY not configured'}

    try:
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_base64)

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{STABILITY_API_BASE}/v1/generation/esrgan-v1-x2plus/image-to-image/upscale",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Accept": "application/json"
                },
                files={"image": ("image.png", image_bytes, "image/png")},
                data={"width": width}
            )

            if response.status_code == 200:
                data = response.json()
                artifacts = data.get('artifacts', [])
                if artifacts:
                    return {
                        'success': True,
                        'image_base64': artifacts[0].get('base64'),
                        'width': width
                    }

            return {'success': False, 'error': f"Upscale failed: {response.status_code}"}

    except Exception as e:
        logger.error(f"Upscale error: {e}")
        return {'success': False, 'error': str(e)}


# =============================================================================
# RUNWAY ML - Advanced Generation
# =============================================================================

RUNWAY_API_BASE = "https://api.runwayml.com/v1"


async def generate_image_runway(
    prompt: str,
    model: str = "gen-3",
    width: int = 1280,
    height: int = 768,
    add_brand_style: bool = True
) -> Dict:
    """
    Generate an image using Runway's API.

    Args:
        prompt: Text description
        model: Runway model to use
        width: Image width
        height: Image height
        add_brand_style: Add AiGentsy brand style

    Returns:
        Dict with image data or error
    """
    api_key = os.getenv('RUNWAY_API_KEY')
    if not api_key:
        return {'success': False, 'error': 'RUNWAY_API_KEY not configured'}

    if add_brand_style:
        full_prompt = f"{AIGENTSY_STYLE_PREFIX}\n\n{prompt}"
    else:
        full_prompt = prompt

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            # Start generation
            response = await client.post(
                f"{RUNWAY_API_BASE}/image_to_image",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": full_prompt,
                    "model": model,
                    "width": width,
                    "height": height
                }
            )

            if response.status_code in [200, 201]:
                data = response.json()
                # Runway returns task ID for async generation
                task_id = data.get('id') or data.get('task_id')

                if task_id:
                    # Poll for completion
                    result = await _poll_runway_task(client, api_key, task_id)
                    return result
                elif data.get('output'):
                    return {
                        'success': True,
                        'provider': 'runway',
                        'image_url': data['output'],
                        'prompt': prompt,
                        'generated_at': datetime.now(timezone.utc).isoformat()
                    }

                return {'success': False, 'error': 'No task ID or output returned'}

            else:
                return {
                    'success': False,
                    'error': f"API error: {response.status_code}",
                    'details': response.text
                }

    except Exception as e:
        logger.error(f"Runway generation error: {e}")
        return {'success': False, 'error': str(e)}


async def _poll_runway_task(
    client: httpx.AsyncClient,
    api_key: str,
    task_id: str,
    max_attempts: int = 60
) -> Dict:
    """Poll Runway task until completion."""
    import asyncio

    for _ in range(max_attempts):
        try:
            response = await client.get(
                f"{RUNWAY_API_BASE}/tasks/{task_id}",
                headers={"Authorization": f"Bearer {api_key}"}
            )

            if response.status_code == 200:
                data = response.json()
                status = data.get('status')

                if status == 'completed':
                    return {
                        'success': True,
                        'provider': 'runway',
                        'image_url': data.get('output'),
                        'task_id': task_id,
                        'generated_at': datetime.now(timezone.utc).isoformat()
                    }
                elif status == 'failed':
                    return {
                        'success': False,
                        'error': data.get('error', 'Task failed'),
                        'task_id': task_id
                    }

            await asyncio.sleep(3)  # Wait 3 seconds between polls

        except Exception as e:
            logger.warning(f"Poll error: {e}")
            await asyncio.sleep(3)

    return {'success': False, 'error': 'Task timed out', 'task_id': task_id}


async def generate_video_runway(
    prompt: str,
    duration: int = 4,
    add_brand_style: bool = True
) -> Dict:
    """
    Generate a short video using Runway's Gen-3.

    Args:
        prompt: Text description
        duration: Video duration in seconds (4, 8, or 16)
        add_brand_style: Add AiGentsy brand style

    Returns:
        Dict with video URL or error
    """
    api_key = os.getenv('RUNWAY_API_KEY')
    if not api_key:
        return {'success': False, 'error': 'RUNWAY_API_KEY not configured'}

    if add_brand_style:
        full_prompt = f"{AIGENTSY_STYLE_PREFIX}\n\n{prompt}"
    else:
        full_prompt = prompt

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            response = await client.post(
                f"{RUNWAY_API_BASE}/text_to_video",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "prompt": full_prompt,
                    "duration": duration
                }
            )

            if response.status_code in [200, 201]:
                data = response.json()
                task_id = data.get('id') or data.get('task_id')

                if task_id:
                    # Poll for completion (videos take longer)
                    result = await _poll_runway_task(client, api_key, task_id, max_attempts=120)
                    result['type'] = 'video'
                    return result

            return {
                'success': False,
                'error': f"API error: {response.status_code}",
                'details': response.text
            }

    except Exception as e:
        logger.error(f"Runway video error: {e}")
        return {'success': False, 'error': str(e)}


# =============================================================================
# CONTENT-SPECIFIC GENERATORS
# =============================================================================

async def generate_portfolio_image(
    project_type: str,
    style: str = "dashboard"
) -> Dict:
    """
    Generate a portfolio showcase image.

    Args:
        project_type: Type of project (React dashboard, API, etc.)
        style: Visual style (dashboard, mobile, code)

    Returns:
        Dict with image data
    """
    prompts = {
        "dashboard": f"Modern {project_type} dashboard interface, dark mode, data visualization, clean minimal UI, professional software screenshot, no text",
        "mobile": f"Mobile app interface for {project_type}, iOS style, clean design, professional mockup, dark mode, no text",
        "code": f"Clean code editor showing {project_type} code, dark theme, syntax highlighting, professional IDE, no visible text",
        "landing": f"Modern landing page design for {project_type}, minimal hero section, dark mode, professional web design, no text"
    }

    prompt = prompts.get(style, prompts["dashboard"])

    # Try Stability first, fallback to Runway
    result = await generate_image_stability(prompt, width=1200, height=675)  # 16:9

    if not result.get('success'):
        result = await generate_image_runway(prompt, width=1280, height=720)

    result['project_type'] = project_type
    result['style'] = style
    return result


async def generate_case_study_image(
    before: str,
    after: str
) -> Dict:
    """
    Generate a before/after case study image.

    Args:
        before: Description of before state
        after: Description of after state

    Returns:
        Dict with image data
    """
    prompt = f"""
    Split screen comparison image:
    Left side: {before} - cluttered, outdated, chaotic
    Right side: {after} - clean, modern, organized
    Professional case study style, dark mode, minimal design, no text overlays
    """

    result = await generate_image_stability(prompt, width=1200, height=600)

    if not result.get('success'):
        result = await generate_image_runway(prompt, width=1280, height=640)

    result['before'] = before
    result['after'] = after
    return result


async def generate_tech_tip_image(
    tip_topic: str
) -> Dict:
    """
    Generate a tech tip visual.

    Args:
        tip_topic: The tech topic (React Query, API pagination, etc.)

    Returns:
        Dict with image data
    """
    prompt = f"""
    Technical illustration about {tip_topic},
    minimalist icon style, dark background,
    clean vector aesthetic, professional infographic style,
    no text, symbolic representation
    """

    return await generate_image_stability(
        prompt,
        width=1080,
        height=1080,
        style_preset="digital-art"
    )


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

async def save_image_to_storage(
    image_data: Dict,
    filename: str = None
) -> Dict:
    """
    Save generated image to cloud storage and return public URL.

    For now, returns base64 data URI. In production, would upload to S3/GCS.

    Args:
        image_data: Dict with image_base64 or image_url
        filename: Optional filename

    Returns:
        Dict with public URL
    """
    if image_data.get('image_url'):
        return {
            'success': True,
            'url': image_data['image_url'],
            'source': 'direct'
        }

    if image_data.get('image_base64'):
        # For now, return data URI (works for testing)
        # In production, upload to S3/GCS and return public URL
        data_uri = f"data:image/png;base64,{image_data['image_base64']}"

        # TODO: Upload to cloud storage for Instagram posting
        # Instagram Graph API requires publicly accessible URLs

        return {
            'success': True,
            'url': data_uri,
            'source': 'base64',
            'note': 'Data URI - needs cloud upload for Instagram'
        }

    return {'success': False, 'error': 'No image data to save'}


def get_available_providers() -> Dict:
    """Check which image generation providers are configured."""
    return {
        'stability': bool(os.getenv('STABILITY_API_KEY')),
        'runway': bool(os.getenv('RUNWAY_API_KEY'))
    }


# Export
__all__ = [
    'generate_image_stability',
    'generate_image_runway',
    'generate_video_runway',
    'generate_portfolio_image',
    'generate_case_study_image',
    'generate_tech_tip_image',
    'upscale_image_stability',
    'save_image_to_storage',
    'get_available_providers'
]
