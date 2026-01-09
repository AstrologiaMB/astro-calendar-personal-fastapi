
import re

def normalize(text):
    return text.strip().lower()

def main():
    required_file = "titulos_faltantes_para_index.txt"
    copy_file = "Copia de titulos_faltantes_para_index.txt"

    # 1. Load Required Titles
    with open(required_file, 'r', encoding='utf-8') as f:
        required_titles = set(normalize(line) for line in f if line.strip())

    print(f"Required Titles Count: {len(required_titles)}")

    # 2. Extract Titles from Copy
    # The copy has titles mixed with text. 
    # Titles seem to follow the pattern "[Planet] en tránsito [aspect] a [Planet] natal"
    # We can just iterate all lines, normalize them, and see if they match any required title.
    
    with open(copy_file, 'r', encoding='utf-8') as f:
        copy_lines = [normalize(line) for line in f]

    found_titles = set()
    
    # Check for exact matches first (ignoring case)
    for line in copy_lines:
        if line in required_titles:
            found_titles.add(line)
            
    # Calculate Missing
    missing = required_titles - found_titles

    if not missing:
        print("✅ SUCCESS: All required titles are present in the copy file.")
    else:
        print(f"❌ FAIL: {len(missing)} titles are missing from the copy file.")
        print("Missing Titles:")
        for t in sorted(missing):
            print(f"  - {t}")

    print(f"\nFound {len(found_titles)} / {len(required_titles)} required titles.")

if __name__ == "__main__":
    main()
