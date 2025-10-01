import csv
import requests
from bs4 import BeautifulSoup
import time
import json

INPUT_FILE = "01_ids.csv"      # generado en el paso anterior
OUTPUT_FILE = "02_fulltext.json"

def fetch_fulltext(pmcid: str, pmid: str = None):
    """Intenta obtener Results/Conclusions de EuropePMC, si no, usa PubMed Abstract como fallback."""

    # --- Plan A: EuropePMC full text XML ---
    url_xml = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"
    resp = requests.get(url_xml)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.content, "lxml-xml")
        results, conclusions = [], []

        for sec in soup.find_all("sec"):
            title_tag = sec.find("title")
            title = title_tag.get_text() if title_tag else ""
            text = " ".join(p.get_text(" ", strip=True) for p in sec.find_all("p"))

            if "result" in title.lower():
                results.append(text)
            elif "conclusion" in title.lower():
                conclusions.append(text)

        return {
            "results": results,
            "conclusions": conclusions,
            "abstract": [],
            "source": "EuropePMC"
        }

    # --- Plan B: fallback → PubMed Abstract ---
    if pmid:
        url_abs = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&retmode=xml"
        r2 = requests.get(url_abs)
        if r2.status_code == 200:
            soup = BeautifulSoup(r2.content, "lxml-xml")
            abs_texts = [a.get_text(" ", strip=True) for a in soup.find_all("AbstractText")]
            return {
                "results": [],
                "conclusions": [],
                "abstract": abs_texts,
                "source": "PubMed"
            }

    # --- Plan C: nada encontrado ---
    return None


def main():
    papers_out = []

    with open(INPUT_FILE, newline="", encoding="utf-8-sig") as infile:
        reader = csv.DictReader(infile)

        for row in reader:
            pmcid = row["pmcid"]
            pmid = row["pmid"]
            title = row["title"]

            if not pmcid:
                print(f"⚠️ {title} no tiene PMCID")
                continue

            print(f"🔎 Descargando texto para {pmcid}...")
            sections = fetch_fulltext(pmcid, pmid)

            if sections:
                papers_out.append({
                    "title": title,
                    "pmcid": pmcid,
                    "pmid": pmid,
                    "results": sections["results"],
                    "conclusions": sections["conclusions"],
                    "abstract": sections["abstract"],
                    "source": sections["source"]
                })
                print(f"✅ Extraído desde {sections['source']} para {pmcid}")
            else:
                print(f"⚠️ No se pudo extraer nada para {pmcid}")

            time.sleep(0.5)  # respetar servidores

    # Guardar resultados
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(papers_out, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Guardado en {OUTPUT_FILE} con {len(papers_out)} artículos procesados")


if __name__ == "__main__":
    main()
