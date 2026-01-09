"""
SOCIAL AUTO-POSTING ENGINE
===========================
Autonomous content creation and posting across social platforms.

SUPPORTED PLATFORMS:
- TikTok (Content Posting API)
- Instagram (Graph API)
- YouTube (Data API v3)
- Twitter/X (API v2)
- LinkedIn (Marketing API)

FLOW:
1. User connects social account via OAuth
2. AI generates content (video_engine, graphics_engine, Claude)
3. Content queued for optimal posting time
4. Auto-post to connected platforms
5. Track performance → Feed back to Yield Memory
6. Optimize future content based on what works

ARCHITECTURE:
- OAuth token management (secure storage)
- Content generation pipeline (AI workers)
- Posting queue with scheduling
- Performance tracking integration
- Cross-platform optimization

This closes the INBOUND content creation loop.
"""

import asyncio
import httpx
import os
import json
import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import urllib.parse
from urllib.parse import urlencode


# ============================================================
# PLATFORM CONFIGURATIONS
# ============================================================

class SocialPlatform(str, Enum):
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    FACEBOOK = "facebook"
    PINTEREST = "pinterest"
    THREADS = "threads"


@dataclass
class PlatformConfig:
    """Configuration for each social platform"""
    platform: SocialPlatform
    client_id_env: str
    client_secret_env: str
    oauth_url: str
    token_url: str
    api_base: str
    scopes: List[str]
    post_endpoint: str
    rate_limit: int  # posts per day
    optimal_times: List[int]  # hours in UTC
    content_types: List[str]
    max_caption_length: int
    requires_audit: bool = False


PLATFORM_CONFIGS: Dict[SocialPlatform, PlatformConfig] = {
    SocialPlatform.TIKTOK: PlatformConfig(
        platform=SocialPlatform.TIKTOK,
        client_id_env="TIKTOK_CLIENT_KEY",
        client_secret_env="TIKTOK_CLIENT_SECRET",
        oauth_url="https://www.tiktok.com/v2/auth/authorize/",
        token_url="https://open.tiktokapis.com/v2/oauth/token/",
        api_base="https://open.tiktokapis.com/v2",
        scopes=["user.info.basic", "video.publish", "video.upload"],
        post_endpoint="/post/publish/video/init/",
        rate_limit=15,  # ~15 posts per day per creator
        optimal_times=[9, 12, 15, 19, 21],  # Peak TikTok hours
        content_types=["video", "photo"],
        max_caption_length=2200,
        requires_audit=True
    ),
    
    SocialPlatform.INSTAGRAM: PlatformConfig(
        platform=SocialPlatform.INSTAGRAM,
        client_id_env="INSTAGRAM_APP_ID",
        client_secret_env="INSTAGRAM_APP_SECRET",
        oauth_url="https://api.instagram.com/oauth/authorize",
        token_url="https://api.instagram.com/oauth/access_token",
        api_base="https://graph.facebook.com/v21.0",
        scopes=["instagram_basic", "instagram_content_publish", "pages_read_engagement"],
        post_endpoint="/{ig_user_id}/media",
        rate_limit=25,  # Instagram allows ~25 posts per day
        optimal_times=[8, 11, 14, 17, 20],
        content_types=["image", "video", "carousel", "reel", "story"],
        max_caption_length=2200,
        requires_audit=False
    ),
    
    SocialPlatform.YOUTUBE: PlatformConfig(
        platform=SocialPlatform.YOUTUBE,
        client_id_env="YOUTUBE_CLIENT_ID",
        client_secret_env="YOUTUBE_CLIENT_SECRET",
        oauth_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        api_base="https://www.googleapis.com/youtube/v3",
        scopes=["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"],
        post_endpoint="/videos",
        rate_limit=50,  # YouTube is generous
        optimal_times=[10, 14, 16, 20],
        content_types=["video", "short"],
        max_caption_length=5000,
        requires_audit=False
    ),
    
    SocialPlatform.TWITTER: PlatformConfig(
        platform=SocialPlatform.TWITTER,
        client_id_env="TWITTER_CLIENT_ID",
        client_secret_env="TWITTER_CLIENT_SECRET",
        oauth_url="https://twitter.com/i/oauth2/authorize",
        token_url="https://api.twitter.com/2/oauth2/token",
        api_base="https://api.twitter.com/2",
        scopes=["tweet.read", "tweet.write", "users.read", "offline.access"],
        post_endpoint="/tweets",
        rate_limit=100,  # Twitter allows many tweets
        optimal_times=[9, 12, 15, 18, 21],
        content_types=["text", "image", "video", "thread"],
        max_caption_length=280,
        requires_audit=False
    ),
    
    SocialPlatform.LINKEDIN: PlatformConfig(
        platform=SocialPlatform.LINKEDIN,
        client_id_env="LINKEDIN_CLIENT_ID",
        client_secret_env="LINKEDIN_CLIENT_SECRET",
        oauth_url="https://www.linkedin.com/oauth/v2/authorization",
        token_url="https://www.linkedin.com/oauth/v2/accessToken",
        api_base="https://api.linkedin.com/v2",
        scopes=["r_liteprofile", "w_member_social"],
        post_endpoint="/ugcPosts",
        rate_limit=20,
        optimal_times=[7, 10, 12, 17],  # Business hours
        content_types=["text", "image", "video", "article"],
        max_caption_length=3000,
        requires_audit=False
    )
}


# ============================================================
# OAUTH TOKEN MANAGEMENT
# ============================================================

@dataclass
class SocialToken:
    """Stored OAuth token for a user's connected platform"""
    user_id: str
    platform: SocialPlatform
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[str] = None
    platform_user_id: Optional[str] = None
    platform_username: Optional[str] = None
    scopes: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_used: Optional[str] = None


