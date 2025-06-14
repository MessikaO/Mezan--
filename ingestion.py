# backend/ingestion.py

import os
import glob # For finding all PDF files in a directory
# dotenv is not strictly needed here if run independently, but good practice
# from dotenv import load_dotenv

# Import PDF and text processing tools
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter # Using base splitter
from typing import List

# LangChain components for embedding and vector store
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings # For local sentence-transformer embeddings
# If using Google Embeddings (requires API key):
# from langchain_google_genai import GoogleGenerativeAIEmbeddings
# import google.generativeai as genai # Needed for Google Embeddings config if not using LangChain wrapper


# --- Configuration ---
# Define paths relative to this script's location or project root
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # Directory of ingestion.py
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..')) # mezan directory (up one level)
RAW_PDFS_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw_pdfs')
VECTOR_STORE_DIR = os.path.join(PROJECT_ROOT, 'data', 'vector_store', 'joradp_chroma_db') # Path for ChromaDB to persist

# Embedding model configuration (using a local sentence-transformer model)
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# ChromaDB collection name
CHROMA_COLLECTION_NAME = "joradp_documents"

# --- PDF Text Extraction Function ---
def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text content from a given PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            num_pages = len(pdf_reader.pages)
            print(f"Reading PDF: {pdf_path} - Found {num_pages} pages.")

            for page_num in range(num_pages):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n" # Add a newline between pages
                else:
                    print(f"Warning: No text extracted from page {page_num + 1} of {pdf_path}")

        print(f"Successfully extracted text from {pdf_path}")
        return text.strip()
    except FileNotFoundError:
        print(f"Error: PDF file not found at {pdf_path}")
        return ""
    except Exception as e:
        print(f"Error extracting text from PDF {pdf_path}: {e}")
        # import traceback; traceback.print_exc() # Uncomment for detailed error
        return ""

# --- Text Cleaning and Chunking Functions ---
def clean_text(text: str) -> str:
    """Basic text cleaning."""
    text = text.replace('\n\n+', '\n') # Replace multiple newlines
    text = text.replace('  +', ' ')   # Replace multiple spaces
    text = "\n".join([line.strip() for line in text.split('\n')]).strip() # Remove leading/trailing whitespace from lines
    # Add more cleaning steps here if needed (e.g., handling ligatures, hyphens)
    return text

def chunk_text_recursive(text: str, chunk_size: int = 1000, chunk_overlap: int = 150) -> List[str]:
    """Splits text into chunks using RecursiveCharacterTextSplitter."""
    if not text:
        return []

    print(f"Chunking text. Original length: {len(text)} chars. Chunk size: {chunk_size}, Overlap: {chunk_overlap}")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        add_start_index=False,
    )
    chunks = text_splitter.split_text(text)
    print(f"Text split into {len(chunks)} chunks.")
    return chunks

# --- Embedding Model Initialization ---
def initialize_embedding_model():
    """Initializes and returns the embedding model."""
    print(f"Initializing embedding model: {EMBEDDING_MODEL_NAME}")
    try:
        # Using a local Sentence Transformer model via HuggingFaceEmbeddings
        # model_kwargs={'device': 'cpu'} ensures it runs on CPU even if GPU is available
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME, model_kwargs={'device': 'cpu'})

        # --- Alternative: Using Google Generative AI Embeddings ---
        # Requires GEMINI_API_KEY in .env and potentially `google.generativeai.configure`
        # Make sure API key is loaded before this.
        # GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        # if not GEMINI_API_KEY:
        #    raise ValueError("GEMINI_API_KEY not found for Google Embeddings.")
        # genai.configure(api_key=GEMINI_API_KEY) # Configure the SDK if not done globally
        # embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001") # Or newer model
        # print("Initialized Google Generative AI Embeddings.")

        print("Embedding model initialized.")
        return embeddings
    except Exception as e:
        print(f"Error initializing embedding model: {e}")
        # import traceback; traceback.print_exc()
        return None # Return None if initialization fails

# --- ChromaDB Vector Store Initialization ---
def initialize_vector_store(embedding_function):
    """Initializes or loads the ChromaDB vector store."""
    print(f"Initializing ChromaDB vector store at: {VECTOR_STORE_DIR}")
    # Ensure the directory exists
    if not os.path.exists(VECTOR_STORE_DIR):
        os.makedirs(VECTOR_STORE_DIR)
        print(f"Created directory: {VECTOR_STORE_DIR}")

    try:
        # Create a persistent ChromaDB client
        # This will create files in the VECTOR_STORE_DIR if they don't exist,
        # or load an existing DB from that path.
        vector_store = Chroma(
            collection_name=CHROMA_COLLECTION_NAME,
            embedding_function=embedding_function, # Must use the same embedding function
            persist_directory=VECTOR_STORE_DIR
        )
        print(f"ChromaDB vector store initialized/loaded. Collection: '{CHROMA_COLLECTION_NAME}'. Documents in collection: {vector_store._collection.count()}")
        if vector_store._collection.count() == 0:
            print("Warning: Vector store is empty. No documents loaded.")
        return vector_store
    except Exception as e:
        print(f"Error initializing/loading vector store: {e}")
        # import traceback; traceback.print_exc()
        return None # Return None if initialization fails


