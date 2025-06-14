# backend/rag_service.py

import os
# Load dotenv is needed here if this module is imported early and needs env vars before app.py runs fully
# from dotenv import load_dotenv

# Google AI SDK
from google.generativeai import GenerativeModel, configure as genai_configure
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# LangChain components
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings # Must use the SAME embedding model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda # Add RunnableLambda
from operator import itemgetter # Add itemgetter
from langchain_core.output_parsers import StrOutputParser


# --- Configuration ---
# Load environment variables (assuming .env is in the same directory as this script)
# Adjust path if rag_service is in a subdirectory
ENV_PATH = os.path.join(os.path.dirname(__file__), '.env') # Path to backend/.env
# load_dotenv(dotenv_path=ENV_PATH) # This might already be loaded by app.py

# Define paths relative to this script's location or project root
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # Directory of rag_service.py
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..')) # mezan directory (up one level)
VECTOR_STORE_DIR = os.path.join(PROJECT_ROOT, 'data', 'vector_store', 'joradp_chroma_db') # Path where ChromaDB persisted

# Embedding model configuration (must use the SAME model name and parameters as ingestion)
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# ChromaDB collection name (must use the SAME name as ingestion)
CHROMA_COLLECTION_NAME = "joradp_documents"

# Gemini LLM model name
GEMINI_LLM_MODEL_NAME = "gemini-2.0-flash" # Or "gemini-1.5-flash-latest", or whatever worked


# --- Global Variables for Initialized Components (Load once) ---
embedding_model = None
vector_store = None # This will be the loaded vector store
llm_model_instance = None


