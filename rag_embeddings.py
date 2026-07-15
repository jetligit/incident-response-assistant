from sentence_transformers import SentenceTransformer
import chromadb
import os

# note: created embedding chunks, now time to continue RAG

def create_embeddings():
    # Load the embedding model
    #model = SentenceTransformer("BAAI/bge-base-en-v1.5")
    folder_path = "runbooks"

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
                    id_description.append(line.split(" ")[1])
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
                chunk = [id, text, metadata]
                print(chunk)


if __name__ == "__main__":
    create_embeddings()




