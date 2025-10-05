"""
Script para mezclar datos de citaciones del backup con el archivo actual.
Sin hacer nuevas llamadas a la API.
"""
import json

BACKUP_FILE = "09_dataset_complete.backup.json"
CURRENT_FILE = "09_dataset_complete.json"
OUTPUT_FILE = "09_dataset_complete.json"

def main():
    print("[INFO] Loading backup file...")
    with open(BACKUP_FILE, "r", encoding="utf-8") as f:
        backup_data = json.load(f)

    print("[INFO] Loading current file...")
    with open(CURRENT_FILE, "r", encoding="utf-8") as f:
        current_data = json.load(f)

    print(f"[INFO] Total articles: {len(current_data)}")

    # Crear índice por título para acceso rápido al backup
    backup_index = {article.get("title"): article for article in backup_data}

    merged_count = 0
    already_complete = 0
    not_in_backup = 0

    for article in current_data:
        title = article.get("title")

        # Si el artículo actual ya tiene citaciones, no tocar
        if article.get("citations") and article.get("citations").get("citation_count") is not None:
            already_complete += 1
            continue

        # Buscar en el backup
        if title in backup_index:
            backup_article = backup_index[title]

            # Si el backup tiene citaciones, copiarlas
            if backup_article.get("citations") and backup_article.get("citations").get("citation_count") is not None:
                article["citations"] = backup_article["citations"]
                article["formatted_citations"] = backup_article.get("formatted_citations", article.get("formatted_citations"))
                merged_count += 1
                print(f"  [+] Merged citations for: {title[:60]}...")
        else:
            not_in_backup += 1

    # Guardar resultado
    print(f"\n[SAVE] Saving merged data to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(current_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"MERGE COMPLETED!")
    print(f"{'='*60}")
    print(f"Articles already complete: {already_complete}")
    print(f"Citations merged from backup: {merged_count}")
    print(f"Articles not in backup: {not_in_backup}")
    print(f"Total articles: {len(current_data)}")
    print(f"{'='*60}")

    # Verificar resultado final
    final_count = sum(1 for a in current_data if a.get("citations") and a.get("citations").get("citation_count") is not None)
    print(f"\n[FINAL] Articles with citation data: {final_count}/{len(current_data)}")
    print(f"[FINAL] Missing citations: {len(current_data) - final_count}")

if __name__ == "__main__":
    main()
