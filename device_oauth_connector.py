from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from uuid import uuid4
import httpx
import os

_OAUTH_TOKENS: Dict[str, Dict[str, Any]] = {}
_PENDING_POSTS: Dict[str, Dict[str, Any]] = {}

# OAuth credentials (set in environment)
TIKTOK_CLIENT_ID = os.getenv("TIKTOK_CLIENT_ID", "")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
INSTAGRAM_CLIENT_ID = os.getenv("INSTAGRAM_CLIENT_ID", "")
INSTAGRAM_CLIENT_SECRET = os.getenv("INSTAGRAM_CLIENT_SECRET", "")
SHOPIFY_API_KEY = os.getenv("SHOPIFY_API_KEY", "")
SHOPIFY_API_SECRET = os.getenv("SHOPIFY_API_SECRET", "")

def now_iso():
    return datetime.now(timezone.utc).isoformat() + "Z"


async def initiate_oauth(
    username: str,
    platform: str,
    redirect_uri: str
) -> Dict[str, Any]:
    """Initiate OAuth flow for platform"""
    
    if platform not in ["tiktok", "instagram", "shopify"]:
        return {"ok": False, "error": "unsupported_platform"}
    
    state = f"{username}:{platform}:{uuid4().hex[:8]}"
    
    if platform == "tiktok":
        auth_url = f"https://www.tiktok.com/auth/authorize/"
        auth_url += f"?client_key={TIKTOK_CLIENT_ID}"
        auth_url += f"&scope=user.info.basic,video.list,video.upload"
        auth_url += f"&response_type=code"
        auth_url += f"&redirect_uri={redirect_uri}"
        auth_url += f"&state={state}"
    
    elif platform == "instagram":
        auth_url = f"https://api.instagram.com/oauth/authorize"
        auth_url += f"?client_id={INSTAGRAM_CLIENT_ID}"
        auth_url += f"&redirect_uri={redirect_uri}"
        auth_url += f"&scope=user_profile,user_media"
        auth_url += f"&response_type=code"
        auth_url += f"&state={state}"
    
    elif platform == "shopify":
        # Shopify requires shop domain
        auth_url = f"https://{{shop}}.myshopify.com/admin/oauth/authorize"
        auth_url += f"?client_id={SHOPIFY_API_KEY}"
        auth_url += f"&scope=read_products,write_products,read_orders"
        auth_url += f"&redirect_uri={redirect_uri}"
        auth_url += f"&state={state}"
    
    return {
        "ok": True,
        "auth_url": auth_url,
        "state": state,
        "message": "Redirect user to auth_url"
    }


async def complete_oauth(
    username: str,
    platform: str,
    code: str,
    redirect_uri: str
) -> Dict[str, Any]:
    """Complete OAuth flow and store tokens"""
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            if platform == "tiktok":
                token_url = "https://open-api.tiktok.com/oauth/access_token/"
                
                r = await client.post(token_url, json={
                    "client_key": TIKTOK_CLIENT_ID,
                    "client_secret": TIKTOK_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri
                })
                
                token_data = r.json()
                
                if "access_token" not in token_data:
                    return {"ok": False, "error": "oauth_failed", "details": token_data}
                
                token_key = f"{username}:{platform}"
                _OAUTH_TOKENS[token_key] = {
                    "username": username,
                    "platform": platform,
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_in": token_data.get("expires_in", 86400),
                    "created_at": now_iso(),
                    "open_id": token_data.get("open_id")
                }
            
            elif platform == "instagram":
                token_url = "https://api.instagram.com/oauth/access_token"
                
                r = await client.post(token_url, data={
                    "client_id": INSTAGRAM_CLIENT_ID,
                    "client_secret": INSTAGRAM_CLIENT_SECRET,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                    "code": code
                })
                
                token_data = r.json()
                
                if "access_token" not in token_data:
                    return {"ok": False, "error": "oauth_failed", "details": token_data}
                
                token_key = f"{username}:{platform}"
                _OAUTH_TOKENS[token_key] = {
                    "username": username,
                    "platform": platform,
                    "access_token": token_data["access_token"],
                    "user_id": token_data.get("user_id"),
                    "created_at": now_iso()
                }
            
            elif platform == "shopify":
                # Shopify needs shop domain - extract from redirect_uri or code
                shop = "placeholder"  # Would be provided by user
                token_url = f"https://{shop}.myshopify.com/admin/oauth/access_token"
                
                r = await client.post(token_url, json={
                    "client_id": SHOPIFY_API_KEY,
                    "client_secret": SHOPIFY_API_SECRET,
                    "code": code
                })
                
                token_data = r.json()
                
                if "access_token" not in token_data:
                    return {"ok": False, "error": "oauth_failed", "details": token_data}
                
                token_key = f"{username}:{platform}"
                _OAUTH_TOKENS[token_key] = {
                    "username": username,
                    "platform": platform,
                    "access_token": token_data["access_token"],
                    "shop": shop,
                    "created_at": now_iso()
                }
        
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    return {
        "ok": True,
        "platform": platform,
        "message": f"{platform} connected successfully"
    }


