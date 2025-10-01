import csv
import requests
from bs4 import BeautifulSoup
import time
import json

INPUT_FILE = "01_ids.csv"        # archivo con PMCID / PMID / DOI
OUTPUT_FILE = "03_pubmed_metadata.json"

def fetch_pubmed_metadata(pmid: str):
    """Descarga metadatos desde PubMed Entrez API (efetch) usando el PMID"""
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {"db": "pubmed", "id": pmid, "retmode": "xml"}

    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        print(f"⚠️ No pude obtener metadatos para PMID {pmid}")
        return None

    soup = BeautifulSoup(resp.content, "lxml-xml")

    article = soup.find("PubmedArticle")
    if not article:
        return None

    # ---- Título ----
    title = article.find("ArticleTitle")
    title = title.get_text(" ", strip=True) if title else None

    # ---- Journal ----
    journal = article.find("Title")
    journal = journal.get_text(" ", strip=True) if journal else None

    # ---- Año ----
    pubdate = article.find("PubDate")
    year = None
    if pubdate:
        year_tag = pubdate.find("Year")
        if year_tag:
            year = year_tag.get_text(strip=True)
        else:
            medline_date = pubdate.find("MedlineDate")
            if medline_date:
                year = medline_date.get_text(strip=True).split(" ")[0]

    # ---- Autores ----
    authors = []
    for author in article.find_all("Author"):
        last = author.find("LastName")
        fore = author.find("ForeName")
        collective = author.find("CollectiveName")
        if collective:
            authors.append(collective.get_text(strip=True))
        elif last and fore:
            authors.append(f"{fore.get_text(strip=True)} {last.get_text(strip=True)}")

    # ---- Palabras clave ----
    keywords = [kw.get_text(strip=True) for kw in article.find_all("Keyword")]

    return {
        "title_pubmed": title,
        "journal": journal,
        "year": year,
        "authors": authors,
        "keywords": keywords
    }

def main():
    enriched_data = []

    with open(INPUT_FILE, newline="", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            pmid = row.get("pmid")
            if not pmid:
                print(f"⚠️ {row['title']} no tiene PMID")
                continue

            print(f"🔎 Buscando metadatos en PubMed para PMID {pmid}...")
            meta = fetch_pubmed_metadata(pmid)

            if meta:
                enriched_row = {
                    "pmid": pmid,
                    "pmcid": row.get("pmcid"),
                    "doi": row.get("doi"),
                    "title_input": row.get("title"),
                    "link": row.get("link"),
                    **meta
                }
                enriched_data.append(enriched_row)
                print(f"✅ Metadatos extraídos para PMID {pmid}")
            else:
                print(f"⚠️ No se obtuvieron metadatos para PMID {pmid}")

            time.sleep(0.4)  # respetar rate limit de NCBI

    # Guardar salida como JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(enriched_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Guardado en {OUTPUT_FILE} con {len(enriched_data)} artículos enriquecidos")


if __name__ == "__main__":
    main()
