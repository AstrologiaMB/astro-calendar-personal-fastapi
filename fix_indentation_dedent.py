
lines = []
with open('src/calculators/vectorized_transits_calculator.py', 'r') as f:
    lines = f.readlines()

start_line = 150
end_line = 216

new_lines = []
for i, line in enumerate(lines):
    if i >= (start_line - 1) and i <= (end_line - 1):
        # We need to REMOVE 4 spaces (dedent)
        # Check if line starts with enough spaces
        if line.startswith("                            "): # 28 spaces
            new_line = line[4:] # Remove 4 spaces -> 24 spaces
            new_lines.append(new_line)
        elif line.startswith("                        "): # 24 spaces (maybe blank lines?)
             # If it's a blank line with spaces, just trim it or keep it?
             # Let's just remove 4 chars if it mimics indentation
             if line.strip() == "":
                 new_lines.append(line)
             else:
                 # This is unexpected, if we have lines with < 28 spaces in the block
                 # It might be `else:` blocks? 
                 # `else:` at level 7 would be 28 spaces.
                 # `else:` at level 6 would be 24 spaces.
                 # If we have 28, we want 24.
                 new_lines.append(line[4:])
        else:
             # Should not happen for code, but maybe blank lines
             new_lines.append(line)
    else:
        new_lines.append(line)

with open('src/calculators/vectorized_transits_calculator.py', 'w') as f:
    f.writelines(new_lines)

print("Dedent fixed.")
