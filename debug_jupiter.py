
import re

def normalize(text):
    return text.strip().lower()

def main():
    required_file = "titulos_faltantes_para_index.txt"
    copy_file = "Copia de titulos_faltantes_para_index.txt"

    with open(required_file, 'r', encoding='utf-8') as f:
        required_titles = set(normalize(line) for line in f if line.strip())

    with open(copy_file, 'r', encoding='utf-8') as f:
        copy_lines = [normalize(line) for line in f]
    
    # Specific Debug for Jupiter
    target = "júpiter en tránsito sextil a júpiter natal"
    print(f"Target in required: {target in required_titles}")
    
    matches_in_copy = [line for line in copy_lines if "júpiter en tránsito sextil a júpiter natal" in line]
    print(f"Matches in copy for '{target}':")
    for m in matches_in_copy:
        print(f"  '{m}'")
        print(f"  Length: {len(m)}")
        print(f"  Target Length: {len(target)}")
        if m == target:
            print("  EXACT MATCH")
        else:
            print("  NO EXACT MATCH - checking chars")
            for i, (c1, c2) in enumerate(zip(target, m)):
                if c1 != c2:
                    print(f"    Difference at index {i}: '{c1}' vs '{c2}'")
                    break

if __name__ == "__main__":
    main()
