import asyncio
import sys
sys.path.insert(0, '.')

from main import get_user, log_agent_update, activate_apex_ultra
from datetime import datetime, timezone

async def create_test_user():
    username = "testuser1000"
    existing = get_user(username)
    if existing:
        print(f"User {username} already exists!")
        return
    
    user = {
        "username": username,
        "email": "test1000@test.com",
        "template": "whitelabel_general",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "reputationScore": 50,
        "ownership": {"aigx": 0, "equity_percentage": 0},
        "skills": ["marketing", "sales", "content"],
        "connectedPlatforms": [],
        "offers": [],
        "deals": []
    }
    
    log_agent_update(user)
    print(f"Created user: {username}")
    
    result = await activate_apex_ultra(username=username, template="whitelabel_general", automation_mode="pro")
    
    print("\nAPEX RESULTS:")
    results = result.get('activation', {}).get('results', {})
    
    working = []
    broken = []
    
    for system, status in results.items():
        if status.get('ok'):
            working.append(system)
            print(f"  ✅ {system}")
        else:
            broken.append(system)
            print(f"  ❌ {system}: {status.get('error')}")
    
    print(f"\nWorking: {len(working)} | Broken: {len(broken)}")
    
    if broken:
        print("\nBROKEN SYSTEMS:")
        for s in broken:
            print(f"  - {s}")
    
    return result

if __name__ == "__main__":
    asyncio.run(create_test_user())
