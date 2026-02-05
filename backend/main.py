from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

from rag_engine import RAGEngine


# Charger les variables d'environnement
load_dotenv()

# CONFIGURATION FASTAPI

app = FastAPI(
    title="AI Doc Assistant API",
    description="API RAG avec Claude (Anthropic)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instance globale du RAG Engine
rag: Optional[RAGEngine] = None

# Chemin du dossier data
DATA_FOLDER = "../data"

# MODÈLES PYDANTIC

class ChatRequest(BaseModel):
    query: str
    use_rag: bool = True


class ChatResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class UploadResponse(BaseModel):
    success: bool
    message: str
    chunks_created: Optional[int] = None
    error: Optional[str] = None

# FONCTIONS UTILITAIRES

def load_documents_from_folder(rag_engine: RAGEngine, folder_path: str = DATA_FOLDER) -> dict:
    """
    Charge tous les fichiers .txt et .md du dossier spécifié.
    """
    stats = {
        "files_loaded": 0,
        "files_failed": 0,
        "total_chunks": 0,
        "files": []
    }

    if not os.path.exists(folder_path):
        print(f"📁 Création du dossier {folder_path}/")
        os.makedirs(folder_path)
        return stats
    
    supported_extensions = ['.txt', '.md']
    
    for filename in sorted(os.listdir(folder_path)):
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in supported_extensions:
            continue
        
        filepath = os.path.join(folder_path, filename)
        
        if os.path.isdir(filepath):
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if not content.strip():
                print(f"⚠️ Fichier vide ignoré: {filename}")
                continue
            
            doc_id = os.path.splitext(filename)[0]
            chunks_count = rag_engine.add_document(content, doc_id)
            
            stats["files_loaded"] += 1
            stats["total_chunks"] += chunks_count
            stats["files"].append(filename)
            
            print(f"📄 Chargé: {filename} ({chunks_count} chunks)")
            
        except UnicodeDecodeError:
            print(f"❌ Erreur encodage: {filename}")
            stats["files_failed"] += 1
        except Exception as e:
            print(f"❌ Erreur {filename}: {e}")
            stats["files_failed"] += 1
    
    return stats



# ÉVÉNEMENTS


@app.on_event("startup")
async def startup_event():
    """Initialise le RAG Engine et charge les documents du dossier data/"""
    global rag
    
    print("=" * 60)
    print("🚀 DÉMARRAGE DE L'API AI DOC ASSISTANT")
    print("=" * 60)
    
    try:
        # Initialiser le RAG Engine
        rag = RAGEngine()
        
        # Charger UNIQUEMENT les documents du dossier data/
        print(f"\n📂 Chargement des documents depuis '{DATA_FOLDER}/'...")
        print("-" * 40)
        
        stats = load_documents_from_folder(rag, DATA_FOLDER)
        
        print("-" * 40)
        print(f"📊 Résumé:")
        print(f"   - Fichiers chargés: {stats['files_loaded']}")
        print(f"   - Fichiers en erreur: {stats['files_failed']}")
        print(f"   - Total chunks: {stats['total_chunks']}")
        
        if stats['files_loaded'] == 0:
            print(f"\n⚠️ ATTENTION: Aucun document trouvé!")
            print(f"💡 Ajoutez des fichiers .txt dans le dossier '{DATA_FOLDER}/'")
        
        print("\n" + "=" * 60)
        print("✅ API PRÊTE!")
        print(f"📖 Documentation: http://localhost:8000/docs")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"❌ Erreur au démarrage: {e}")
        raise e

# ENDPOINTS

@app.get("/", tags=["Health"])
async def root():
    """Health check"""
    return {
        "status": "ok",
        "message": "API RAG opérationnelle"
    }


@app.get("/stats", tags=["Info"])
async def get_stats():
    """Statistiques de la base"""
    if not rag:
        raise HTTPException(status_code=503, detail="RAG Engine non initialisé")
    
    files_in_data = []
    if os.path.exists(DATA_FOLDER):
        files_in_data = [f for f in os.listdir(DATA_FOLDER) 
                        if f.endswith(('.txt', '.md'))]
    
    return {
        "success": True,
        "data": {
            **rag.get_stats(),
            "data_folder": DATA_FOLDER,
            "files_in_folder": files_in_data
        }
    }


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """Pose une question au chatbot"""
    if not rag:
        raise HTTPException(status_code=503, detail="RAG Engine non initialisé")
    
    if not request.query.strip():
        return ChatResponse(success=False, error="Question vide")
    
    try:
        result = rag.generate_answer(
            query=request.query,
            use_rag=request.use_rag
        )
        return ChatResponse(success=True, data=result)
        
    except Exception as e:
        print(f"❌ Erreur chat: {e}")
        return ChatResponse(success=False, error=str(e))


@app.post("/upload", response_model=UploadResponse, tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """Upload et indexe un document"""
    if not rag:
        raise HTTPException(status_code=503, detail="RAG Engine non initialisé")
    
    allowed_extensions = [".txt", ".md"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        return UploadResponse(
            success=False,
            message="",
            error=f"Format non supporté. Utilisez: {', '.join(allowed_extensions)}"
        )
    
    try:
        content = await file.read()
        text = content.decode('utf-8')
        
        if not text.strip():
            return UploadResponse(success=False, message="", error="Fichier vide")
        
        
        if not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)
        
        save_path = os.path.join(DATA_FOLDER, file.filename)
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        doc_id = os.path.splitext(file.filename)[0]
        chunks_count = rag.add_document(text, doc_id)
        
        return UploadResponse(
            success=True,
            message=f"'{file.filename}' sauvegardé dans {DATA_FOLDER}/",
            chunks_created=chunks_count
        )
        
    except UnicodeDecodeError:
        return UploadResponse(success=False, message="", error="Encodage invalide (utilisez UTF-8)")
    except Exception as e:
        return UploadResponse(success=False, message="", error=str(e))


@app.post("/reload", tags=["Documents"])
async def reload_documents():
    """Recharge tous les documents du dossier data/"""
    if not rag:
        raise HTTPException(status_code=503, detail="RAG Engine non initialisé")
    
    try:
        stats = load_documents_from_folder(rag, DATA_FOLDER)
        return {
            "success": True,
            "message": f"{stats['files_loaded']} fichiers rechargés",
            "data": stats
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/files", tags=["Documents"])
async def list_files():
    """Liste les fichiers dans data/"""
    if not os.path.exists(DATA_FOLDER):
        return {"success": True, "files": [], "count": 0}
    
    files = []
    for filename in sorted(os.listdir(DATA_FOLDER)):
        filepath = os.path.join(DATA_FOLDER, filename)
        if os.path.isfile(filepath) and filename.endswith(('.txt', '.md')):
            size = os.path.getsize(filepath)
            files.append({
                "name": filename,
                "size_bytes": size,
                "size_kb": round(size / 1024, 2)
            })
    
    return {"success": True, "folder": DATA_FOLDER, "count": len(files), "files": files}

# LANCEMENT LOCAL


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)