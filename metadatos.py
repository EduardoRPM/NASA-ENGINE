import requests
import re

def get_ids_from_pmc(url: str):
    # Extraer el PMCID de la URL
    match = re.search(r"(PMC\d+)", url)
    if not match:
        raise ValueError("No se encontró PMCID en la URL")
    pmcid = match.group(1)

    # Consultar ID Converter API
    api_url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={pmcid}&format=json"
    resp = requests.get(api_url)
    resp.raise_for_status()

    data = resp.json()
    if "records" not in data or not data["records"]:
        raise ValueError("No se encontraron resultados en el API")

    record = data["records"][0]

    return {
        "pmcid": record.get("pmcid"),
        "pmid": record.get("pmid"),
        "doi": record.get("doi"),
        "status": record.get("status")
    }

# ---------------- Ejemplo de uso ----------------
url = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4136787/"
ids = get_ids_from_pmc(url)
print(ids)