class OAuthManager:
    """
    Manages OAuth flows and token storage for social platforms
    """
    
    def __init__(self):
        # In production, tokens would be stored encrypted in database
        self._tokens: Dict[str, Dict[str, SocialToken]] = {}  # user_id -> platform -> token
    
    def get_oauth_url(
        self,
        platform: SocialPlatform,
        user_id: str,
        redirect_uri: str
    ) -> str:
        """Generate OAuth authorization URL for a platform"""
        
        config = PLATFORM_CONFIGS.get(platform)
        if not config:
            raise ValueError(f"Unknown platform: {platform}")
        
        client_id = os.getenv(config.client_id_env)
        if not client_id:
            raise ValueError(f"Missing {config.client_id_env} environment variable")
        
        # Generate state for CSRF protection
        state = hashlib.sha256(f"{user_id}:{platform}:{datetime.now().timestamp()}".encode()).hexdigest()[:32]
        
        params = {
            "client_key" if platform == SocialPlatform.TIKTOK else "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": ",".join(config.scopes) if platform == SocialPlatform.TIKTOK else " ".join(config.scopes),
            "response_type": "code",
            "state": state
        }
        
        return f"{config.oauth_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(
        self,
        platform: SocialPlatform,
        code: str,
        redirect_uri: str,
        user_id: str
    ) -> SocialToken:
        """Exchange OAuth code for access token"""
        
        config = PLATFORM_CONFIGS.get(platform)
        if not config:
            raise ValueError(f"Unknown platform: {platform}")
        
        client_id = os.getenv(config.client_id_env)
        client_secret = os.getenv(config.client_secret_env)
        
        if not client_id or not client_secret:
            raise ValueError(f"Missing OAuth credentials for {platform}")
        
        async with httpx.AsyncClient() as client:
            if platform == SocialPlatform.TIKTOK:
                response = await client.post(
                    config.token_url,
                    data={
                        "client_key": client_id,
                        "client_secret": client_secret,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": redirect_uri
                    }
                )
            else:
                response = await client.post(
                    config.token_url,
                    data={
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "code": code,
                        "grant_type": "authorization_code",
                        "redirect_uri": redirect_uri
                    }
                )
            
            if response.status_code != 200:
                raise Exception(f"Token exchange failed: {response.text}")
            
            data = response.json()
            
            # Handle platform-specific response formats
            if platform == SocialPlatform.TIKTOK:
                token_data = data.get("data", data)
            else:
                token_data = data
            
            token = SocialToken(
                user_id=user_id,
                platform=platform,
                access_token=token_data.get("access_token"),
                refresh_token=token_data.get("refresh_token"),
                expires_at=(datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))).isoformat(),
                platform_user_id=token_data.get("open_id") or token_data.get("user_id"),
                scopes=config.scopes
            )
            
            # Store token
            self._store_token(token)
            
            return token
    
    def _store_token(self, token: SocialToken):
        """Store token (in production, encrypt and save to DB)"""
        if token.user_id not in self._tokens:
            self._tokens[token.user_id] = {}
        self._tokens[token.user_id][token.platform.value] = token
    
    def get_token(self, user_id: str, platform: SocialPlatform) -> Optional[SocialToken]:
        """Retrieve stored token"""
        return self._tokens.get(user_id, {}).get(platform.value)
    
    def get_connected_platforms(self, user_id: str) -> List[SocialPlatform]:
        """Get list of platforms user has connected"""
        return [SocialPlatform(p) for p in self._tokens.get(user_id, {}).keys()]
    
    async def refresh_token_if_needed(self, token: SocialToken) -> SocialToken:
        """Refresh token if expired or about to expire"""
        
        if not token.expires_at or not token.refresh_token:
            return token
        
        expires = datetime.fromisoformat(token.expires_at.replace('Z', '+00:00'))
        if expires > datetime.now(timezone.utc) + timedelta(minutes=5):
            return token  # Still valid
        
        # Need to refresh
        config = PLATFORM_CONFIGS.get(token.platform)
        client_id = os.getenv(config.client_id_env)
        client_secret = os.getenv(config.client_secret_env)
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config.token_url,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": token.refresh_token,
                    "grant_type": "refresh_token"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                token.access_token = data.get("access_token", token.access_token)
                token.refresh_token = data.get("refresh_token", token.refresh_token)
                token.expires_at = (datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600))).isoformat()
                self._store_token(token)
        
        return token


# ============================================================
# CONTENT GENERATION
# ============================================================

@dataclass
class SocialContent:
    """Content to be posted to social platforms"""
    content_id: str
    content_type: str  # video, image, text, carousel
    caption: str
    hashtags: List[str]
    media_urls: List[str]  # URLs to media files
    media_paths: List[str] = field(default_factory=list)  # Local paths
    platforms: List[SocialPlatform] = field(default_factory=list)
    scheduled_time: Optional[str] = None
    status: str = "pending"  # pending, scheduled, posted, failed
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    posted_at: Optional[str] = None
    post_ids: Dict[str, str] = field(default_factory=dict)  # platform -> post_id
    performance: Dict[str, Any] = field(default_factory=dict)


