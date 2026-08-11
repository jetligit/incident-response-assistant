from sentence_transformers import SentenceTransformer
import chromadb
import os
import collections

_model = None
_collection = None

def create_embeddings():
    # Load the embedding model
    model = SentenceTransformer("BAAI/bge-base-en-v1.5")
    folder_path = "runbooks"

    client = chromadb.PersistentClient(path="chroma_db")    
    collection = client.get_or_create_collection(           
        "runbooks", metadata={"hnsw:space": "cosine"}
    )

    ids, documents, metadatas = [], [], []

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        separator = "##"
        with open(file_path, "r") as r:
            lines = r.readlines()
            file_str = ""
            id_description = []
            severity = ""
            for line in lines:
                if separator in line:
                    file_str += "##"
                    id_description.append(line.lstrip("#").strip())
                elif "**Severity:**" in line: 
                    severity = line.lstrip("#").strip()
                else:
                    file_str += line.strip() + "\n"

            
            splitted = file_str.split("##")
            for i in range(1, len(splitted)): 
                section = id_description[i - 1]

                id = filename + "#" + section
                text = splitted[i]
                metadata = {
                    # fix this 
                    "source_file": filename,
                    "doc_id": id,
                    "section": section,
                    "severity": severity 
                }
                ids.append(id)
                documents.append(text)
                metadatas.append(metadata)

    # accumulate across the loop: ids, documents, metadatas
    embeddings = model.encode(documents, normalize_embeddings=True).tolist()
    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

def _resources():
    global _model, _collection
    if _model is None:
        _model = SentenceTransformer("BAAI/bge-base-en-v1.5")
        client = chromadb.PersistentClient(path="chroma_db")
        _collection = client.get_or_create_collection(
            "runbooks", metadata={"hnsw:space": "cosine"}
        )
    return _model, _collection

def search(query, k=3):
    model, collection = _resources()
    INSTRUCTION = "Represent this sentence for searching relevant passages: "
    q_emb = model.encode(
        INSTRUCTION + query,         
        normalize_embeddings=True,
    ).tolist()
    return collection.query(query_embeddings=[q_emb], n_results=k)


if __name__ == "__main__":
    create_embeddings()




