import csv
import requests
from bs4 import BeautifulSoup
import time
import json
from typing import List, Optional

INPUT_CSV = "data/SB_publication_PMC.csv"
INPUT_JSON = "06_dataset_enriched.json"
OUTPUT_JSON = "08_dataset_with_abstracts.json"

def extract_pmcid_from_url(url: str) -> Optional[str]:
    """Extrae el PMCID de una URL de PMC."""
    # Formato esperado: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4136787/
    if "PMC" in url:
        parts = url.split("PMC")
        if len(parts) > 1:
            pmcid = "PMC" + parts[1].rstrip("/")
            return pmcid
    return None

def is_unwanted_content(text: str) -> bool:
    """Verifica si el texto es contenido no deseado en el abstract."""
    unwanted_patterns = [
        "video abstract",
        "graphical abstract",
        "audio abstract",
        "supplementary",
        "click here",
        "download",
        "available online"
    ]
    text_lower = text.lower().strip()

    # Filtrar párrafos muy cortos que probablemente sean títulos/labels
    if len(text_lower) < 10:
        return True

    # Filtrar patrones no deseados
    for pattern in unwanted_patterns:
        if pattern in text_lower:
            return True

    return False

def fetch_abstract_from_pmc(pmcid: str) -> List[str]:
    """
    Obtiene el abstract de un artículo de PMC usando la API de EuropePMC.
    Retorna una lista de párrafos del abstract, filtrando contenido no deseado.
    """
    url_xml = f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML"

    try:
        resp = requests.get(url_xml, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "lxml-xml")

            # Buscar la sección de abstract
            abstract_section = soup.find("abstract")

            if abstract_section:
                # Extraer todos los párrafos del abstract
                abstract_paragraphs = []

                # Buscar todos los elementos <p> dentro del abstract
                for p in abstract_section.find_all("p"):
                    text = p.get_text(" ", strip=True)
                    if text and not is_unwanted_content(text):
                        abstract_paragraphs.append(text)

                # Si no hay <p>, intentar obtener todo el texto del abstract
                if not abstract_paragraphs:
                    text = abstract_section.get_text(" ", strip=True)
                    if text and not is_unwanted_content(text):
                        abstract_paragraphs.append(text)

                return abstract_paragraphs

            # Si no hay abstract en el XML, intentar con sec que tenga title="Abstract"
            for sec in soup.find_all("sec"):
                title_tag = sec.find("title")
                if title_tag and "abstract" in title_tag.get_text().lower():
                    paragraphs = []
                    for p in sec.find_all("p"):
                        text = p.get_text(" ", strip=True)
                        if text and not is_unwanted_content(text):
                            paragraphs.append(text)
                    if paragraphs:
                        return paragraphs

        return []

    except Exception as e:
        print(f"  [!] Error fetching abstract for {pmcid}: {e}")
        return []

def load_csv_mapping():
    """Carga el CSV y crea un diccionario de título -> URL."""
    mapping = {}

    with open(INPUT_CSV, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            title = row.get("Title", "").strip()
            link = row.get("Link", "").strip()
            if title and link:
                mapping[title] = link

    print(f"[INFO] Loaded {len(mapping)} articles from CSV")
    return mapping

def main():
    # Cargar el mapeo de título -> URL
    url_mapping = load_csv_mapping()

    # Cargar el JSON enriquecido
    print(f"[INFO] Loading {INPUT_JSON}...")
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    print(f"[INFO] Total articles in dataset: {len(dataset)}")

    # Contar artículos con abstract vacío
    articles_without_abstract = [art for art in dataset if not art.get("abstract")]
    print(f"[INFO] Articles with empty abstract: {len(articles_without_abstract)}")

    # Procesar artículos
    updated_count = 0
    failed_count = 0
    checkpoint_interval = 50

    for idx, article in enumerate(dataset):
        # Saltar si ya tiene abstract
        if article.get("abstract"):
            continue

        title = article.get("title", "")
        pmcid = article.get("pmcid", "")

        # Intentar obtener PMCID si no está presente
        if not pmcid and title in url_mapping:
            url = url_mapping[title]
            pmcid = extract_pmcid_from_url(url)
            if pmcid:
                article["pmcid"] = pmcid

        if not pmcid:
            print(f"  [!] No PMCID found for: {title[:60]}...")
            failed_count += 1
            continue

        print(f"\n[{idx + 1}/{len(dataset)}] Fetching abstract for {pmcid}...")
        # Manejar caracteres especiales en Windows
        safe_title = title[:60].encode('ascii', 'ignore').decode('ascii')
        print(f"  Title: {safe_title}...")

        # Obtener el abstract
        abstract_paragraphs = fetch_abstract_from_pmc(pmcid)

        if abstract_paragraphs:
            article["abstract"] = abstract_paragraphs
            updated_count += 1
            print(f"  [OK] Abstract extracted ({len(abstract_paragraphs)} paragraphs)")
        else:
            print(f"  [!] No abstract found")
            failed_count += 1

        # Guardar checkpoint cada N artículos
        if (updated_count > 0) and (updated_count % checkpoint_interval == 0):
            print(f"\n[SAVE] Checkpoint at {updated_count} updates...")
            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(dataset, f, ensure_ascii=False, indent=2)
            print(f"[OK] Checkpoint saved")

        # Respetar rate limiting
        time.sleep(0.5)

    # Guardar resultado final
    print(f"\n[SAVE] Saving final results to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"COMPLETED!")
    print(f"{'='*60}")
    print(f"Total articles processed: {len(dataset)}")
    print(f"Abstracts added: {updated_count}")
    print(f"Failed/No abstract: {failed_count}")
    print(f"Output saved to: {OUTPUT_JSON}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
