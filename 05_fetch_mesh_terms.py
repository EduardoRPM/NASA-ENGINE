import csv
import requests
from bs4 import BeautifulSoup
import time
import json

INPUT_FILE = "01_ids.csv"             # tu archivo con PMCID / PMID
OUTPUT_FILE = "05_mesh_terms.json"

def fetch_mesh_terms(pmid: str):
    """Obtiene los MeSH terms de PubMed usando Entrez EFetch"""
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {"db": "pubmed", "id": pmid, "retmode": "xml"}

    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        print(f"⚠️ Error {resp.status_code} al descargar PMID {pmid}")
        return []

    soup = BeautifulSoup(resp.content, "lxml-xml")

    mesh_terms = []
    for mh in soup.find_all("MeshHeading"):
        descriptor = mh.find("DescriptorName")
        qualifier = mh.find("QualifierName")

        if descriptor:
            term = descriptor.get_text(strip=True)
            if qualifier:
                term = f"{term} / {qualifier.get_text(strip=True)}"
            mesh_terms.append(term)

    return mesh_terms


def main():
    enriched = []

    with open(INPUT_FILE, newline="", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            pmid = row.get("pmid")
            if not pmid:
                print(f"⚠️ El artículo '{row['title']}' no tiene PMID, lo salto.")
                continue

            print(f"🔎 Buscando MeSH terms para PMID {pmid}...")
            mesh_terms = fetch_mesh_terms(pmid)

            enriched.append({
                "title": row["title"],
                "pmid": pmid,
                "pmcid": row.get("pmcid"),
                "mesh_terms": mesh_terms
            })

            print(f"✅ PMID {pmid} → {len(mesh_terms)} términos encontrados")
            time.sleep(0.4)  # respetar rate limit NCBI

    # Guardar en JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Guardado en {OUTPUT_FILE} con {len(enriched)} artículos")


if __name__ == "__main__":
    main()