class ContentGenerator:
    """
    Generates content for social platforms using AI workers
    """
    
    def __init__(self):
        # Import AI workers
        self.video_engine = None
        self.graphics_engine = None
        self.research_engine = None
        
        try:
            from video_engine import VideoEngine
            self.video_engine = VideoEngine()
        except:
            print("⚠️ video_engine not available")
        
        try:
            from graphics_engine import GraphicsEngine
            self.graphics_engine = GraphicsEngine()
        except:
            print("⚠️ graphics_engine not available")
        
        try:
            from research_engine import ResearchEngine
            self.research_engine = ResearchEngine()
        except:
            print("⚠️ research_engine not available")
    
    async def generate_content(
        self,
        content_type: str,
        topic: str,
        platform: SocialPlatform,
        style: str = "engaging",
        user_preferences: Dict = None
    ) -> SocialContent:
        """
        Generate content for a specific platform
        
        Args:
            content_type: video, image, text, carousel
            topic: What the content should be about
            platform: Target platform
            style: engaging, educational, promotional, etc.
            user_preferences: User's brand voice, colors, etc.
        """
        
        content_id = f"content_{hashlib.md5(f'{topic}{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"
        
        config = PLATFORM_CONFIGS.get(platform)
        user_preferences = user_preferences or {}
        
        # Generate caption with hashtags
        caption, hashtags = await self._generate_caption(topic, platform, style, user_preferences)
        
        # Truncate caption to platform limit
        if len(caption) > config.max_caption_length - 50:  # Leave room for hashtags
            caption = caption[:config.max_caption_length - 50] + "..."
        
        # Generate media based on content type
        media_urls = []
        
        if content_type == "video" and self.video_engine:
            video_result = await self._generate_video(topic, platform, style)
            if video_result.get('url'):
                media_urls.append(video_result['url'])
        
        elif content_type == "image" and self.graphics_engine:
            image_result = await self._generate_image(topic, platform, style)
            if image_result.get('url'):
                media_urls.append(image_result['url'])
        
        return SocialContent(
            content_id=content_id,
            content_type=content_type,
            caption=caption,
            hashtags=hashtags,
            media_urls=media_urls,
            platforms=[platform],
            status="pending"
        )
    
    async def _generate_caption(
        self,
        topic: str,
        platform: SocialPlatform,
        style: str,
        preferences: Dict
    ) -> tuple:
        """Generate platform-optimized caption and hashtags"""
        
        # Platform-specific caption styles
        platform_styles = {
            SocialPlatform.TIKTOK: "casual, trendy, use emojis, hook in first line, call-to-action",
            SocialPlatform.INSTAGRAM: "aesthetic, storytelling, use line breaks, mix of emojis",
            SocialPlatform.YOUTUBE: "SEO-optimized, descriptive, include timestamps if video",
            SocialPlatform.TWITTER: "concise, witty, conversation-starting",
            SocialPlatform.LINKEDIN: "professional, insightful, thought-leadership"
        }
        
        platform_style = platform_styles.get(platform, "engaging")
        
        # In production, this would use Claude/GPT to generate
        # For now, template-based
        
        hook_templates = {
            SocialPlatform.TIKTOK: [
                f"Wait for it... 🔥 {topic}",
                f"POV: You just discovered {topic} 😱",
                f"This changed everything about {topic}",
            ],
            SocialPlatform.INSTAGRAM: [
                f"✨ {topic} ✨\n\nHere's what you need to know...",
                f"Saving this for later? You should. {topic} explained 👇",
            ],
            SocialPlatform.YOUTUBE: [
                f"{topic} - Complete Guide | Everything You Need to Know",
                f"How to Master {topic} in 2025 (Step-by-Step)",
            ],
            SocialPlatform.TWITTER: [
                f"Hot take: {topic} is about to change everything.\n\nHere's why 🧵",
                f"{topic} - a thread 👇",
            ],
            SocialPlatform.LINKEDIN: [
                f"I've been thinking about {topic} a lot lately.\n\nHere's what I've learned:",
                f"The future of {topic} is here. Are you ready?",
            ]
        }
        
        templates = hook_templates.get(platform, [f"Check this out: {topic}"])
        caption = templates[0]  # In production, randomly select or AI generate
        
        # Generate hashtags
        hashtags = self._generate_hashtags(topic, platform)
        
        # Add hashtags to caption (platform-specific formatting)
        if platform in [SocialPlatform.INSTAGRAM, SocialPlatform.TIKTOK]:
            hashtag_str = " ".join([f"#{h}" for h in hashtags[:10]])
            caption = f"{caption}\n\n{hashtag_str}"
        
        return caption, hashtags
    
    def _generate_hashtags(self, topic: str, platform: SocialPlatform) -> List[str]:
        """Generate relevant hashtags for the topic"""
        
        # Base hashtags by platform
        platform_base = {
            SocialPlatform.TIKTOK: ["fyp", "foryou", "viral", "trending"],
            SocialPlatform.INSTAGRAM: ["instagood", "photooftheday", "explore"],
            SocialPlatform.YOUTUBE: [],  # YouTube uses tags differently
            SocialPlatform.TWITTER: [],
            SocialPlatform.LINKEDIN: ["business", "entrepreneurship", "innovation"]
        }
        
        base = platform_base.get(platform, [])
        
        # Topic-based hashtags (simplified - would use AI in production)
        topic_words = topic.lower().replace("-", " ").replace("_", " ").split()
        topic_hashtags = [w for w in topic_words if len(w) > 3][:5]
        
        return base + topic_hashtags
    
    async def _generate_video(self, topic: str, platform: SocialPlatform, style: str) -> Dict:
        """Generate video using video engine"""
        
        if not self.video_engine:
            return {"url": None, "error": "Video engine not available"}
        
        try:
            # Platform-specific video specs
            specs = {
                SocialPlatform.TIKTOK: {"aspect_ratio": "9:16", "max_duration": 180},
                SocialPlatform.INSTAGRAM: {"aspect_ratio": "9:16", "max_duration": 90},
                SocialPlatform.YOUTUBE: {"aspect_ratio": "16:9", "max_duration": 600},
            }
            
            spec = specs.get(platform, {"aspect_ratio": "16:9", "max_duration": 60})
            
            result = await self.video_engine.generate_video({
                "topic": topic,
                "style": style,
                "aspect_ratio": spec["aspect_ratio"],
                "max_duration": spec["max_duration"]
            })
            
            return result
        except Exception as e:
            return {"url": None, "error": str(e)}
    
    async def _generate_image(self, topic: str, platform: SocialPlatform, style: str) -> Dict:
        """Generate image using graphics engine"""
        
        if not self.graphics_engine:
            return {"url": None, "error": "Graphics engine not available"}
        
        try:
            # Platform-specific image specs
            specs = {
                SocialPlatform.INSTAGRAM: {"size": "1080x1080", "style": "aesthetic"},
                SocialPlatform.TWITTER: {"size": "1200x675", "style": "bold"},
                SocialPlatform.LINKEDIN: {"size": "1200x627", "style": "professional"},
                SocialPlatform.PINTEREST: {"size": "1000x1500", "style": "eye-catching"},
            }
            
            spec = specs.get(platform, {"size": "1080x1080", "style": "modern"})
            
            result = await self.graphics_engine.generate_image({
                "prompt": f"{topic}, {spec['style']} style, social media optimized",
                "size": spec["size"]
            })
            
            return result
        except Exception as e:
            return {"url": None, "error": str(e)}


# ============================================================
# PLATFORM POSTING
# ============================================================

