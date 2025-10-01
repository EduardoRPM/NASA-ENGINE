from sentence_transformers import SentenceTransformer
import json

# cargar modelo
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# cargar dataset
with open("06_dataset_enriched.json", "r") as f:
    papers = json.load(f)

vectors = []
for paper in papers:
    # juntar secciones más útiles
    text = " ".join(paper.get("results", []) + paper.get("conclusions", []))
    
    # generar embedding
    embedding = model.encode(text, convert_to_numpy=True).tolist()
    
    vectors.append({
        "id": paper["pmcid"],
        "vector": embedding,
        "payload": {
            "title": paper["title"],
            "year": paper["year"],
            "authors": paper["authors"],
            "mesh_terms": paper["mesh_terms"],
            "results": paper["results"],
            "conclusions": paper["conclusions"]
        }
    })