def initialize_rag_components():
    """Initializes embedding model (for querying), loads vector store, and initializes LLM."""
    global embedding_model, vector_store, llm_model_instance

    # 1. Initialize Embedding Model (MUST BE THE SAME MODEL/PARAMS AS INGESTION)
    if embedding_model is None:
        print(f"RAG Service: Initializing embedding model for querying: {EMBEDDING_MODEL_NAME}")
        try:
            embedding_model = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL_NAME,
                model_kwargs={'device': 'cpu'} # Use CPU device consistently
            )
            print("RAG Service: Embedding model initialized.")
        except Exception as e:
            print(f"RAG Service: Error initializing embedding model: {e}")
            import traceback; traceback.print_exc()
            embedding_model = None


    # 2. Load Vector Store (Loads the data persisted by ingestion.py)
    if vector_store is None and embedding_model is not None:
        print(f"RAG Service: Loading ChromaDB vector store from: {VECTOR_STORE_DIR}")
        if not os.path.exists(VECTOR_STORE_DIR):
            print(f"Error: Vector store directory not found: {VECTOR_STORE_DIR}. Please run ingestion.py first.")
            vector_store = None # Ensure it's None if directory is missing
            return # Cannot load if directory doesn't exist

        try:
            # Load the existing ChromaDB from the persistence directory
            vector_store = Chroma(
                collection_name=CHROMA_COLLECTION_NAME,
                embedding_function=embedding_model, # Must use the SAME embedding function for querying
                persist_directory=VECTOR_STORE_DIR
            )
            print(f"RAG Service: ChromaDB loaded. Collection: '{CHROMA_COLLECTION_NAME}'. Documents in collection: {vector_store._collection.count()}")
            if vector_store._collection.count() == 0:
                print("Warning: Loaded vector store is empty. RAG will not find any relevant documents. Please run ingestion.py.")
        except Exception as e:
            print(f"RAG Service: Error loading vector store: {e}")
            import traceback; traceback.print_exc()
            vector_store = None


    # 3. Initialize LLM (Gemini) - Same as in the previous app.py
    if llm_model_instance is None:
        # Need to ensure GEMINI_API_KEY is available in environment variables
        # It should be loaded by app.py's dotenv, but can be reloaded here if needed
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            print("RAG Service: GEMINI_API_KEY not found in environment. LLM will NOT be initialized.")
            llm_model_instance = None # Explicitly set to None
            return
        try:
            print(f"RAG Service: Initializing Gemini LLM: {GEMINI_LLM_MODEL_NAME}")
            genai_configure(api_key=GEMINI_API_KEY) # Configure the SDK

            # Using GenerativeModel from the direct SDK
            llm_model_instance = GenerativeModel(
                 model_name=GEMINI_LLM_MODEL_NAME,
                 safety_settings=[
                    {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                    {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                    {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                    {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                ],
                 generation_config={"temperature": 0.3} # Set temperature here
            )
            print("RAG Service: Gemini LLM initialized successfully.")
        except Exception as e:
            print(f"RAG Service: Error initializing Gemini LLM: {e}")
            import traceback; traceback.print_exc()
            llm_model_instance = None


# --- Call initialization when this module is loaded by app.py ---
initialize_rag_components()


def format_docs_for_prompt(docs: list) -> str:
    """Helper function to format retrieved documents (list of Document objects) for the prompt."""
    if not docs:
        return "No relevant information found in the knowledge base for this query."
    # Concatenate the page_content of each document, adding source metadata
    # doc.page_content is the text, doc.metadata is a dictionary
    return "\n\n".join([f"--- Context Snippet from JORADP (Source: {doc.metadata.get('source', 'N/A')}, Chunk: {doc.metadata.get('chunk_num', 'N/A')}) ---\n{doc.page_content}" for doc in docs])


def get_rag_response(user_message: str, category: str) -> str:
    """
    Performs RAG:
    1. Receives user message and category.
    2. Retrieves relevant contexts from the loaded vector store based on the user message.
    3. Constructs an augmented prompt using the user message and retrieved contexts.
    4. Calls the LLM (Gemini) with the augmented prompt.
    5. Returns the LLM's response text.
    """
    print(f"RAG Service: Received query for category '{category}': '{user_message}'")

    # --- Check if components are initialized before proceeding ---
    if vector_store is None:
        print("Error: Vector store not loaded. Cannot perform RAG retrieval.")
        return "Apologies, the knowledge base is currently unavailable. Please ensure ingestion.py was run successfully."
    if llm_model_instance is None:
        print("Error: LLM instance not initialized. Cannot generate AI response.")
        return "Apologies, the AI language model is currently unavailable. Please check backend configuration."
    if embedding_model is None:
         print("Error: Embedding model not initialized. Cannot perform RAG retrieval.")
         return "Apologies, a critical component for understanding your query is unavailable."

    try:
        # --- 1. Retrieve relevant documents (contexts) ---
        # Use the loaded vector store's retriever.
        # LangChain's retriever.invoke() will use the associated embedding function
        # to embed the user_message and perform the similarity search.
        # k=3 means retrieve the top 3 most similar document chunks.
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})

        print(f"RAG Service: Retrieving documents for query: '{user_message[:50]}...'")
        # The retriever.invoke method takes the query string as input.
        retrieved_docs = retriever.invoke(user_message)

        print(f"RAG Service: Retrieved {len(retrieved_docs)} documents.")
        # Debug: print(f"Retrieved Docs: {retrieved_docs}") # Uncomment to see retrieved content

        # --- 2. Format the retrieved documents for the prompt ---
        context_text = format_docs_for_prompt(retrieved_docs)
        # Debug: print(f"Formatted Context: {context_text[:300]}...") # Uncomment to see formatted context snippet


        # --- 3. Construct the Augmented Prompt ---
        # This prompt template structure guides the AI using the retrieved context.
        # It's similar to before, but now the {context} placeholder is populated by RAG.
        template = """
        **Role:** You are Mezan, a helpful AI assistant providing *general informational guidance* on Algerian law, operating as part of a university project MVP.
        Your responses are based *primarily* on the "Context Snippets from JORADP" provided below, which come from processed Algerian Official Journal documents.

        **Context Snippets from JORADP:**
        {context}

        **User's Question related to the legal category "{category}":**
        {question}

        **Task:**
        1. Carefully review the "Context Snippets from JORADP".
        2. Based *only* on the information found in these snippets, provide a clear, concise, and *general informational* answer to the user's question.
        3. If the provided snippets do not contain enough information to directly answer the question, state that the specific detail is not found in the *available documents* and provide any *general information* you can based on *relevant parts* of the snippets, or state you cannot answer based on the provided context. Do not invent information outside the snippets.
        4. RESPOND IN THE SAME LANGUAGE AS THE USER'S QUESTION.
        5. **Crucially, DO NOT give specific legal advice, predict legal outcomes, or tell the user what they *should* do in their personal situation.** Frame answers as general possibilities, common procedures, or what the *provided context* indicates the law generally states.
        6. **ALWAYS include the following disclaimer VERBATIM at the end of your response, on a new line:**
           "--- Disclaimer: This information is for general educational purposes only based on Algerian law and is not a substitute for professional legal advice. Laws can change, and individual situations vary. You should consult a qualified Algerian lawyer for advice tailored to your specific circumstances. ---"

        **Constraints:**
        * Keep the response informative but relatively brief for a chat context.
        * Adhere to your safety settings.
        * Strictly base answers on the provided "Context Snippets from JORADP".

        **Answer:**
        """
        # Create a ChatPromptTemplate instance
        prompt_template = ChatPromptTemplate.from_template(template)

        # Format the prompt with the retrieved context, user question, and category
        # Note: llm_model_instance.generate_content expects a list of messages or a string.
        # We'll format the prompt template output into a string message for the LLM.
        # The prompt template format will create a list of ChatMessage objects or a string depending on LangChain version.
        # Let's make it simpler for direct SDK call and format it into a single string prompt.

        # Create the final prompt string
        final_prompt_string = template.format(
            context=context_text,
            category=category,
            question=user_message
        )

        print(f"RAG Service: Sending augmented prompt to Gemini: {final_prompt_string[:300]}...")


        # --- 4. Call the LLM (Gemini) with the augmented prompt ---
        # Use the direct SDK call
        response = llm_model_instance.generate_content(final_prompt_string)

        # Extract the text response - Handle different response structures and blocks
        reply_text = ""
        if response and hasattr(response, 'text') and response.text:
            reply_text = response.text
        elif response and response.parts:
             for part in response.parts:
                 if hasattr(part, 'text') and part.text:
                     reply_text += part.text
        # Handle blocked content
        if not reply_text and response and response.prompt_feedback and response.prompt_feedback.block_reason:
             block_reason_message = response.prompt_feedback.block_reason_message or "Content blocked by safety filters."
             print(f"RAG Service: Gemini response blocked. Reason: {response.prompt_feedback.block_reason}, Message: {block_reason_message}")
             # Return a specific message if blocked
             return f"Sorry, I couldn't generate a response for that request. {block_reason_message} Please try rephrasing your question."
        elif not reply_text:
            # Handle empty response that wasn't explicitly blocked
            print("RAG Service: Gemini response was empty or format not recognized.")
            # Debug: print(f"Full Gemini response object: {response}")
            return "Sorry, I received an unexpected empty response from the AI. Please try again."


        print(f"RAG Service: Gemini generated text: {reply_text[:100]}...")
        return reply_text # Return the final response text

    except Exception as e:
        print(f"Error during RAG process in rag_service: {e}")
        import traceback; traceback.print_exc()
        # Return a generic error message if RAG process fails
        return "Sorry, I encountered an error while processing your request with the knowledge base."