class SocialPoster:
    """
    Posts content to social platforms using their APIs
    """
    
    def __init__(self, oauth_manager: OAuthManager):
        self.oauth = oauth_manager
    
    async def post_content(
        self,
        content: SocialContent,
        user_id: str,
        platform: SocialPlatform
    ) -> Dict[str, Any]:
        """Post content to a specific platform"""
        
        token = self.oauth.get_token(user_id, platform)
        if not token:
            return {"success": False, "error": f"No {platform.value} account connected"}
        
        # Refresh token if needed
        token = await self.oauth.refresh_token_if_needed(token)
        
        # Route to platform-specific poster
        if platform == SocialPlatform.TIKTOK:
            return await self._post_to_tiktok(content, token)
        elif platform == SocialPlatform.INSTAGRAM:
            return await self._post_to_instagram(content, token)
        elif platform == SocialPlatform.YOUTUBE:
            return await self._post_to_youtube(content, token)
        elif platform == SocialPlatform.TWITTER:
            return await self._post_to_twitter(content, token)
        elif platform == SocialPlatform.LINKEDIN:
            return await self._post_to_linkedin(content, token)
        else:
            return {"success": False, "error": f"Platform {platform.value} not yet supported"}
    
    async def _post_to_tiktok(self, content: SocialContent, token: SocialToken) -> Dict:
        """Post to TikTok using Content Posting API"""
        
        config = PLATFORM_CONFIGS[SocialPlatform.TIKTOK]
        
        async with httpx.AsyncClient() as client:
            # Step 1: Initialize upload
            if content.content_type == "video":
                init_response = await client.post(
                    f"{config.api_base}/post/publish/inbox/video/init/",
                    headers={
                        "Authorization": f"Bearer {token.access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "source_info": {
                            "source": "PULL_FROM_URL",
                            "video_url": content.media_urls[0] if content.media_urls else None
                        }
                    }
                )
                
                if init_response.status_code != 200:
                    return {"success": False, "error": init_response.text, "platform": "tiktok"}
                
                data = init_response.json()
                publish_id = data.get("data", {}).get("publish_id")
                
                return {
                    "success": True,
                    "platform": "tiktok",
                    "publish_id": publish_id,
                    "status": "processing",
                    "note": "TikTok videos require processing time"
                }
            
            elif content.content_type == "photo":
                init_response = await client.post(
                    f"{config.api_base}/post/publish/content/init/",
                    headers={
                        "Authorization": f"Bearer {token.access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "post_info": {
                            "title": content.caption[:150],
                            "description": content.caption
                        },
                        "source_info": {
                            "source": "PULL_FROM_URL",
                            "photo_images": content.media_urls
                        },
                        "post_mode": "DIRECT_POST",
                        "media_type": "PHOTO"
                    }
                )
                
                if init_response.status_code != 200:
                    return {"success": False, "error": init_response.text, "platform": "tiktok"}
                
                data = init_response.json()
                return {
                    "success": True,
                    "platform": "tiktok",
                    "publish_id": data.get("data", {}).get("publish_id"),
                    "status": "posted"
                }
        
        return {"success": False, "error": "Unknown content type", "platform": "tiktok"}
    
    async def _post_to_instagram(self, content: SocialContent, token: SocialToken) -> Dict:
        """Post to Instagram using Graph API"""
        
        config = PLATFORM_CONFIGS[SocialPlatform.INSTAGRAM]
        ig_user_id = token.platform_user_id
        
        async with httpx.AsyncClient() as client:
            # Step 1: Create media container
            container_params = {
                "caption": content.caption,
                "access_token": token.access_token
            }
            
            if content.content_type == "video":
                container_params["media_type"] = "REELS"
                container_params["video_url"] = content.media_urls[0] if content.media_urls else None
            else:
                container_params["image_url"] = content.media_urls[0] if content.media_urls else None
            
            container_response = await client.post(
                f"{config.api_base}/{ig_user_id}/media",
                data=container_params
            )
            
            if container_response.status_code != 200:
                return {"success": False, "error": container_response.text, "platform": "instagram"}
            
            container_id = container_response.json().get("id")
            
            # Step 2: Publish the container
            publish_response = await client.post(
                f"{config.api_base}/{ig_user_id}/media_publish",
                data={
                    "creation_id": container_id,
                    "access_token": token.access_token
                }
            )
            
            if publish_response.status_code != 200:
                return {"success": False, "error": publish_response.text, "platform": "instagram"}
            
            post_id = publish_response.json().get("id")
            
            return {
                "success": True,
                "platform": "instagram",
                "post_id": post_id,
                "status": "posted"
            }
    
    async def _post_to_youtube(self, content: SocialContent, token: SocialToken) -> Dict:
        """Post to YouTube using Data API v3"""
        
        config = PLATFORM_CONFIGS[SocialPlatform.YOUTUBE]
        
        async with httpx.AsyncClient() as client:
            # YouTube requires uploading video file, more complex flow
            # For now, return placeholder
            return {
                "success": False,
                "platform": "youtube",
                "error": "YouTube upload requires video file upload - use resumable upload",
                "docs": "https://developers.google.com/youtube/v3/guides/uploading_a_video"
            }
    
    async def _post_to_twitter(self, content: SocialContent, token: SocialToken) -> Dict:
        """Post to Twitter using API v2"""
        
        config = PLATFORM_CONFIGS[SocialPlatform.TWITTER]
        
        async with httpx.AsyncClient() as client:
            # Text-only tweet
            tweet_data = {"text": content.caption[:280]}
            
            response = await client.post(
                f"{config.api_base}/tweets",
                headers={
                    "Authorization": f"Bearer {token.access_token}",
                    "Content-Type": "application/json"
                },
                json=tweet_data
            )
            
            if response.status_code not in [200, 201]:
                return {"success": False, "error": response.text, "platform": "twitter"}
            
            data = response.json()
            
            return {
                "success": True,
                "platform": "twitter",
                "tweet_id": data.get("data", {}).get("id"),
                "status": "posted"
            }
    
    async def _post_to_linkedin(self, content: SocialContent, token: SocialToken) -> Dict:
        """Post to LinkedIn using Marketing API"""
        
        config = PLATFORM_CONFIGS[SocialPlatform.LINKEDIN]
        
        async with httpx.AsyncClient() as client:
            # Get user URN
            profile_response = await client.get(
                f"{config.api_base}/me",
                headers={"Authorization": f"Bearer {token.access_token}"}
            )
            
            if profile_response.status_code != 200:
                return {"success": False, "error": "Failed to get LinkedIn profile", "platform": "linkedin"}
            
            user_urn = f"urn:li:person:{profile_response.json().get('id')}"
            
            # Create post
            post_data = {
                "author": user_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content.caption},
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            response = await client.post(
                f"{config.api_base}/ugcPosts",
                headers={
                    "Authorization": f"Bearer {token.access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0"
                },
                json=post_data
            )
            
            if response.status_code not in [200, 201]:
                return {"success": False, "error": response.text, "platform": "linkedin"}
            
            return {
                "success": True,
                "platform": "linkedin",
                "post_id": response.headers.get("x-restli-id"),
                "status": "posted"
            }


# ============================================================
# APPROVAL MODES
# ============================================================

class ApprovalMode(str, Enum):
    """How much control the user wants over posts"""
    
    MANUAL = "manual"           # User approves every post before it goes live
    REVIEW_FIRST = "review_first"  # AI generates, user reviews queue, batch approves
    AUTO_WITH_NOTIFY = "auto_with_notify"  # Auto-posts but notifies user
    FULL_AUTO = "full_auto"     # Complete autopilot (user opted in explicitly)


