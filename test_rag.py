import os
from dotenv import load_dotenv

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def main():
    print("\n🚀 Starting RAG Retrieval Test...")
    
    # 1. Load environment variables
    load_dotenv()
    
    vectorstore_dir = "vectorstore"
    if not os.path.exists(vectorstore_dir):
        print(f"❌ Error: Vector store not found in '{vectorstore_dir}/'. Please run ingest.py first.")
        return
        
    # 2. Initialize the SAME HuggingFace embeddings model used during ingestion
    print("\n🧠 Initializing HuggingFace Embeddings Model (all-MiniLM-L6-v2) on CPU...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    # 3. Load the saved FAISS index from disk
    print(f"\n📂 Loading FAISS vector index from '{vectorstore_dir}/'...")
    try:
        # allow_dangerous_deserialization=True is required to load FAISS indices saved locally in recent versions
        vectorstore = FAISS.load_local(vectorstore_dir, embeddings, allow_dangerous_deserialization=True)
        print("   ✅ Vector index loaded successfully.")
    except Exception as e:
        print(f"   ❌ Error loading vector index: {e}")
        return
        
    # 4. Hardcode a medical test query
    query = "What are the symptoms of Type 2 diabetes?"
    print(f"\n❓ Test Query: '{query}'")
    
    # 5. Run a similarity search against the FAISS index
    print("🔍 Searching the vector store for the most relevant information...")
    # Retrieve the top 3 most relevant chunks (k=3)
    k = 3
    results = vectorstore.similarity_search(query, k=k)
    
    # 6. Print the results
    print(f"\n🎯 --- Top {len(results)} Most Relevant Document Chunks ---\n")
    for i, doc in enumerate(results, 1):
        # Extract metadata
        source_path = doc.metadata.get('source', 'Unknown source')
        filename = os.path.basename(source_path)
        page = doc.metadata.get('page', 'Unknown')
        
        # In PyPDFLoader, pages are 0-indexed, so we add 1 for human readability
        page_num = page + 1 if isinstance(page, int) else page
        
        print(f"📄 Result {i} (Source: '{filename}', Page: {page_num})")
        print("-" * 60)
        print(doc.page_content.strip())
        print("-" * 60 + "\n")
        
    print("🎉 RAG Retrieval Test complete!")

if __name__ == "__main__":
    main()
