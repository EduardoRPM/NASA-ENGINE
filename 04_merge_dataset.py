import json

FULLTEXT_FILE = "02_fulltext.json"
PUBMED_FILE = "03_pubmed_metadata.json"
OUTPUT_FILE = "04_merged_dataset.json"

def main():
    # --- Cargar archivos ---
    with open(FULLTEXT_FILE, "r", encoding="utf-8") as f:
        fulltext_data = json.load(f)

    with open(PUBMED_FILE, "r", encoding="utf-8") as f:
        pubmed_data = json.load(f)

    # Indexar pubmed_data por PMID y PMCID para búsqueda rápida
    pubmed_by_pmid = {p.get("pmid"): p for p in pubmed_data if p.get("pmid")}
    pubmed_by_pmcid = {p.get("pmcid"): p for p in pubmed_data if p.get("pmcid")}

    merged = []

    for paper in fulltext_data:
        pmid = paper.get("pmid")
        pmcid = paper.get("pmcid")

        # Buscar metadatos asociados
        meta = None
        if pmid and pmid in pubmed_by_pmid:
            meta = pubmed_by_pmid[pmid]
        elif pmcid and pmcid in pubmed_by_pmcid:
            meta = pubmed_by_pmcid[pmcid]

        merged_entry = {
            "title": paper.get("title"),
            "pmcid": pmcid,
            "pmid": pmid,
            "doi": paper.get("doi"),
            "results": paper.get("results", []),
            "conclusions": paper.get("conclusions", []),
            "abstract": paper.get("abstract", []),
            "source": paper.get("source")
        }

        if meta:
            merged_entry.update({
                "title_pubmed": meta.get("title_pubmed"),
                "journal": meta.get("journal"),
                "year": meta.get("year"),
                "authors": meta.get("authors"),
                "keywords": meta.get("keywords")
            })

        merged.append(merged_entry)

    # Guardar dataset final
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"✅ Guardado en {OUTPUT_FILE} con {len(merged)} artículos combinados")

if __name__ == "__main__":
    main()
