
import os

def normalize(text):
    return text.strip().lower()

def main():
    titles_file = "titulos_faltantes_para_index.txt"
    content_file = "Copia de titulos_faltantes_para_index.txt"
    output_file = "transitos_faltantes_convertidos.md"

    # 1. Load Valid Titles
    with open(titles_file, 'r', encoding='utf-8') as f:
        valid_titles = set(normalize(line) for line in f if line.strip())

    print(f"Loaded {len(valid_titles)} valid titles.")

    # 2. Process Content File
    markdown_lines = []
    
    with open(content_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        normalized = normalize(stripped)
        
        # Check if line is a title
        if normalized in valid_titles:
            # Add spacing before title if not first line
            if markdown_lines:
                markdown_lines.append("\n")
            
            # Format as H3
            markdown_lines.append(f"### {stripped}\n")
            markdown_lines.append("\n") # Blank line after header
        else:
            # Description text
            markdown_lines.append(f"{stripped}\n")

    # 3. Write Output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(markdown_lines)
        
    print(f"✅ Generated {output_file}")
    print(f"Total lines: {len(markdown_lines)}")

if __name__ == "__main__":
    main()
