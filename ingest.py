import os
import glob
from dotenv import load_dotenv

# LangChain components for document loading, splitting, and vector storage
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

def main():
    print("\n🚀 Starting Data Ingestion Process...")
    
    # 1. Load environment variables
    load_dotenv()
    
    data_dir = "data"
    
    # Check if data directory exists and create it if not
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"⚠️ Created '{data_dir}/' folder. Please add your medical PDFs to this folder and run again.")
        return
        
    # Get all PDF files in the data directory recursively
    pdf_files = glob.glob(os.path.join(data_dir, "**", "*.pdf"), recursive=True)
    if not pdf_files:
        print(f"⚠️ No PDF files found in '{data_dir}/'. Please add some PDFs and run again.")
        return
        
    print(f"📂 Found {len(pdf_files)} PDF file(s) in '{data_dir}/'")
    
    # 2. Iterate through each PDF and load its text content
    documents = []
    for pdf_file in pdf_files:
        print(f"📄 Loading: {pdf_file}...")
        try:
            # PyPDFLoader extracts text and metadata (like page numbers) from PDFs
            loader = PyPDFLoader(pdf_file)
            docs = loader.load()
            documents.extend(docs)
            print(f"   ✅ Successfully loaded {len(docs)} pages from {os.path.basename(pdf_file)}")
        except Exception as e:
            print(f"   ❌ Error loading {pdf_file}: {e}")
            
    if not documents:
        print("\n⚠️ No content could be extracted from the PDFs.")
        print("💡 NOTE: If your PDFs are scanned images, PyPDFLoader won't work because it only extracts text.")
        print("For scanned images, you will need an OCR (Optical Character Recognition) loader like UnstructuredPDFLoader.")
        return
        
    # 3. Split the loaded documents into overlapping chunks
    print(f"\n✂️ Splitting {len(documents)} pages into smaller text chunks...")
    # We use a chunk size of 500 characters with an overlap of 50 characters to preserve context between chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len
    )
    chunks = text_splitter.split_documents(documents)
    print(f"   ✅ Created {len(chunks)} text chunks.")
    
    # 4. Initialize HuggingFace embeddings model
    print("\n🧠 Initializing HuggingFace Embeddings Model (all-MiniLM-L6-v2)...")
    print("   (This runs locally on your CPU and is 100% free. It might take a moment to download the first time.)")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'} # Explicitly force it to run on CPU
    )
    
    # 5. Generate vector embeddings and store them in a FAISS index
    print("\n📊 Generating embeddings and building FAISS vector index...")
    print("   (This step might take a few minutes depending on the size and amount of your PDFs.)")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    
    # 6. Save the FAISS index to disk so it can be reloaded without rebuilding
    vectorstore_dir = "vectorstore"
    print(f"\n💾 Saving FAISS vector index to the '{vectorstore_dir}/' folder...")
    vectorstore.save_local(vectorstore_dir)
    
    print("\n🎉 Ingestion complete! Your local medical knowledge base has been built successfully.")

if __name__ == "__main__":
    main()
