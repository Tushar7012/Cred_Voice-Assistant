import os
import json
import faiss
from sentence_transformers import SentenceTransformer


# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "faiss.index")
DOCS_PATH = os.path.join(BASE_DIR, "documents.json")


# -----------------------------
# Government Scheme Knowledge
# (You can expand this later)
# -----------------------------
documents = [
    "प्रधानमंत्री आवास योजना गरीब नागरिकों को पक्का घर प्रदान करने के लिए बनाई गई है। पात्र परिवारों को आर्थिक सहायता दी जाती है।",

    "प्रधानमंत्री किसान सम्मान निधि योजना के तहत किसानों को हर साल 6000 रुपये की आर्थिक सहायता दी जाती है।",

    "आयुष्मान भारत योजना के अंतर्गत गरीब परिवारों को 5 लाख रुपये तक का मुफ्त स्वास्थ्य बीमा मिलता है।",

    "उज्ज्वला योजना का उद्देश्य महिलाओं को मुफ्त एलपीजी गैस कनेक्शन प्रदान करना है।",

    "महाराष्ट्र में मुख्यमंत्री माझी लाडकी बहिण योजना महिलाओं को आर्थिक सहायता देती है।",

    "ओडिशा सरकार की कालिया योजना किसानों और कृषि श्रमिकों के लिए वित्तीय सहायता प्रदान करती है।",

    "बंगाल सरकार की स्वास्थ्य साथी योजना राज्य के नागरिकों को स्वास्थ्य बीमा देती है।"
]


# -----------------------------
# Save documents
# -----------------------------
with open(DOCS_PATH, "w", encoding="utf-8") as f:
    json.dump(documents, f, ensure_ascii=False, indent=2)


# -----------------------------
# Build embeddings
# -----------------------------
print("🔹 Loading embedding model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("🔹 Creating embeddings...")
embeddings = model.encode(documents, show_progress_bar=True)


# -----------------------------
# Create FAISS index
# -----------------------------
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(embeddings)

# -----------------------------
# Save FAISS index
# -----------------------------
faiss.write_index(index, INDEX_PATH)

print("✅ FAISS index created successfully!")
print(f"📄 Documents saved at: {DOCS_PATH}")
print(f"📦 Index saved at: {INDEX_PATH}")
