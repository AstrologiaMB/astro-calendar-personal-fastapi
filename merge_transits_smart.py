
import re
import os

def normalize_title(t):
    return t.strip().lower()

def get_planet_from_title(title):
    # Title format: "### planeta en tránsito..."
    # clean: "planeta en tránsito..."
    clean = title.replace('#', '').strip().lower()
    parts = clean.split()
    if not parts: return "unknown"
    return parts[0] # "sol", "luna", "júpiter", etc.

def main():
    target_path = "/Users/apple/astro_interpretador_rag_fastapi/data/20 - tránsitos.md"
    source_path = "/Users/apple/astro-calendar-personal-fastapi/transitos_faltantes_convertidos.md"
    
    # Planets definition
    fast_planets = ["sol", "luna", "mercurio", "venus", "marte"]
    slow_planets = ["júpiter", "saturno", "urano", "neptuno", "plutón"]
    
    # 1. Read Target File and Split by Sections
    with open(target_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
        
    # We want to split by "## planeta en tránsito"
    # But we need to keep the order.
    # Let's find the indices of "## " headers
    
    # Simple strategy: Parse lines, build a structured object
    lines = original_content.splitlines()
    sections = [] # List of {'header': str, 'content': [], 'planet': str, 'type': 'main'|'intro'}
    
    current_section = {'header': '', 'content': [], 'planet': '', 'type': 'intro'}
    sections.append(current_section)
    
    planet_header_regex = re.compile(r'^##\s+(\w+)\s+en\s+tránsito')
    
    for line in lines:
        match = planet_header_regex.match(line.lower())
        if match:
            # Start new section
            planet = match.group(1)
            current_section = {'header': line, 'content': [], 'planet': planet, 'type': 'planet_section'}
            sections.append(current_section)
        else:
            current_section['content'].append(line)
            
    print(f"Parsed {len(sections)} sections from target file.")
    for s in sections:
        if s['type'] == 'planet_section':
            print(f" - Found section for: {s['planet']}")

    # 2. Parse Source File (New Content)
    new_items_by_planet = {} # {'luna': [lines], 'júpiter': [lines]}
    
    with open(source_path, 'r', encoding='utf-8') as f:
        source_lines = f.readlines()
        
    current_item = []
    current_planet = None
    
    for line in source_lines:
        if line.strip().startswith('### '):
            # Save previous if exists
            if current_planet and current_item:
                if current_planet not in new_items_by_planet:
                    new_items_by_planet[current_planet] = []
                new_items_by_planet[current_planet].append(current_item)
            
            # Start new
            current_item = [line]
            # Extract planet
            title_text = line.strip().replace('###', '').strip().lower()
            current_planet = title_text.split()[0]
        else:
            if current_item:
                current_item.append(line)
                
    # Save last
    if current_planet and current_item:
        if current_planet not in new_items_by_planet:
            new_items_by_planet[current_planet] = []
        new_items_by_planet[current_planet].append(current_item)
        
    print(f"Parsed new items for planets: {list(new_items_by_planet.keys())}")

    # 3. Merging Logic
    
    # Special Case: Luna (if section doesn't exist, create it)
    luna_exists = any(s['planet'] == 'luna' for s in sections)
    if 'luna' in new_items_by_planet and not luna_exists:
        print("Creating new section for 'luna'...")
        # Insert after 'sol' if exists, otherwise at end of intros
        insert_idx = 1 # Default after intro
        for i, s in enumerate(sections):
            if s['planet'] == 'sol':
                insert_idx = i + 1
                break
        
        new_luna_section = {
            'header': '## luna en tránsito',
            'content': ['', ''], # specific intro text could be added here if we had it
            'planet': 'luna',
            'type': 'planet_section'
        }
        sections.insert(insert_idx, new_luna_section)

    # Now verify sections updated
    section_map = {s['planet']: s for s in sections if s['planet']}
    
    for planet, items_list in new_items_by_planet.items():
        if planet not in section_map:
            print(f"WARNING: No section found for {planet}, skipping items.")
            continue
            
        target_section = section_map[planet]
        is_slow = planet in slow_planets
        
        print(f"Merging {len(items_list)} items into {planet} (Slow: {is_slow})")
        
        for item_lines in items_list:
            header = item_lines[0].strip()
            body = item_lines[1:]
            
            # Adjust Header Level
            if is_slow:
                # Should be ####
                clean_header = header.replace('#', '').strip()
                new_header = f"#### {clean_header}"
            else:
                # Should be ###
                clean_header = header.replace('#', '').strip()
                new_header = f"### {clean_header}"
            
            # Prepare content block
            block_to_add = [new_header] + [b.rstrip() for b in body] + ['']
            
            # Insert Logic
            # If slow, we ideally want to append to '### tránsitos de [planet] aspectos' if it exists in content
            # If fast, append to end of content
            
            if is_slow:
                # Find the "aspectos" subsection in content lines
                aspects_header_idx = -1
                for i, line in enumerate(target_section['content']):
                    if "aspectos" in line.lower() and line.strip().startswith('### '):
                        aspects_header_idx = i
                        # We don't break, effectively finding the start of that section, 
                        # but we really want to append to the END of that section.
                        # The end of the section is effectively the end of the planets content 
                        # OR before the next major block? 
                        # In this file, "aspectos" seems to be the last subsection for slow planets.
                        # So appending to the end of target_section['content'] is likely safe 
                        # provided we are inside the 'aspectos' flow.
                        pass 
                
                # If we found an aspects header, we assume everything after it belongs to it.
                # So we can just append to the end of the section content.
                if aspects_header_idx != -1:
                     target_section['content'].extend([''] + block_to_add)
                else:
                    # If no aspects header (weird for slow), just append
                     target_section['content'].extend([''] + block_to_add)
            else:
                # Fast planet: Append to end of section
                target_section['content'].extend([''] + block_to_add)

    # 4. Reconstruct File
    final_lines = []
    for s in sections:
        if s['header']:
            final_lines.append(s['header'])
        final_lines.extend(s['content'])
        # Ensure section ends with simple newline if not present
        if final_lines and final_lines[-1].strip() != '':
             final_lines.append('')

    # Write
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_lines))
        
    print(f"✅ Merged content successfully.")

if __name__ == "__main__":
    main()