# --- Main Ingestion Process ---
def run_ingestion_pipeline(pdf_directory: str, vector_store: Chroma, embedding_function):
    """
    Processes all PDF files in a directory: extracts text, chunks, embeds, and stores in ChromaDB.
    Checks if a document (by filename) has already been processed to avoid duplicates.
    """
    pdf_files = glob.glob(os.path.join(pdf_directory, "*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {pdf_directory}. Please add JORADP PDFs there.")
        return

    print(f"Found {len(pdf_files)} PDF files to process in {pdf_directory}")

    for pdf_path in pdf_files:
        pdf_filename = os.path.basename(pdf_path)
        print(f"\n--- Processing PDF: {pdf_filename} ---")

        # --- Check if document already processed ---
        # Simple check by filename in metadata. Query for existence.
        try:
            existing_docs = vector_store.get(where={"source": pdf_filename}, include=[]) # Only need IDs or count
            if existing_docs and existing_docs.get('ids') and len(existing_docs['ids']) > 0:
                print(f"Document '{pdf_filename}' seems to be already processed ({len(existing_docs['ids'])} chunks found). Skipping.")
                continue # Skip to the next PDF
            else:
                 print(f"Document '{pdf_filename}' not found in store or has no chunks. Processing.")
        except Exception as e:
             print(f"Error checking existence of '{pdf_filename}' in vector store: {e}. Attempting to re-process.")
             # import traceback; traceback.print_exc() # Uncomment for detailed error
             # Continue processing if check fails


        # 1. Extract Text
        raw_text = extract_text_from_pdf(pdf_path)
        if not raw_text:
            print(f"No text extracted from {pdf_filename}. Skipping.")
            continue

        # 2. Clean Text
        cleaned_text = clean_text(raw_text)
        # print(f"Cleaned text length: {len(cleaned_text)} chars.")

        # 3. Chunk Text
        # Adjust chunk_size and chunk_overlap based on your content and embedding model's preferences
        # Smaller chunks capture more local context but might lose broader context.
        # Overlap helps prevent splitting important sentences/phrases.
        # 1000 chars, 150 overlap is a common starting point.
        text_chunks = chunk_text_recursive(cleaned_text, chunk_size=1000, chunk_overlap=150)
        if not text_chunks:
            print(f"No chunks generated for {pdf_filename}. Skipping.")
            continue

        print(f"Generated {len(text_chunks)} chunks for {pdf_filename}.")

        # 4. Prepare Metadatas for each chunk
        # This helps in filtering or identifying sources later
        metadatas = [{"source": pdf_filename, "chunk_num": i, "category": "General JORADP"} for i in range(len(text_chunks))]
        # You could potentially add category metadata here if you know the PDF's category (e.g., all Civil Law PDFs get category="Civil Law")
        # But for general JORADP, "General JORADP" might be fine.

        # 5. Add Chunks to Vector Store (this also handles embedding)
        # vector_store.add_texts handles embedding the texts using the provided embedding_function
        # and then stores the texts and their embeddings.
        try:
            print(f"Adding {len(text_chunks)} chunks from '{pdf_filename}' to vector store...")
            vector_store.add_texts(texts=text_chunks, metadatas=metadatas)
            # vector_store.persist() # Recent ChromaDB versions auto-persist. This line might give a deprecation warning or not be needed.
            print(f"Successfully added chunks from '{pdf_filename}'.") # Updated message
            print(f"Current total documents in collection '{CHROMA_COLLECTION_NAME}': {vector_store._collection.count()}")
        except Exception as e:
            print(f"Error adding texts from '{pdf_filename}' to vector store: {e}")
            # import traceback; traceback.print_exc()
            # Potentially log which document failed and continue with others


    print("\n--- PDF Processing Complete ---")


if __name__ == "__main__":
    # This block runs when you execute `python backend/ingestion.py`
    print("Starting Data Ingestion Pipeline for Mezan JORADP...")

    # --- IMPORTANT: Place your JORADP PDF files in the 'data/raw_pdfs/' directory ---
    # Ensure the input directory exists
    if not os.path.exists(RAW_PDFS_DIR):
         print(f"Error: The directory {RAW_PDFS_DIR} does not exist.")
         print("Please create this directory and add your JORADP PDF files there.")
         exit(1) # Exit the script if input directory is missing

    # 1. Initialize Embedding Model
    embedding_model = initialize_embedding_model()
    if embedding_model is None:
        print("FATAL: Embedding model could not be initialized. Exiting.")
        exit(1)

    # 2. Initialize Vector Store (Loads existing or creates new)
    db = initialize_vector_store(embedding_function=embedding_model)
    if db is None:
        print("FATAL: Vector store could not be initialized/loaded. Exiting.")
        exit(1)


    # 3. Process and Store PDFs
    run_ingestion_pipeline(RAW_PDFS_DIR, db, embedding_model)

    print("\nData Ingestion Pipeline Finished.")
    print(f"Vector store data is persisted in: {VECTOR_STORE_DIR}")
    print(f"Total documents in collection '{CHROMA_COLLECTION_NAME}': {db._collection.count()}")

    # --- Example: How to query the store directly (for testing) ---
    # You can uncomment this block and run the script again to test retrieval
    # if db._collection.count() > 0:
    #     print("\n--- Example Direct Vector Store Query ---")
    #     query_text = "What are the conditions for obtaining Algerian nationality?"
    #     try:
    #         # k is the number of most similar documents to retrieve
    #         retrieved_docs = db.similarity_search_with_score(query_text, k=2)
    #         print(f"Query: '{query_text}'")
    #         if retrieved_docs:
    #             for i, (doc, score) in enumerate(retrieved_docs):
    #                 print(f"\n[Retrieved Doc {i+1}] Score: {score:.4f}")
    #                 print(f"Source: {doc.metadata.get('source', 'N/A')}, Chunk: {doc.metadata.get('chunk_num', 'N/A')}")
    #                 print(f"Content: {doc.page_content[:300]}...") # Print first 300 chars
    #         else:
    #             print("No relevant documents found in the vector store.")
    #     except Exception as e_query:
    #         print(f"Error during example query: {e_query}")