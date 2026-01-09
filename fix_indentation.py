
lines = []
with open('src/calculators/vectorized_transits_calculator.py', 'r') as f:
    lines = f.readlines()

# Lines are 0-indexed in list, but 1-indexed in file.
# We want to indent lines 150 to 216 (approx).
# The previous loop ended around 214, but we added one line to the header so indices shifted.
# Let's find the range dynamically or just guess safely.
# Line 148 is "target = ...".
# Line 150 starts the logic that needs indenting.
start_line = 150
end_line = 216

new_lines = []
for i, line in enumerate(lines):
    if i >= (start_line - 1) and i <= (end_line - 1):
        if line.strip():
            new_line = "    " + line
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

with open('src/calculators/vectorized_transits_calculator.py', 'w') as f:
    f.writelines(new_lines)

print("Indentation fixed.")