@dataclass
class UserPostingPreferences:
    """User's preferences for auto-posting"""
    user_id: str
    approval_mode: ApprovalMode = ApprovalMode.MANUAL
    platforms_enabled: List[SocialPlatform] = field(default_factory=list)
    max_posts_per_day: int = 3
    posting_hours: List[int] = field(default_factory=lambda: [9, 12, 17])  # When they want posts
    content_guidelines: str = ""  # Brand voice, topics to avoid, etc.
    require_hashtag_approval: bool = True
    auto_respond_to_comments: bool = False
    notify_on_post: bool = True
    notify_on_engagement: bool = True
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass 
class PendingApproval:
    """Content awaiting user approval"""
    approval_id: str
    user_id: str
    platform: SocialPlatform
    content: 'SocialContent'
    generated_at: str
    status: str = "pending"  # pending, approved, rejected, edited, expired
    user_feedback: Optional[str] = None
    edited_caption: Optional[str] = None
    approved_at: Optional[str] = None
    expires_at: Optional[str] = None


class ApprovalManager:
    """
    Manages the approval workflow for social posts
    
    Modes:
    - MANUAL: Every post requires explicit approval
    - REVIEW_FIRST: Posts queue up, user batch reviews
    - AUTO_WITH_NOTIFY: Posts go live, user gets notified
    - FULL_AUTO: Complete autopilot (requires explicit opt-in)
    """
    
    def __init__(self):
        self._preferences: Dict[str, UserPostingPreferences] = {}
        self._pending_approvals: Dict[str, PendingApproval] = {}
        self._approval_history: List[Dict] = []
    
    def set_user_preferences(
        self,
        user_id: str,
        approval_mode: str = "manual",
        platforms: List[str] = None,
        max_posts_per_day: int = 3,
        content_guidelines: str = ""
    ) -> UserPostingPreferences:
        """Set user's posting preferences"""
        
        prefs = UserPostingPreferences(
            user_id=user_id,
            approval_mode=ApprovalMode(approval_mode),
            platforms_enabled=[SocialPlatform(p) for p in (platforms or [])],
            max_posts_per_day=max_posts_per_day,
            content_guidelines=content_guidelines
        )
        
        self._preferences[user_id] = prefs
        return prefs
    
    def get_user_preferences(self, user_id: str) -> Optional[UserPostingPreferences]:
        """Get user's posting preferences"""
        return self._preferences.get(user_id)
    
    def get_approval_mode(self, user_id: str) -> ApprovalMode:
        """Get user's approval mode (defaults to MANUAL)"""
        prefs = self._preferences.get(user_id)
        return prefs.approval_mode if prefs else ApprovalMode.MANUAL
    
    def queue_for_approval(
        self,
        user_id: str,
        platform: SocialPlatform,
        content: 'SocialContent'
    ) -> PendingApproval:
        """Queue content for user approval"""
        
        approval_id = f"approval_{hashlib.md5(f'{user_id}{content.content_id}'.encode()).hexdigest()[:12]}"
        
        pending = PendingApproval(
            approval_id=approval_id,
            user_id=user_id,
            platform=platform,
            content=content,
            generated_at=datetime.now(timezone.utc).isoformat(),
            expires_at=(datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        )
        
        self._pending_approvals[approval_id] = pending
        return pending
    
    def get_pending_approvals(self, user_id: str) -> List[PendingApproval]:
        """Get all pending approvals for a user"""
        return [
            p for p in self._pending_approvals.values()
            if p.user_id == user_id and p.status == "pending"
        ]
    
    def approve(
        self,
        approval_id: str,
        edited_caption: str = None
    ) -> Dict[str, Any]:
        """Approve a pending post"""
        
        pending = self._pending_approvals.get(approval_id)
        if not pending:
            return {"success": False, "error": "Approval not found"}
        
        pending.status = "approved"
        pending.approved_at = datetime.now(timezone.utc).isoformat()
        
        if edited_caption:
            pending.edited_caption = edited_caption
            pending.content.caption = edited_caption
        
        self._approval_history.append({
            "approval_id": approval_id,
            "action": "approved",
            "timestamp": pending.approved_at
        })
        
        return {"success": True, "approval_id": approval_id, "status": "approved"}
    
    def reject(
        self,
        approval_id: str,
        feedback: str = None
    ) -> Dict[str, Any]:
        """Reject a pending post"""
        
        pending = self._pending_approvals.get(approval_id)
        if not pending:
            return {"success": False, "error": "Approval not found"}
        
        pending.status = "rejected"
        pending.user_feedback = feedback
        
        self._approval_history.append({
            "approval_id": approval_id,
            "action": "rejected",
            "feedback": feedback,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {"success": True, "approval_id": approval_id, "status": "rejected"}
    
    def bulk_approve(self, approval_ids: List[str]) -> Dict[str, Any]:
        """Approve multiple posts at once"""
        results = []
        for aid in approval_ids:
            result = self.approve(aid)
            results.append(result)
        
        return {
            "success": True,
            "approved": len([r for r in results if r.get("success")]),
            "failed": len([r for r in results if not r.get("success")])
        }
    
    def get_approved_ready_to_post(self, user_id: str) -> List[PendingApproval]:
        """Get approved content ready to post"""
        return [
            p for p in self._pending_approvals.values()
            if p.user_id == user_id and p.status == "approved"
        ]


# ============================================================
# SCHEDULING & QUEUE
# ============================================================

class PostingQueue:
    """
    Manages scheduled posts across platforms
    """
    
    def __init__(self):
        self.queue: List[Dict[str, Any]] = []
        self.posted: List[Dict[str, Any]] = []
    
    def schedule_post(
        self,
        content: SocialContent,
        user_id: str,
        platform: SocialPlatform,
        scheduled_time: datetime = None
    ) -> Dict[str, Any]:
        """Schedule a post for later"""
        
        if not scheduled_time:
            # Auto-schedule to next optimal time
            config = PLATFORM_CONFIGS.get(platform)
            scheduled_time = self._get_next_optimal_time(config.optimal_times)
        
        scheduled_item = {
            "id": f"sched_{hashlib.md5(f'{content.content_id}{scheduled_time.isoformat()}'.encode()).hexdigest()[:8]}",
            "content": content,
            "user_id": user_id,
            "platform": platform,
            "scheduled_time": scheduled_time.isoformat(),
            "status": "scheduled",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        self.queue.append(scheduled_item)
        
        return scheduled_item
    
    def _get_next_optimal_time(self, optimal_hours: List[int]) -> datetime:
        """Find next optimal posting time"""
        
        now = datetime.now(timezone.utc)
        current_hour = now.hour
        
        # Find next optimal hour
        for hour in sorted(optimal_hours):
            if hour > current_hour:
                return now.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        # No optimal time today, schedule for tomorrow
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=optimal_hours[0], minute=0, second=0, microsecond=0)
    
    def get_pending_posts(self) -> List[Dict]:
        """Get posts ready to be published"""
        
        now = datetime.now(timezone.utc)
        pending = []
        
        for item in self.queue:
            if item["status"] == "scheduled":
                scheduled = datetime.fromisoformat(item["scheduled_time"].replace('Z', '+00:00'))
                if scheduled <= now:
                    pending.append(item)
        
        return pending
    
    def mark_posted(self, schedule_id: str, result: Dict):
        """Mark a scheduled post as completed"""
        
        for item in self.queue:
            if item["id"] == schedule_id:
                item["status"] = "posted" if result.get("success") else "failed"
                item["result"] = result
                item["posted_at"] = datetime.now(timezone.utc).isoformat()
                self.posted.append(item)
                break


# ============================================================
# MAIN ENGINE
# ============================================================

class SocialAutoPostingEngine:
    """
    Main orchestrator for social auto-posting
    
    Combines:
    - OAuth management
    - Content generation
    - Approval workflow (user controls how much autonomy)
    - Platform posting
    - Scheduling
    - Performance tracking
    """
    
    def __init__(self):
        self.oauth = OAuthManager()
        self.content_generator = ContentGenerator()
        self.poster = SocialPoster(self.oauth)
        self.queue = PostingQueue()
        self.approvals = ApprovalManager()
        
        # Try to import Yield Memory for learning
        try:
            from yield_memory import store_pattern, find_similar_patterns
            self.yield_memory = True
            self.store_pattern = store_pattern
            self.find_patterns = find_similar_patterns
        except:
            self.yield_memory = False
    
    def get_oauth_url(self, platform: str, user_id: str, redirect_uri: str) -> str:
        """Get OAuth URL for connecting a platform"""
        platform_enum = SocialPlatform(platform)
        return self.oauth.get_oauth_url(platform_enum, user_id, redirect_uri)
    
    async def handle_oauth_callback(
        self,
        platform: str,
        code: str,
        user_id: str,
        redirect_uri: str
    ) -> Dict[str, Any]:
        """Handle OAuth callback after user authorizes"""
        
        platform_enum = SocialPlatform(platform)
        token = await self.oauth.exchange_code_for_token(platform_enum, code, redirect_uri, user_id)
        
        return {
            "success": True,
            "platform": platform,
            "connected": True,
            "platform_user_id": token.platform_user_id
        }
    
    def get_connected_platforms(self, user_id: str) -> List[str]:
        """Get list of platforms user has connected"""
        return [p.value for p in self.oauth.get_connected_platforms(user_id)]
    
    def set_user_preferences(
        self,
        user_id: str,
        approval_mode: str = "manual",
        platforms: List[str] = None,
        max_posts_per_day: int = 3,
        content_guidelines: str = ""
    ) -> Dict[str, Any]:
        """Set user's posting preferences and approval mode"""
        
        prefs = self.approvals.set_user_preferences(
            user_id=user_id,
            approval_mode=approval_mode,
            platforms=platforms,
            max_posts_per_day=max_posts_per_day,
            content_guidelines=content_guidelines
        )
        
        return {
            "user_id": user_id,
            "approval_mode": prefs.approval_mode.value,
            "platforms_enabled": [p.value for p in prefs.platforms_enabled],
            "max_posts_per_day": prefs.max_posts_per_day
        }
    
    async def create_and_post(
        self,
        user_id: str,
        platform: str,
        content_type: str,
        topic: str,
        style: str = "engaging",
        schedule: bool = False,
        scheduled_time: datetime = None,
        bypass_approval: bool = False
    ) -> Dict[str, Any]:
        """
        Create content and handle based on user's approval mode
        
        Approval Modes:
        - MANUAL: Queue for approval, don't post until approved
        - REVIEW_FIRST: Queue for review, user can batch approve
        - AUTO_WITH_NOTIFY: Post immediately, notify user
        - FULL_AUTO: Post immediately, no notification
        
        bypass_approval: If True, post immediately regardless of mode (for testing)
        """
        
        platform_enum = SocialPlatform(platform)
        approval_mode = self.approvals.get_approval_mode(user_id)
        
        # Generate content
        content = await self.content_generator.generate_content(
            content_type=content_type,
            topic=topic,
            platform=platform_enum,
            style=style
        )
        
        # Check approval mode
        if not bypass_approval and approval_mode in [ApprovalMode.MANUAL, ApprovalMode.REVIEW_FIRST]:
            # Queue for approval instead of posting
            pending = self.approvals.queue_for_approval(
                user_id=user_id,
                platform=platform_enum,
                content=content
            )
            
            return {
                "success": True,
                "action": "queued_for_approval",
                "approval_id": pending.approval_id,
                "approval_mode": approval_mode.value,
                "message": "Content generated and queued for your approval",
                "content_preview": {
                    "caption": content.caption[:200] + "..." if len(content.caption) > 200 else content.caption,
                    "type": content.content_type,
                    "hashtags": content.hashtags,
                    "platform": platform
                },
                "actions": {
                    "approve": f"/social/approve/{pending.approval_id}",
                    "reject": f"/social/reject/{pending.approval_id}",
                    "edit": f"/social/edit/{pending.approval_id}"
                }
            }
        
        # Auto-post modes (AUTO_WITH_NOTIFY or FULL_AUTO) or bypass
        if schedule:
            # Schedule for later
            scheduled = self.queue.schedule_post(
                content=content,
                user_id=user_id,
                platform=platform_enum,
                scheduled_time=scheduled_time
            )
            return {
                "success": True,
                "action": "scheduled",
                "scheduled_id": scheduled["id"],
                "scheduled_time": scheduled["scheduled_time"],
                "content": {
                    "caption": content.caption[:200] + "...",
                    "type": content.content_type,
                    "hashtags": content.hashtags
                }
            }
        else:
            # Post immediately
            result = await self.poster.post_content(content, user_id, platform_enum)
            
            # Notify if AUTO_WITH_NOTIFY
            if approval_mode == ApprovalMode.AUTO_WITH_NOTIFY:
                # In production, send push notification / email
                result["notification_sent"] = True
                result["message"] = "Posted to your account. Check your notifications."
            
            # Store pattern in Yield Memory if successful
            if result.get("success") and self.yield_memory:
                try:
                    await self.store_pattern({
                        "type": "social_post_success",
                        "platform": platform,
                        "content_type": content_type,
                        "topic": topic,
                        "style": style,
                        "hashtags": content.hashtags
                    })
                except:
                    pass
            
            return {
                "success": result.get("success"),
                "action": "posted",
                "result": result,
                "content": {
                    "caption": content.caption[:200] + "...",
                    "type": content.content_type,
                    "hashtags": content.hashtags
                }
            }
    
    def get_pending_approvals(self, user_id: str) -> List[Dict]:
        """Get all posts pending user approval"""
        pending = self.approvals.get_pending_approvals(user_id)
        return [
            {
                "approval_id": p.approval_id,
                "platform": p.platform.value,
                "content_type": p.content.content_type,
                "caption_preview": p.content.caption[:200] + "..." if len(p.content.caption) > 200 else p.content.caption,
                "full_caption": p.content.caption,
                "hashtags": p.content.hashtags,
                "generated_at": p.generated_at,
                "expires_at": p.expires_at
            }
            for p in pending
        ]
    
    async def approve_and_post(
        self,
        approval_id: str,
        edited_caption: str = None
    ) -> Dict[str, Any]:
        """Approve a pending post and publish it"""
        
        # Approve
        result = self.approvals.approve(approval_id, edited_caption)
        if not result.get("success"):
            return result
        
        # Get the approved content
        pending = self.approvals._pending_approvals.get(approval_id)
        if not pending:
            return {"success": False, "error": "Approval not found after approving"}
        
        # Post it
        post_result = await self.poster.post_content(
            pending.content,
            pending.user_id,
            pending.platform
        )
        
        return {
            "success": post_result.get("success"),
            "action": "approved_and_posted",
            "approval_id": approval_id,
            "post_result": post_result
        }
    
    def reject_post(
        self,
        approval_id: str,
        feedback: str = None
    ) -> Dict[str, Any]:
        """Reject a pending post"""
        return self.approvals.reject(approval_id, feedback)
    
    async def bulk_approve_and_post(
        self,
        approval_ids: List[str]
    ) -> Dict[str, Any]:
        """Approve and post multiple items at once"""
        results = []
        for aid in approval_ids:
            result = await self.approve_and_post(aid)
            results.append({"approval_id": aid, **result})
        
        return {
            "success": True,
            "processed": len(results),
            "posted": len([r for r in results if r.get("success")]),
            "failed": len([r for r in results if not r.get("success")]),
            "results": results
        }
    
    async def process_scheduled_posts(self) -> List[Dict]:
        """Process all pending scheduled posts"""
        
        pending = self.queue.get_pending_posts()
        results = []
        
        for item in pending:
            result = await self.poster.post_content(
                item["content"],
                item["user_id"],
                item["platform"]
            )
            
            self.queue.mark_posted(item["id"], result)
            results.append({
                "schedule_id": item["id"],
                "platform": item["platform"].value,
                "result": result
            })
        
        return results
    
    async def get_optimal_posting_strategy(
        self,
        user_id: str,
        platforms: List[str]
    ) -> Dict[str, Any]:
        """Get AI-recommended posting strategy based on past performance"""
        
        strategy = {
            "user_id": user_id,
            "recommendations": []
        }
        
        for platform in platforms:
            config = PLATFORM_CONFIGS.get(SocialPlatform(platform))
            if config:
                strategy["recommendations"].append({
                    "platform": platform,
                    "optimal_times": config.optimal_times,
                    "recommended_frequency": f"{config.rate_limit // 3} posts/day",
                    "best_content_types": config.content_types[:2],
                    "max_caption_length": config.max_caption_length
                })
        
        return strategy


# ============================================================
# SINGLETON & CONVENIENCE
# ============================================================

_engine = None

def get_social_engine() -> SocialAutoPostingEngine:
    """Get singleton social auto-posting engine"""
    global _engine
    if _engine is None:
        _engine = SocialAutoPostingEngine()
    return _engine


# ============================================================
# FASTAPI ENDPOINTS
# ============================================================

ENDPOINTS_FOR_MAIN_PY = '''
# ============================================================
# SOCIAL AUTO-POSTING ENDPOINTS
# Autonomous content creation and posting
# ============================================================

from social_autoposting_engine import (
    get_social_engine,
    SocialPlatform,
    PLATFORM_CONFIGS
)

@app.get("/social/platforms")
async def social_platforms():
    """List available social platforms and their configurations"""
    platforms = []
    for platform, config in PLATFORM_CONFIGS.items():
        platforms.append({
            "platform": platform.value,
            "rate_limit": config.rate_limit,
            "optimal_times": config.optimal_times,
            "content_types": config.content_types,
            "max_caption_length": config.max_caption_length,
            "requires_audit": config.requires_audit
        })
    return {"ok": True, "platforms": platforms}


@app.get("/social/oauth/{platform}")
async def social_oauth_url(platform: str, username: str):
    """Get OAuth URL to connect a social platform"""
    engine = get_social_engine()
    redirect_uri = f"{os.getenv('SELF_URL', 'https://aigentsy.com')}/social/callback/{platform}"
    
    try:
        url = engine.get_oauth_url(platform, username, redirect_uri)
        return {"ok": True, "oauth_url": url, "platform": platform}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/social/callback/{platform}")
async def social_oauth_callback(platform: str, code: str, state: str):
    """Handle OAuth callback from social platform"""
    engine = get_social_engine()
    # In production, extract user_id from state
    user_id = "extracted_from_state"
    redirect_uri = f"{os.getenv('SELF_URL', 'https://aigentsy.com')}/social/callback/{platform}"
    
    try:
        result = await engine.handle_oauth_callback(platform, code, user_id, redirect_uri)
        return {"ok": True, **result}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/social/connected/{username}")
async def social_connected(username: str):
    """Get list of connected social platforms for user"""
    engine = get_social_engine()
    platforms = engine.get_connected_platforms(username)
    return {"ok": True, "username": username, "connected_platforms": platforms}


@app.post("/social/post")
async def social_post(body: Dict = Body(...)):
    """
    Create and post content to a social platform
    
    Body: {
        username: str,
        platform: "tiktok" | "instagram" | "youtube" | "twitter" | "linkedin",
        content_type: "video" | "image" | "text",
        topic: str,
        style?: "engaging" | "educational" | "promotional",
        schedule?: bool,
        scheduled_time?: str (ISO format)
    }
    """
    engine = get_social_engine()
    
    username = body.get("username")
    platform = body.get("platform")
    content_type = body.get("content_type", "text")
    topic = body.get("topic")
    style = body.get("style", "engaging")
    schedule = body.get("schedule", False)
    scheduled_time = None
    
    if body.get("scheduled_time"):
        scheduled_time = datetime.fromisoformat(body["scheduled_time"])
    
    if not all([username, platform, topic]):
        return {"ok": False, "error": "username, platform, and topic required"}
    
    result = await engine.create_and_post(
        user_id=username,
        platform=platform,
        content_type=content_type,
        topic=topic,
        style=style,
        schedule=schedule,
        scheduled_time=scheduled_time
    )
    
    return {"ok": True, **result}


@app.post("/social/process-queue")
async def social_process_queue():
    """Process all pending scheduled posts"""
    engine = get_social_engine()
    results = await engine.process_scheduled_posts()
    return {"ok": True, "processed": len(results), "results": results}


@app.get("/social/strategy/{username}")
async def social_strategy(username: str, platforms: str = "tiktok,instagram"):
    """Get AI-recommended posting strategy"""
    engine = get_social_engine()
    platform_list = platforms.split(",")
    strategy = await engine.get_optimal_posting_strategy(username, platform_list)
    return {"ok": True, **strategy}
'''
async def post_to_twitter_direct(text: str) -> dict:
    """
    Post directly to Twitter/X using OAuth 1.0a with env var credentials.
    Uses the 4 keys: API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET
    """
    
    api_key = os.getenv("TWITTER_API_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN")
    access_secret = os.getenv("TWITTER_ACCESS_SECRET")
    
    if not all([api_key, api_secret, access_token, access_secret]):
        return {"success": False, "error": "Missing Twitter credentials in env"}
    
    # Twitter API v2 endpoint
    url = "https://api.twitter.com/2/tweets"
    
    # OAuth 1.0a signature generation
    oauth_params = {
        "oauth_consumer_key": api_key,
        "oauth_token": access_token,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_nonce": hashlib.md5(str(time.time()).encode()).hexdigest(),
        "oauth_version": "1.0"
    }
    
    # Create signature base string
    method = "POST"
    params_string = "&".join([f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}" 
                              for k, v in sorted(oauth_params.items())])
    base_string = f"{method}&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(params_string, safe='')}"
    
    # Create signing key
    signing_key = f"{urllib.parse.quote(api_secret, safe='')}&{urllib.parse.quote(access_secret, safe='')}"
    
    # Generate signature
    signature = base64.b64encode(
        hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
    ).decode()
    
    oauth_params["oauth_signature"] = signature
    
    # Build Authorization header
    auth_header = "OAuth " + ", ".join([f'{k}="{urllib.parse.quote(v, safe="")}"' 
                                         for k, v in sorted(oauth_params.items())])
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json"
                },
                json={"text": text[:280]}  # Twitter limit
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    "success": True,
                    "platform": "twitter",
                    "tweet_id": data.get("data", {}).get("id"),
                    "text": text[:280]
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code
                }
        except Exception as e:
            return {"success": False, "error": str(e)}


