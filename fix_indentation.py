with open('aigentsy_apex_ultra.py', 'r') as f:
    lines = f.readlines()

# Fix lines 732-758 (0-indexed: 731-757)
fixed = []
for i, line in enumerate(lines):
    if 731 <= i <= 757:  # Lines that need fixing
        # Add 4 spaces to indent them properly inside try block
        if line.strip():  # Only indent non-empty lines
            fixed.append('    ' + line)
        else:
            fixed.append(line)
    else:
        fixed.append(line)

with open('aigentsy_apex_ultra.py', 'w') as f:
    f.writelines(fixed)

print("✅ Fixed Intent Exchange indentation")
