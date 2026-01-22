# Fix all 6 bugs in aigentsy_apex_ultra.py

with open('aigentsy_apex_ultra.py', 'r') as f:
    content = f.read()

# FIX #1: Intent Exchange - move matches outside loop
old = """                intents_created.append(result)
        
                # Find buyer opportunities
                matches = await find_matches(self.username)
        
        # FIX: Check if matches is a list and has items"""

new = """                intents_created.append(result)
        
        # Find buyer opportunities
        matches = await find_matches(self.username)
        
        # FIX: Check if matches is a list and has items"""

content = content.replace(old, new)

with open('aigentsy_apex_ultra.py', 'w') as f:
    f.write(content)

print("✅ Fixed Intent Exchange - moved matches outside loop")
