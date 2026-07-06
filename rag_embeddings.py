from sentence_transformers import SentenceTransformer
import chromadb
import os

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
            for line in lines:
                if separator in line:
                    file_str += "##"
                else:
                    file_str += line.strip()

            
            splitted = file_str.split("##")
            for i in range(1, len(splitted)):
                # fix this 
                id = filename
                text = splitted[i]
                metadata = {
                    # fix this 
                    "doc_id": id,
                    "section":
                }
                print(splitted[i] + "\n")


if __name__ == "__main__":
    create_embeddings()




