
import os

def normalize_key(text):
    # Retrieve base form for matching: lowercase, strip BOM, grammar fix
    # Handle BOM by encoding/decoding or just replacing \ufeff
    text = text.replace('\ufeff', '').strip().lower()
    text = text.replace('al sol', 'a sol')
    return text

def main():
    source_path = "titulos_faltantes_para_index.txt"
    target_path = "Copia de titulos_faltantes_para_index.txt"
    
    # 1. Load Source Titles into a Map for exact retrieval
    # Key: normalized version (e.g. "sol en tránsito sextil a sol natal")
    # Value: exact string from file (e.g. "sol en tránsito sextil a sol natal")
    valid_titles_map = {}
    
    with open(source_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                # The source file already has the desired format (lowercase, 'a sol')
                # But we normalize just to be sure we match against what we'll produce from the target
                clean_line = line.strip()
                key = normalize_key(clean_line)
                valid_titles_map[key] = clean_line
                
    print(f"Loaded {len(valid_titles_map)} valid titles from source.")

    # 2. Process Target File
    new_lines = []
    
    with open(target_path, 'r', encoding='utf-8') as f:
        # Read lines one by one
        target_lines = f.readlines()
        
    replaced_count = 0
    
    for line in target_lines:
        original_line = line
        stripped = line.strip()
        
        if not stripped:
            new_lines.append(line)
            continue
            
        # Check if this line looks like a title we want to replace
        # We try to normalize it and see if it exists in our valid map
        key = normalize_key(stripped)
        
        if key in valid_titles_map:
            # It's a title! Replace with the exact form from source
            correct_title = valid_titles_map[key]
            
            # Preserve newline if original had it
            if line.endswith('\n'):
                new_line = correct_title + '\n'
            else:
                new_line = correct_title
                
            if new_line != line:
                # remove BOM if present in comparison too, purely for logging
                if line.replace('\ufeff', '') != new_line:
                     replaced_count += 1
            
            new_lines.append(new_line)
        else:
            # Not a title, or a title not in our source list (shouldn't happen based on previous check)
            # Just keep it as is (Descriptions, etc)
            new_lines.append(line)

    # 3. Write Back
    with open(target_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print(f"✅ Processed {len(target_lines)} lines.")
    print(f"✅ Replaced {replaced_count} titles/lines.")

if __name__ == "__main__":
    main()
