# backend/rag_service.py

import os
# load_dotenv is typically called in the main app file (app.py)
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
# Define paths relative to this script's location or project root
# Assumes this file is in the 'backend' directory
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__)) # Directory of rag_service.py
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..')) # mezan directory (up one level)
VECTOR_STORE_DIR = os.path.join(PROJECT_ROOT, 'data', 'vector_store', 'joradp_chroma_db') # Path where ChromaDB persisted

# Embedding model configuration (must use the SAME model name and parameters as ingestion)
EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2" # Using improved model

# ChromaDB collection name (must use the SAME name as ingestion)
CHROMA_COLLECTION_NAME = "joradp_documents"

# Gemini LLM model name (use the one that successfully initialized)
GEMINI_LLM_MODEL_NAME = "gemini-2.0-flash"


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
            # Using a local Sentence Transformer model via HuggingFaceEmbeddings
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
            # Do NOT return here, let LLM initialize even if vector store isn't found
        else: # Only load if directory exists
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


    # 3. Initialize LLM (Gemini)
    if llm_model_instance is None:
        # Need to ensure GEMINI_API_KEY is available in environment variables
        # It should be loaded by app.py's dotenv.
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            print("RAG Service: GEMINI_API_KEY not found in environment. LLM will NOT be initialized.")
            llm_model_instance = None # Explicitly set to None
            # Do NOT return here, let the function run and return an error message
        else: # Only initialize if API key is found
            try:
                print(f"RAG Service: Initializing Gemini LLM: {GEMINI_LLM_MODEL_NAME}")
                genai_configure(api_key=GEMINI_API_KEY) # Configure the SDK

                # Using GenerativeModel from the direct SDK
                llm_model_instance = GenerativeModel(
                     model_name=GEMINI_LLM_MODEL_NAME,
                     safety_settings=[ # Keep basic safety settings
                        {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                        {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                        {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                        {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},
                    ],
                     generation_config={"temperature": 0.5} # Slightly increase temperature maybe? Or keep at 0.3
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
        # This case should ideally be handled by the prompt instructions if context is empty
        return "No relevant context snippets were retrieved."
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

    # --- Check if essential components are initialized before proceeding ---
    if vector_store is None or embedding_model is None:
         print("Error: Vector store or embedding model not initialized. Cannot perform RAG retrieval.")
         # Return a specific error message indicating ingestion failure
         return "Apologies, the legal knowledge base is not fully loaded. Please contact support or try again later."

    if llm_model_instance is None:
        print("Error: LLM instance not initialized. Cannot generate AI response.")
        # Return a specific error message indicating LLM failure
        return "Apologies, the AI language model is currently unavailable. Please check backend configuration."


    try:
        # --- 1. Retrieve relevant documents (contexts) ---
        # Use the loaded vector store's retriever.
        # LangChain's retriever.invoke() will use the associated embedding function
        # to embed the user_message and perform the similarity search.
        # k=10 is used to retrieve the top 10 most similar document chunks.
        retriever = vector_store.as_retriever(search_kwargs={"k": 10}) # Using k=10

        print(f"RAG Service: Retrieving documents for query: '{user_message[:50]}...'")
        # The retriever.invoke method takes the query string as input.
        retrieved_docs = retriever.invoke(user_message)

        print(f"RAG Service: Retrieved {len(retrieved_docs)} documents.")
        # Debug: print(f"Retrieved Docs: {retrieved_docs}") # Uncomment to see retrieved content


        # --- 2. Format the retrieved documents for the prompt ---
        # The format_docs_for_prompt function prepares the retrieved documents into a string.
        context_text = format_docs_for_prompt(retrieved_docs)
        # Debug: print(f"Formatted Context: {context_text[:300]}...") # Uncomment to see formatted context snippet


        # --- 3. Construct the Augmented Prompt ---
        # This prompt template guides the AI using the retrieved context AND its general knowledge.
        template = """
         **Role:** You are Mezan, a helpful AI assistant providing guidance and information on Algerian law. You are part of a university project.

        **Your Knowledge Sources:**
        - "Context Snippets from JORADP" provided below (from processed Algerian Official Journal documents).
        - Your inherent general knowledge about law and Algeria.

        **Context Snippets from JORADP:**
        {context}

        **User's Question related to the legal category "{category}":**
        {question}

        **Task:**
        1. Analyze the user's question and the provided "Context Snippets from JORADP".
        2. Provide a clear, concise answer and accurate answer.
        3. **If the "Context Snippets" are relevant and sufficient, base your answer *solely* on them.** Quote or reference them where appropriate. Do NOT paraphrase if quoting directly is possible and relevant.
        4. **If the "Context Snippets" are not relevant, are insufficient, or do not contain the specific answer:**
           a. Explicitly state that the answer was not found in the provided documents (e.g., "Based on the available documents, I couldn't find information on...").
           b. Then, **use your general knowledge about law and Algeria** to provide, relevant information that might help the user understand the topic. Ensure this general information is distinct from information found in the snippets.
        5. RESPOND IN THE SAME LANGUAGE AS THE USER'S QUESTION, AND **ENSURE THE WRITING (especially Arabic) IS CORRECT, CLEAR, AND HAS NO TYPOS.**
        6. Aim to provide guidance relevant to Algerian law, indicating potential legal validity or next steps based on the information available (from snippets or general knowledge).

        **Constraints:**
        * Keep the response informative and relevant to legal principles.
        * Adhere to your safety settings.
        * Pay close attention to Arabic grammar, spelling, and correct character usage.
        * **Do NOT invent information.** If neither snippets nor general knowledge can provide relevant information, state that you cannot answer based on the current query or knowledge.

        **Answer:**
        """
        # Create a ChatPromptTemplate instance
        prompt_template = ChatPromptTemplate.from_template(template)

        # Format the prompt with the retrieved context, user question, and category
        # We format the prompt into a single string message for the LLM direct call.
        final_prompt_string = template.format(
            context=context_text, # Populated by RAG
            category=category,    # From frontend input
            question=user_message # From frontend input
        )

        print(f"RAG Service: Sending augmented prompt to Gemini: {final_prompt_string[:500]}...") # Log larger snippet


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
            # Provide a fallback message if AI returns empty
            return "Apologies, I couldn't generate a meaningful response based on your query and the available information."


        print(f"RAG Service: Gemini generated text: {reply_text[:200]}...") # Log larger snippet
        return reply_text # Return the final response text

    except Exception as e:
        print(f"Error during RAG process in rag_service: {e}")
        import traceback; traceback.print_exc()
        # Return a generic error message if RAG process fails
        return "Sorry, I encountered an error while processing your request with the knowledge base."
