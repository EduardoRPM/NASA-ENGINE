import json

MERGED_FILE = "/Users/diegopermar/NASA ENGINE/04_merged_dataset.json"
MESH_FILE = "/Users/diegopermar/NASA ENGINE/05_mesh_terms.json"
OUTPUT_FILE = "/Users/diegopermar/NASA ENGINE/06_dataset_enriched.json"

def main():
    # Cargar ambos archivos
    with open(MERGED_FILE, "r", encoding="utf-8") as f:
        merged_data = json.load(f)

    with open(MESH_FILE, "r", encoding="utf-8") as f:
        mesh_data = json.load(f)

    # Indexar MeSH por PMID
    mesh_by_pmid = {m["pmid"]: m.get("mesh_terms", []) for m in mesh_data}

    enriched = []
    for paper in merged_data:
        pmid = paper.get("pmid")
        mesh_terms = mesh_by_pmid.get(pmid, [])

        # fallback → usar keywords si no hay MeSH
        if mesh_terms:
            topics = mesh_terms
        elif paper.get("keywords"):
            topics = paper["keywords"]
        else:
            topics = ["not_indexed"]

        paper["mesh_terms"] = mesh_terms
        paper["topics"] = topics

        enriched.append(paper)

    # Guardar archivo final
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"✅ Guardado en {OUTPUT_FILE} con {len(enriched)} artículos enriquecidos")

if __name__ == "__main__":
    main()
