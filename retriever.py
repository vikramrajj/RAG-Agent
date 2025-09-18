# retriever.py
import faiss
import json
from sentence_transformers import SentenceTransformer

# Load model and FAISS index
model = SentenceTransformer('all-MiniLM-L6-v2')
index = faiss.read_index("outlook_index.faiss")

# Load metadata (troubleshooting logs)
with open("metadata.json", "r", encoding="utf-8") as f:
    metadata_store = json.load(f)

def retrieve(query, k=3):
    vec = model.encode([query])[0].reshape(1, -1)
    distances, indices = index.search(vec, k)
    return [metadata_store[i] for i in indices[0]]

if __name__ == "__main__":
    query = "Outlook won't open"
    results = retrieve(query)

    print(f"\n🔍 Query: {query}\n")
    for r in results:
        print(f"🔧 Title: {r['title']}")
        print(f"🧠 Symptoms: {', '.join(r['symptoms'])}")
        print(f"🛠️ Fix Steps:")
        for step in r['fix_steps']:
            print(f"   - {step}")
        print("🧩────────────────────────────\n")
