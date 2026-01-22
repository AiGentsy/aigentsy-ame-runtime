with open('aigentsy_apex_ultra.py', 'r') as f:
    content = f.read()

# The old broken code (lines 734-751 are wrong indent)
old_code = """            for skill in skills[:5]:  # Top 5 skills
                result = await create_intent(
                    username=self.username,
                    intent_type="offer",
                    description=skill,
                    price=500
                )
                if result.get("ok"):
                    intents_created.append(result)
        
                # Find buyer opportunities
                matches = await find_matches(self.username)
        
        # FIX: Check if matches is a list and has items
            if not isinstance(matches, list):
                matches = []
        
            bids_placed = []
            for match in matches[:3]:  # Bid on top 3
            # FIX: Check if match is a dict and has required fields
                if isinstance(match, dict) and "intent_id" in match:
                    result = await place_bid(
                        username=self.username,
                        intent_id=match["intent_id"],
                        bid_amount=match.get("suggested_bid", 100)
                    )
                    if result.get("ok"):
                        bids_placed.append(result)
        
        # Set Intent Exchange active flag
            self.user.setdefault("intentExchange", {"active": True, "seller": True, "buyer": True})"""

# The new correctly indented code
new_code = """            for skill in skills[:5]:  # Top 5 skills
                result = await create_intent(
                    username=self.username,
                    intent_type="offer",
                    description=skill,
                    price=500
                )
                if result.get("ok"):
                    intents_created.append(result)
        
            # Find buyer opportunities
            matches = await find_matches(self.username)
            
            # Check if matches is a list and has items
            if not isinstance(matches, list):
                matches = []
            
            bids_placed = []
            for match in matches[:3]:  # Bid on top 3
                # Check if match is a dict and has required fields
                if isinstance(match, dict) and "intent_id" in match:
                    result = await place_bid(
                        username=self.username,
                        intent_id=match["intent_id"],
                        bid_amount=match.get("suggested_bid", 100)
                    )
                    if result.get("ok"):
                        bids_placed.append(result)
            
            # Set Intent Exchange active flag
            self.user.setdefault("intentExchange", {"active": True, "seller": True, "buyer": True})"""

content = content.replace(old_code, new_code)

with open('aigentsy_apex_ultra.py', 'w') as f:
    f.write(content)

print("✅ Fixed Intent Exchange indentation properly")