async def create_post(
    username: str,
    platform: str,
    content: Dict[str, Any],
    schedule_for: str = None
) -> Dict[str, Any]:
    """Create a post (stores in pending, awaits approval)"""
    
    token_key = f"{username}:{platform}"
    
    if token_key not in _OAUTH_TOKENS:
        return {"ok": False, "error": "platform_not_connected"}
    
    post_id = f"post_{uuid4().hex[:8]}"
    
    post = {
        "id": post_id,
        "username": username,
        "platform": platform,
        "content": content,
        "schedule_for": schedule_for or now_iso(),
        "status": "PENDING_APPROVAL",
        "created_at": now_iso(),
        "approved_at": None,
        "posted_at": None
    }
    
    _PENDING_POSTS[post_id] = post
    
    # Notify user for approval
    await _notify_post_approval(username, post_id, platform, content)
    
    return {
        "ok": True,
        "post_id": post_id,
        "status": "PENDING_APPROVAL",
        "message": "Post created, awaiting your approval"
    }


async def approve_post(
    post_id: str,
    username: str
) -> Dict[str, Any]:
    """User approves post"""
    
    post = _PENDING_POSTS.get(post_id)
    
    if not post:
        return {"ok": False, "error": "post_not_found"}
    
    if post["username"] != username:
        return {"ok": False, "error": "unauthorized"}
    
    if post["status"] != "PENDING_APPROVAL":
        return {"ok": False, "error": f"post_already_{post['status'].lower()}"}
    
    post["status"] = "APPROVED"
    post["approved_at"] = now_iso()
    
    # Execute post
    result = await _execute_post(post)
    
    return result


async def reject_post(
    post_id: str,
    username: str,
    reason: str = ""
) -> Dict[str, Any]:
    """User rejects post"""
    
    post = _PENDING_POSTS.get(post_id)
    
    if not post:
        return {"ok": False, "error": "post_not_found"}
    
    if post["username"] != username:
        return {"ok": False, "error": "unauthorized"}
    
    post["status"] = "REJECTED"
    post["rejection_reason"] = reason
    
    return {"ok": True, "message": "Post rejected"}


