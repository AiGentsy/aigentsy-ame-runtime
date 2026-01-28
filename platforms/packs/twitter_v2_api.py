"""
TWITTER V2 API PACK: Full Twitter Search Integration

Priority: 100 (highest - premium API access)

Features:
- Recent search with v2 bearer token
- User expansion with metrics
- Multiple search queries covering hiring/freelance/projects
"""

import os
import logging
import hashlib
from typing import Dict, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


async def twitter_v2_search() -> List[Dict]:
    """
    Twitter v2 API - Search for opportunities

    Uses Twitter's recent search endpoint with v2 bearer token
    Searches for hiring, freelance, project help keywords
    """
    import httpx

    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    if not bearer_token:
        logger.debug("No Twitter bearer token, skipping")
        return []

    # Search queries for opportunities
    queries = [
        'hiring developer -is:retweet -is:reply lang:en',
        '(looking for OR need) developer -is:retweet -is:reply lang:en',
        'freelance opportunity -is:retweet -is:reply lang:en',
        'contract work available -is:retweet -is:reply lang:en',
        '(project help OR collaboration) developer -is:retweet -is:reply lang:en'
    ]

    all_tweets = []

    async with httpx.AsyncClient(timeout=15) as client:
        for query in queries[:3]:  # Limit to avoid rate limits
            try:
                response = await client.get(
                    'https://api.twitter.com/2/tweets/search/recent',
                    params={
                        'query': query,
                        'max_results': 20,
                        'tweet.fields': 'created_at,author_id,public_metrics,entities',
                        'expansions': 'author_id',
                        'user.fields': 'username,verified,public_metrics'
                    },
                    headers={'Authorization': f'Bearer {bearer_token}'}
                )

                if response.status_code == 200:
                    data = response.json()
                    tweets = data.get('data', [])
                    users = {u['id']: u for u in data.get('includes', {}).get('users', [])}

                    # Enrich tweets with user data
                    for tweet in tweets:
                        tweet['user'] = users.get(tweet['author_id'], {})

                    all_tweets.extend(tweets)
                    logger.info(f"Twitter v2: {len(tweets)} tweets for '{query[:30]}'")

                elif response.status_code == 429:
                    logger.warning("Twitter rate limit hit")
                    break
                else:
                    logger.warning(f"Twitter API error: {response.status_code}")

            except Exception as e:
                logger.error(f"Twitter search failed: {e}")

    return all_tweets


def twitter_v2_normalizer(raw: dict) -> Dict:
    """Normalize Twitter v2 API response to opportunity format"""

    tweet_id = raw.get('id', '')
    text = raw.get('text', '')
    user = raw.get('user', {})
    username = user.get('username', 'unknown')
    metrics = raw.get('public_metrics', {})

    # Calculate signals
    engagement = (
        metrics.get('like_count', 0) +
        metrics.get('retweet_count', 0) * 2 +
        metrics.get('reply_count', 0) * 3
    )

    verified = user.get('verified', False)
    follower_count = user.get('public_metrics', {}).get('followers_count', 0)

    # Reputation score
    reputation = 0.5
    if verified:
        reputation += 0.3
    if follower_count > 1000:
        reputation += 0.2

    # Payment proximity (keywords)
    payment_keywords = ['pay', 'budget', 'compensation', 'rate', 'salary', 'price', '$']
    payment_proximity = 0.3
    text_lower = text.lower()
    for keyword in payment_keywords:
        if keyword.lower() in text_lower:
            payment_proximity = min(1.0, payment_proximity + 0.15)

    # Contactability
    contactability = 0.6
    if engagement > 10:
        contactability += 0.2
    if '@' in text:
        contactability += 0.1
    if 'dm' in text_lower:
        contactability += 0.1

    return {
        'id': f"twitter_v2_{tweet_id}",
        'platform': 'twitter_v2_api',
        'url': f"https://twitter.com/{username}/status/{tweet_id}",
        'canonical_url': f"https://twitter.com/{username}/status/{tweet_id}",
        'title': text[:200],
        'body': text,
        'discovered_at': datetime.now(timezone.utc).isoformat(),
        'value': 500,
        'payment_proximity': min(1.0, payment_proximity),
        'contactability': min(1.0, contactability),
        'poster_reputation': min(1.0, reputation),
        'type': 'opportunity',
        'source': 'api',
        'metadata': {
            'tweet_id': tweet_id,
            'username': username,
            'verified': verified,
            'engagement': engagement,
            'followers': follower_count
        }
    }


# =============================================================================
# CONTENT POSTING (Proactive brand building)
# =============================================================================

async def post_tweet(content: str, reply_to: str = None) -> Dict:
    """
    Post a tweet from the AiGentsy account using tweepy.

    Args:
        content: Tweet text (max 280 chars)
        reply_to: Optional tweet ID to reply to

    Returns:
        Result dict with success status and tweet ID
    """
    import tweepy

    # OAuth 1.0a credentials
    consumer_key = os.getenv('TWITTER_API_KEY')
    consumer_secret = os.getenv('TWITTER_API_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_secret = os.getenv('TWITTER_ACCESS_SECRET')

    if not all([consumer_key, consumer_secret, access_token, access_secret]):
        return {'success': False, 'error': 'Twitter OAuth credentials not configured'}

    # Truncate to Twitter limit
    if len(content) > 280:
        content = content[:277] + "..."

    try:
        # Create tweepy client
        client = tweepy.Client(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_token_secret=access_secret
        )

        # Post tweet
        if reply_to:
            response = client.create_tweet(
                text=content,
                in_reply_to_tweet_id=reply_to
            )
        else:
            response = client.create_tweet(text=content)

        if response.data:
            tweet_id = response.data['id']
            logger.info(f"Tweet posted: {tweet_id}")
            return {
                'success': True,
                'tweet_id': tweet_id,
                'platform': 'twitter',
                'url': f"https://twitter.com/AiGentsy/status/{tweet_id}"
            }
        else:
            return {'success': False, 'error': 'No response data from Twitter'}

    except tweepy.TweepyException as e:
        logger.error(f"Tweepy error: {e}")
        return {'success': False, 'error': str(e)}
    except Exception as e:
        logger.error(f"Tweet error: {e}")
        return {'success': False, 'error': str(e)}


async def post_thread(tweets: List[str]) -> Dict:
    """
    Post a Twitter thread (multiple connected tweets).

    Args:
        tweets: List of tweet texts (will be posted in order)

    Returns:
        Result dict with all tweet IDs
    """
    if not tweets:
        return {'success': False, 'error': 'No tweets provided'}

    results = []
    reply_to = None

    for i, content in enumerate(tweets):
        result = await post_tweet(content, reply_to=reply_to)

        if not result.get('success'):
            logger.warning(f"Thread stopped at tweet {i}: {result.get('error')}")
            break

        results.append(result)
        reply_to = result.get('tweet_id')

    return {
        'success': len(results) > 0,
        'tweets': results,
        'thread_length': len(results),
        'thread_url': results[0].get('url') if results else None
    }


# Pack registration
TWITTER_V2_PACK = {
    'name': 'twitter_v2_api',
    'priority': 100,
    'api_func': twitter_v2_search,
    'normalizer': twitter_v2_normalizer,
    'requires_auth': True,
    'has_api': True,
    'post_tweet': post_tweet,
    'post_thread': post_thread
}
