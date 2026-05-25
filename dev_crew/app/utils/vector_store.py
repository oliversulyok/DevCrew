import os
import hashlib
import json
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
    except ImportError:
        class RecursiveCharacterTextSplitter:
            def __init__(self, chunk_size=1000, chunk_overlap=150):
                self.chunk_size = chunk_size
                self.chunk_overlap = chunk_overlap
            def split_text(self, text):
                chunks = []
                start = 0
                while start < len(text):
                    end = min(start + self.chunk_size, len(text))
                    chunks.append(text[start:end])
                    start += self.chunk_size - self.chunk_overlap
                return chunks

_embeddings_instance = None

def get_embeddings():
    """Initializes and caches the local HuggingFace embeddings model."""
    global _embeddings_instance
    if _embeddings_instance is None:
        # Using a small, efficient local embedding model (~120MB)
        # It runs on CPU/GPU and downloads automatically on first execution.
        _embeddings_instance = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return _embeddings_instance

def get_chroma_db(project_dir):
    """Returns a local ChromaDB instance isolated for the given project directory."""
    db_path = os.path.join(project_dir, "chroma_db")
    return Chroma(persist_directory=db_path, embedding_function=get_embeddings())

def sync_project_files(project_dir):
    """Synchronizes files in docs/, spec/, src/, and test/ with the local ChromaDB database.
    Only processes files that are new or have changed (based on MD5 hash).
    """
    print("\n🔄 Szinkronizáció a helyi vektor-adatbázissal...")
    
    state_file = os.path.join(project_dir, "indexing_state.json")
    state = {}
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}
            
    current_files = {}
    target_dirs = ["spec", "src", "test", "docs"]
    
    # 1. Scan directory for current files
    for dir_name in target_dirs:
        dir_path = os.path.join(project_dir, dir_name)
        if os.path.exists(dir_path):
            for root, _, files in os.walk(dir_path):
                # Prevent indexing the DB files itself
                if "chroma_db" in root:
                    continue
                for file in files:
                    # Ignore non-text files or specific state files
                    if file in ["indexing_state.json", "summary.json", "last_goal.txt"]:
                        continue
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, project_dir)
                    try:
                        mtime = os.path.getmtime(full_path)
                        with open(full_path, "rb") as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                        current_files[rel_path] = {
                            "full_path": full_path,
                            "rel_path": rel_path,
                            "type": dir_name,
                            "mtime": mtime,
                            "hash": file_hash
                        }
                    except Exception:
                        pass

    # Initialize the local db
    db = get_chroma_db(project_dir)
    
    # 2. Check for deleted files
    deleted_files = []
    for rel_path in list(state.keys()):
        if rel_path not in current_files:
            deleted_files.append(rel_path)
            
    for rel_path in deleted_files:
        print(f" 🗑️ Fájl törölve a vektor-adatbázisból: {rel_path}")
        try:
            db.delete(where={"source": rel_path})
        except Exception:
            pass
        del state[rel_path]

    # 3. Check for new or modified files
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    
    for rel_path, info in current_files.items():
        old_info = state.get(rel_path)
        if old_info is None or old_info.get("hash") != info["hash"]:
            action = "Frissítés" if old_info else "Új fájl"
            print(f" 📂 {action} a vektor-adatbázisban: {rel_path}")
            
            # Remove old chunks first if it's an update
            if old_info:
                try:
                    db.delete(where={"source": rel_path})
                except Exception:
                    pass
            
            try:
                # Read content
                with open(info["full_path"], "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Split content into chunks
                chunks = text_splitter.split_text(content)
                
                if chunks:
                    docs = [
                        Document(
                            page_content=chunk,
                            metadata={"source": rel_path, "type": info["type"]}
                        )
                        for chunk in chunks
                    ]
                    db.add_documents(docs)
                
                # Update tracking state
                state[rel_path] = {
                    "mtime": info["mtime"],
                    "hash": info["hash"]
                }
            except Exception as e:
                print(f" ❌ Hiba a fájl feldolgozása közben ({rel_path}): {e}")

    # 4. Save tracking state to json
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)
    except Exception as e:
        print(f" ❌ Nem sikerült menteni a szinkronizációs állapotot: {e}")