async def post_to_instagram_direct(caption: str, image_url: str = None) -> dict:
    """
    Post to Instagram using Graph API with env var credentials.
    Note: Instagram requires a media URL for posts (can't do text-only)
    """
    
    access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    business_id = os.getenv("INSTAGRAM_BUSINESS_ID")
    
    if not access_token or not business_id:
        return {"success": False, "error": "Missing Instagram credentials in env"}
    
    if not image_url:
        return {"success": False, "error": "Instagram requires an image_url for posts"}
    
    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Create media container
            container_response = await client.post(
                f"https://graph.facebook.com/v18.0/{business_id}/media",
                params={
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": access_token
                }
            )
            
            if container_response.status_code != 200:
                return {"success": False, "error": container_response.text}
            
            container_id = container_response.json().get("id")
            
            # Step 2: Publish the container
            publish_response = await client.post(
                f"https://graph.facebook.com/v18.0/{business_id}/media_publish",
                params={
                    "creation_id": container_id,
                    "access_token": access_token
                }
            )
            
            if publish_response.status_code == 200:
                return {
                    "success": True,
                    "platform": "instagram",
                    "post_id": publish_response.json().get("id")
                }
            else:
                return {"success": False, "error": publish_response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}


async def post_to_linkedin_direct(text: str) -> dict:
    """
    Post to LinkedIn using env var access token.
    """
    
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    
    if not access_token:
        return {"success": False, "error": "Missing LinkedIn credentials in env"}
    
    async with httpx.AsyncClient() as client:
        try:
            # Get user URN first
            profile_response = await client.get(
                "https://api.linkedin.com/v2/me",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if profile_response.status_code != 200:
                return {"success": False, "error": f"Failed to get profile: {profile_response.text}"}
            
            user_urn = f"urn:li:person:{profile_response.json().get('id')}"
            
            # Create post
            post_data = {
                "author": user_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": text},
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            response = await client.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "X-Restli-Protocol-Version": "2.0.0"
                },
                json=post_data
            )
            
            if response.status_code in [200, 201]:
                return {
                    "success": True,
                    "platform": "linkedin",
                    "post_id": response.headers.get("x-restli-id")
                }
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}


async def send_sms_direct(to: str, message: str) -> dict:
    """
    Send SMS using Twilio env var credentials.
    """
    
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    if not all([account_sid, auth_token, from_number]):
        return {"success": False, "error": "Missing Twilio credentials in env"}
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json",
                auth=(account_sid, auth_token),
                data={
                    "To": to,
                    "From": from_number,
                    "Body": message
                }
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    "success": True,
                    "platform": "twilio",
                    "message_sid": data.get("sid"),
                    "to": to
                }
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    print("=" * 70)
    print("SOCIAL AUTO-POSTING ENGINE")
    print("=" * 70)
    print("\nSupported platforms:")
    for platform, config in PLATFORM_CONFIGS.items():
        print(f"  - {platform.value}: {config.content_types}, {config.rate_limit} posts/day")
    print("\nEndpoints to add to main.py - see ENDPOINTS_FOR_MAIN_PY variable")
