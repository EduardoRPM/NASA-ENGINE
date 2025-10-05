import csv
import requests
import time
import json
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
# File paths
INPUT_CSV = "data/SB_publication_PMC.csv"
INPUT_JSON = "09_dataset_complete.json"  # Cargar v09 existente para preservar progreso
OUTPUT_JSON = "09_dataset_complete.json"

# API endpoints
OPENCITATIONS_POCI_BASE = os.getenv("OPENCITATIONS_POCI_BASE")
OPENCITATIONS_COCI_BASE = os.getenv("OPENCITATIONS_COCI_BASE")
SEMANTIC_SCHOLAR_BASE = os.getenv("SEMANTIC_SCHOLAR_BASE")

def load_csv_mapping() -> Dict[str, str]:
    """Carga el CSV y crea un diccionario de título -> URL."""
    mapping = {}

    with open(INPUT_CSV, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            title = row.get("Title", "").strip()
            link = row.get("Link", "").strip()
            if title and link:
                mapping[title] = link

    print(f"[INFO] Loaded {len(mapping)} links from CSV")
    return mapping

def get_citation_count_opencitations(pmid: Optional[str] = None, doi: Optional[str] = None) -> Optional[int]:
    """
    Obtiene el conteo de citaciones desde OpenCitations.
    Intenta PMID primero (POCI), luego DOI (COCI).
    """
    # Intentar con PMID primero
    if pmid:
        try:
            url = f"{OPENCITATIONS_POCI_BASE}/citation-count/pmid:{pmid}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    count = data[0].get("count")
                    if count is not None:
                        return int(count)
        except Exception as e:
            print(f"  [!] OpenCitations PMID error: {e}")

    # Intentar con DOI como fallback
    if doi:
        try:
            url = f"{OPENCITATIONS_COCI_BASE}/citation-count/{doi}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    count = data[0].get("count")
                    if count is not None:
                        return int(count)
        except Exception as e:
            print(f"  [!] OpenCitations DOI error: {e}")

    return None

def get_citation_count_semantic_scholar(pmid: Optional[str] = None, doi: Optional[str] = None) -> Optional[Dict]:
    """
    Obtiene datos de citación desde Semantic Scholar API.
    Retorna un diccionario con citation_count e influential_citation_count.
    """
    identifier = None

    if doi:
        identifier = f"DOI:{doi}"
    elif pmid:
        identifier = f"PMID:{pmid}"

    if not identifier:
        return None

    try:
        url = f"{SEMANTIC_SCHOLAR_BASE}/paper/{identifier}"
        params = {"fields": "citationCount,influentialCitationCount"}

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return {
                "citation_count": data.get("citationCount"),
                "influential_citation_count": data.get("influentialCitationCount")
            }
    except Exception as e:
        print(f"  [!] Semantic Scholar error: {e}")

    return None

def format_authors_apa(authors: List[str]) -> str:
    """Formatea autores en estilo APA."""
    if not authors:
        return ""

    formatted = []
    for author in authors[:7]:  # APA usa máximo 7 autores
        parts = author.split()
        if len(parts) >= 2:
            # Apellido, Inicial(es)
            last_name = parts[-1]
            initials = "".join([p[0] + "." for p in parts[:-1] if p])
            formatted.append(f"{last_name}, {initials}")
        else:
            formatted.append(author)

    if len(authors) > 7:
        return ", ".join(formatted[:6]) + ", ... " + formatted[-1]
    elif len(formatted) > 1:
        return ", ".join(formatted[:-1]) + ", & " + formatted[-1]
    else:
        return formatted[0] if formatted else ""

def format_authors_bibtex(authors: List[str]) -> str:
    """Formatea autores para BibTeX."""
    if not authors:
        return ""
    return " and ".join(authors)

def generate_apa_citation(article: Dict) -> str:
    """Genera una citación en formato APA 7."""
    authors = format_authors_apa(article.get("authors", []))
    year = article.get("year", "n.d.")
    title = article.get("title", "")
    journal = article.get("journal", "")
    doi = article.get("doi", "")

    citation = f"{authors} ({year}). {title}. "

    if journal:
        citation += f"*{journal}*. "

    if doi:
        citation += f"https://doi.org/{doi}"
    elif article.get("link"):
        citation += article.get("link")

    return citation

def generate_bibtex_citation(article: Dict) -> str:
    """Genera una citación en formato BibTeX."""
    pmid = article.get("pmid", "")
    year = article.get("year", "")
    title = article.get("title", "").replace("{", "\\{").replace("}", "\\}")
    authors = format_authors_bibtex(article.get("authors", []))
    journal = article.get("journal", "")
    doi = article.get("doi", "")

    # Generar citekey
    first_author = article.get("authors", ["Unknown"])[0].split()[-1] if article.get("authors") else "Unknown"
    citekey = f"{first_author}{year}"

    bibtex = f"@article{{{citekey},\n"
    bibtex += f"  author = {{{authors}}},\n"
    bibtex += f"  title = {{{{{title}}}}},\n"
    bibtex += f"  journal = {{{journal}}},\n"
    bibtex += f"  year = {{{year}}},\n"

    if doi:
        bibtex += f"  doi = {{{doi}}},\n"
    if pmid:
        bibtex += f"  pmid = {{{pmid}}},\n"

    bibtex += "}"

    return bibtex

def generate_ris_citation(article: Dict) -> str:
    """Genera una citación en formato RIS."""
    ris = "TY  - JOUR\n"

    for author in article.get("authors", []):
        ris += f"AU  - {author}\n"

    title = article.get("title", "")
    if title:
        ris += f"TI  - {title}\n"

    journal = article.get("journal", "")
    if journal:
        ris += f"JO  - {journal}\n"

    year = article.get("year", "")
    if year:
        ris += f"PY  - {year}\n"

    doi = article.get("doi", "")
    if doi:
        ris += f"DO  - {doi}\n"

    pmid = article.get("pmid", "")
    if pmid:
        ris += f"AN  - {pmid}\n"

    link = article.get("link", "")
    if link:
        ris += f"UR  - {link}\n"

    ris += "ER  - \n"

    return ris

def generate_pubmed_citation(article: Dict) -> str:
    """Genera una citación en formato PubMed/NBIB."""
    citation = ""

    pmid = article.get("pmid", "")
    if pmid:
        citation += f"PMID- {pmid}\n"

    for author in article.get("authors", []):
        citation += f"AU  - {author}\n"

    title = article.get("title", "")
    if title:
        citation += f"TI  - {title}\n"

    journal = article.get("journal", "")
    if journal:
        citation += f"TA  - {journal}\n"

    year = article.get("year", "")
    if year:
        citation += f"DP  - {year}\n"

    doi = article.get("doi", "")
    if doi:
        citation += f"AID - {doi} [doi]\n"

    return citation

def main():
    # Cargar mapeo de links
    link_mapping = load_csv_mapping()

    # Cargar dataset
    print(f"[INFO] Loading {INPUT_JSON}...")
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"[INFO] Total articles: {len(dataset)}")

    # Procesar cada artículo
    updated_count = 0
    citation_success = 0
    citation_failed = 0
    checkpoint_interval = 50

    for idx, article in enumerate(dataset):
        # Saltar artículos que ya tienen datos de citaciones (preservar progreso)
        if article.get("citations") and article.get("formatted_citations"):
            continue

        # Manejar caracteres Unicode especiales en títulos para Windows
        safe_title = article.get('title', '')[:60].encode('ascii', 'ignore').decode('ascii')
        print(f"\n[{idx + 1}/{len(dataset)}] Processing: {safe_title}...")

        # 1. Agregar link si no existe
        if not article.get("link"):
            title = article.get("title", "")
            if title in link_mapping:
                article["link"] = link_mapping[title]
                print(f"  [+] Link added")

        # 2. Obtener conteo de citaciones
        pmid = article.get("pmid")
        doi = article.get("doi")

        citations_data = {
            "citation_count": None,
            "influential_citation_count": None,
            "last_updated": datetime.now().isoformat(),
            "source": None
        }

        # Intentar OpenCitations primero
        citation_count = get_citation_count_opencitations(pmid=pmid, doi=doi)
        if citation_count is not None:
            citations_data["citation_count"] = citation_count
            citations_data["source"] = "OpenCitations"
            citation_success += 1
            print(f"  [+] Citations: {citation_count} (OpenCitations)")
        else:
            # Fallback a Semantic Scholar
            semantic_data = get_citation_count_semantic_scholar(pmid=pmid, doi=doi)
            if semantic_data:
                citations_data["citation_count"] = semantic_data.get("citation_count")
                citations_data["influential_citation_count"] = semantic_data.get("influential_citation_count")
                citations_data["source"] = "Semantic Scholar"
                citation_success += 1
                print(f"  [+] Citations: {citations_data['citation_count']} (Semantic Scholar)")
            else:
                citation_failed += 1
                print(f"  [!] No citation data available")

        article["citations"] = citations_data

        # 3. Generar formatos de citación
        formatted_citations = {
            "apa": generate_apa_citation(article),
            "bibtex": generate_bibtex_citation(article),
            "ris": generate_ris_citation(article),
            "pubmed": generate_pubmed_citation(article)
        }

        article["formatted_citations"] = formatted_citations
        print(f"  [+] Citation formats generated")

        updated_count += 1

        # Checkpoint
        if updated_count % checkpoint_interval == 0:
            print(f"\n[SAVE] Checkpoint at {updated_count} updates...")
            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(dataset, f, ensure_ascii=False, indent=2)
            print(f"[OK] Checkpoint saved")

        # Rate limiting (respetar límites de API)
        time.sleep(1.2)  # ~50 req/min para Semantic Scholar

    # Guardar resultado final
    print(f"\n[SAVE] Saving final results to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"COMPLETED!")
    print(f"{'='*60}")
    print(f"Total articles processed: {len(dataset)}")
    print(f"Links added: {updated_count}")
    print(f"Citation data retrieved: {citation_success}")
    print(f"Citation data failed: {citation_failed}")
    print(f"Output saved to: {OUTPUT_JSON}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
