#%%
from asyncio import sleep
from uuid import uuid4
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.documents import Document
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from dotenv import load_dotenv
load_dotenv()

import getpass
import os

if not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google API key: ")

#%%
# Initialize embeddings model
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# Create vector store with persistence
vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
)

#%%
# Load all markdown files from docs directory
md_files = ["./docs/" + i for i in os.listdir("./docs")]

# Create loaders for each markdown file and load documents
loaders = [
    UnstructuredMarkdownLoader(md_file, strategy="fast").load() 
    for md_file in md_files
]

#%%
# Extract first document from each loader result
docs = [i[0] for i in loaders]

# Generate unique IDs for each document
uuids = [str(uuid4()) for _ in range(len(docs))]


# Add documents to vector store
index=0
while index < len(docs):
    doc = docs[index]
    uid = uuids[index]
    try:
        vector_store.add_documents([doc], ids=[uid])
        index += 1
        
    except Exception as e:
        print(f"Error adding document {uid}: {e}")
        sleep(10)  # Wait before retrying or proceeding
        
print(f"Successfully added {len(docs)} documents to the vector store.")
# %%
