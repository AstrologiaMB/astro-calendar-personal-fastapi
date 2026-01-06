
import csv
import re

def normalize_rag_title(raw_title):
    """
    Transforms: 'Sol (directo) por tránsito esta en Trígono a tu Urano Natal'
    To: 'sol en tránsito trígono a urano natal'
    """
    # 1. Lowercase
    lower_title = raw_title.lower()
    
    # 2. Extract components using regex
    # Pattern: metches "(planet) (...) por tránsito esta en (aspect) a tu (planet) natal"
    pattern = r"([a-záéíóúüñ]+)\s*\(.*?\)\s*por tránsito esta en\s*([a-záéíóúüñ]+)\s*a tu\s*([a-záéíóúüñ]+)\s*natal"
    match = re.search(pattern, lower_title)
    
    if match:
        p1 = match.group(1)
        aspect = match.group(2)
        p2 = match.group(3)
        return f"{p1} en tránsito {aspect} a {p2} natal"
    
    # Fallback/Debug if pattern doesn't match
    return f"FAILED_TO_PARSE: {lower_title}"

def main():
    input_csv = "reporte_faltantes_rag.csv"
    output_txt = "titulos_faltantes_para_index.txt"
    
    titles_to_write = []
    
    try:
        with open(input_csv, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_title = row.get("Titulo_Requerido", "")
                if raw_title:
                    normalized = normalize_rag_title(raw_title)
                    if "FAILED_TO_PARSE" not in normalized:
                        titles_to_write.append(normalized)
                    else:
                        print(f"Warning: Could not parse '{raw_title}'")

        # Remove duplicates and sort
        unique_titles = sorted(list(set(titles_to_write)))

        with open(output_txt, mode='w', encoding='utf-8') as f:
            for title in unique_titles:
                f.write(title + "\n")
                
        print(f"✅ Successfully generated '{output_txt}' with {len(unique_titles)} unique titles.")
        print("First 5 titles:")
        for t in unique_titles[:5]:
            print(f"  - {t}")

    except FileNotFoundError:
        print(f"❌ Error: Could not find {input_csv}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