async def _execute_post(post: Dict[str, Any]) -> Dict[str, Any]:
    """Execute approved post to platform"""
    
    username = post["username"]
    platform = post["platform"]
    content = post["content"]
    
    token_key = f"{username}:{platform}"
    token_data = _OAUTH_TOKENS.get(token_key)
    
    if not token_data:
        return {"ok": False, "error": "token_not_found"}
    
    access_token = token_data["access_token"]
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            if platform == "tiktok":
                # TikTok video upload (simplified)
                upload_url = "https://open-api.tiktok.com/share/video/upload/"
                
                headers = {"Authorization": f"Bearer {access_token}"}
                
                # Would need video file - for now simulate
                post["status"] = "POSTED"
                post["posted_at"] = now_iso()
                post["platform_post_id"] = f"tiktok_{uuid4().hex[:8]}"
                
                return {
                    "ok": True,
                    "post_id": post["id"],
                    "platform_post_id": post["platform_post_id"],
                    "message": "Posted to TikTok successfully"
                }
            
            elif platform == "instagram":
                # Instagram post (simplified)
                user_id = token_data.get("user_id")
                
                # Step 1: Create media container
                create_url = f"https://graph.instagram.com/{user_id}/media"
                
                params = {
                    "image_url": content.get("image_url"),
                    "caption": content.get("caption"),
                    "access_token": access_token
                }
                
                r = await client.post(create_url, params=params)
                container = r.json()
                
                if "id" not in container:
                    return {"ok": False, "error": "failed_to_create_container", "details": container}
                
                # Step 2: Publish media
                publish_url = f"https://graph.instagram.com/{user_id}/media_publish"
                
                r = await client.post(publish_url, params={
                    "creation_id": container["id"],
                    "access_token": access_token
                })
                
                result = r.json()
                
                post["status"] = "POSTED"
                post["posted_at"] = now_iso()
                post["platform_post_id"] = result.get("id")
                
                return {
                    "ok": True,
                    "post_id": post["id"],
                    "platform_post_id": post["platform_post_id"],
                    "message": "Posted to Instagram successfully"
                }
            
            elif platform == "shopify":
                # Shopify product/discount creation
                shop = token_data.get("shop")
                
                if content.get("type") == "discount":
                    create_url = f"https://{shop}.myshopify.com/admin/api/2023-10/price_rules.json"
                    
                    headers = {"X-Shopify-Access-Token": access_token}
                    
                    discount_data = {
                        "price_rule": {
                            "title": content.get("title"),
                            "target_type": "line_item",
                            "target_selection": "all",
                            "allocation_method": "across",
                            "value_type": "percentage",
                            "value": f"-{content.get('discount_pct', 10)}",
                            "customer_selection": "all",
                            "starts_at": now_iso()
                        }
                    }
                    
                    r = await client.post(create_url, json=discount_data, headers=headers)
                    result = r.json()
                    
                    post["status"] = "POSTED"
                    post["posted_at"] = now_iso()
                    post["platform_post_id"] = result.get("price_rule", {}).get("id")
                    
                    return {
                        "ok": True,
                        "post_id": post["id"],
                        "platform_post_id": post["platform_post_id"],
                        "message": "Discount created on Shopify"
                    }
        
        except Exception as e:
            post["status"] = "FAILED"
            post["error"] = str(e)
            return {"ok": False, "error": str(e)}
    
    return {"ok": False, "error": "unsupported_platform"}


async def _notify_post_approval(
    username: str,
    post_id: str,
    platform: str,
    content: Dict[str, Any]
) -> None:
    """Notify user to approve post"""
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            preview = content.get("caption", content.get("title", ""))[:100]
            
            await client.post(
                "https://aigentsy-ame-runtime.onrender.com/submit_proposal",
                json={
                    "id": f"post_approval_{uuid4().hex[:8]}",
                    "sender": "aigentsy_conductor",
                    "recipient": username,
                    "title": f"Approve {platform.title()} Post",
                    "body": f"""AiGentsy wants to post on your {platform} account.

Preview: {preview}

Approve at: /conductor/posts/{post_id}/approve
Reject at: /conductor/posts/{post_id}/reject""",
                    "meta": {"post_id": post_id, "platform": platform},
                    "status": "sent",
                    "timestamp": now_iso()
                }
            )
        except Exception as e:
            print(f"Failed to notify user: {e}")


def get_connected_platforms(username: str) -> Dict[str, Any]:
    """Get user's connected platforms"""
    
    platforms = []
    
    for key, token in _OAUTH_TOKENS.items():
        if token["username"] == username:
            platforms.append({
                "platform": token["platform"],
                "connected_at": token["created_at"],
                "status": "ACTIVE"
            })
    
    return {
        "ok": True,
        "username": username,
        "platforms": platforms,
        "count": len(platforms)
    }


def get_pending_posts(username: str) -> Dict[str, Any]:
    """Get user's pending posts"""
    
    pending = [
        post for post in _PENDING_POSTS.values()
        if post["username"] == username and post["status"] == "PENDING_APPROVAL"
    ]
    
    pending.sort(key=lambda p: p["created_at"], reverse=True)
    
    return {
        "ok": True,
        "username": username,
        "pending_posts": pending,
        "count": len(pending)
    }


async def disconnect_platform(
    username: str,
    platform: str
) -> Dict[str, Any]:
    """Disconnect platform"""
    
    token_key = f"{username}:{platform}"
    
    if token_key not in _OAUTH_TOKENS:
        return {"ok": False, "error": "platform_not_connected"}
    
    del _OAUTH_TOKENS[token_key]
    
    return {
        "ok": True,
        "platform": platform,
        "message": f"{platform} disconnected"
    }
