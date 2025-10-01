import csv
import re
import requests

INPUT_FILE = "/Users/diegopermar/NASA ENGINE/data/SB_publication_PMC.csv"
OUTPUT_FILE = "01_ids.csv"

def extract_pmcid_from_url(url: str) -> str:
    match = re.search(r"(PMC\d+)", url)
    return match.group(1) if match else None

def get_ids_from_pmcid(pmcid: str):
    api_url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?ids={pmcid}&format=json"
    resp = requests.get(api_url)
    resp.raise_for_status()
    data = resp.json()
    if "records" not in data or not data["records"]:
        return {"pmcid": pmcid, "pmid": None, "doi": None}
    record = data["records"][0]
    return {
        "pmcid": record.get("pmcid"),
        "pmid": record.get("pmid"),
        "doi": record.get("doi"),
    }

def main():
    with open(INPUT_FILE, newline="", encoding="utf-8-sig") as infile, \
         open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as outfile:

        reader = csv.DictReader(infile)
        print("Columnas detectadas:", reader.fieldnames)

        fieldnames = ["title", "link", "pmcid", "pmid", "doi"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            # Columnas seguras
            title = row.get("Title") or row.get("title")
            link = row.get("Link") or row.get("link")

            if not title or not link:
                print("⚠️ Fila ignorada (no se encontró Title o Link):", row)
                continue

            pmcid = extract_pmcid_from_url(link)
            if not pmcid:
                print(f"⚠️ No encontré PMCID en {link}")
                continue

            ids = get_ids_from_pmcid(pmcid)

            writer.writerow({
                "title": title.strip(),
                "link": link.strip(),
                "pmcid": ids["pmcid"],
                "pmid": ids["pmid"],
                "doi": ids["doi"]
            })

            print(f"✅ Procesado: {title[:50]}... -> {ids}")

if __name__ == "__main__":
    main()
