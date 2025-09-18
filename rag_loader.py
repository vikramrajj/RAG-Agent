# rag_loader.py
import json
import faiss
import os
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')
index = faiss.IndexFlatL2(384)
metadata_store = []

def embed_text(text):
    return model.encode([text])[0]

def load_logs(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        logs = json.load(f)
    for log in logs:
        text = f"{log['title']} {log['symptoms']} {log['fix_steps']}"
        vec = embed_text(text)
        index.add(vec.reshape(1, -1))
        metadata_store.append(log)

def save_index(index_path='outlook_index.faiss'):
    faiss.write_index(index, index_path)
    with open('metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata_store, f, indent=4)

if __name__ == "__main__":
    load_logs("outlook_logs.json")
    save_index()
    print("✅ Logs embedded and index saved.")
