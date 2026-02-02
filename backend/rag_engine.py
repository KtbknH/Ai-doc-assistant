import os
from anthropic import Anthropic
import chromadb


class RAGEngine:
    """
    Moteur RAG (Retrieval-Augmented Generation) avec Claude.
    
    Permet de:
    - Ajouter des documents à une base vectorielle
    - Rechercher des passages pertinents
    - Générer des réponses avec ou sans contexte RAG
    """
    
    def __init__(self):
        """Initialise le client Claude et la base ChromaDB."""
    
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("❌ ANTHROPIC_API_KEY non trouvée dans .env")
    
        self.client = Anthropic(api_key=api_key)
        
        self.chroma_client = chromadb.Client()
  
        self.collection = self.chroma_client.get_or_create_collection(
            name="documents"
        )
        
        print("✅ RAG Engine initialisé avec Claude")
    
    def add_document(self, text: str, doc_id: str) -> int:
        """
        Ajoute un document à la base vectorielle.
        
        Le texte est découpé en chunks de 500 caractères
        pour optimiser la recherche sémantique.
        
        Args:
            text: Contenu du document
            doc_id: Identifiant unique du document
            
        Returns:
            Nombre de chunks créés
        """
        chunk_size = 300
        overlap = 100 
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            if chunk.strip():
                chunks.append(chunk)
            
            start = end - overlap
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"
            
            existing = self.collection.get(ids=[chunk_id])
            if not existing['ids']:
                self.collection.add(
                    documents=[chunk],
                    ids=[chunk_id],
                    metadatas=[{
                        "source": doc_id,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }]
                )
        
        print(f"✅ {len(chunks)} chunks ajoutés pour '{doc_id}'")
        return len(chunks)
    
    def search_context(self, query: str, n_results: int = 3) -> list:
        """
        Recherche les passages les plus pertinents pour une question.
        
        Utilise la recherche sémantique de ChromaDB pour trouver
        les chunks les plus similaires à la question.
        
        Args:
            query: Question de l'utilisateur
            n_results: Nombre de résultats à retourner (défaut: 3)
            
        Returns:
            Liste des chunks pertinents
        """

        if self.collection.count() == 0:
            print("⚠️ Aucun document dans la base")
            return []
        
        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, self.collection.count())
        )
    
        if results and results['documents']:
            chunks = results['documents'][0]
            print(f"🔍 {len(chunks)} chunk(s) trouvé(s)")
            return chunks
        
        return []
    
    def generate_answer(self, query: str, use_rag: bool = True) -> dict:
        """
        Génère une réponse avec Claude, avec ou sans RAG.
        
        Mode RAG activé:
        1. Recherche le contexte pertinent dans les documents
        2. Injecte le contexte dans le prompt
        3. Claude répond en se basant sur le contexte
        
        Mode RAG désactivé:
        - Claude répond directement sans contexte
        
        Args:
            query: Question de l'utilisateur
            use_rag: Activer le mode RAG (défaut: True)
            
        Returns:
            Dict avec answer, sources, mode, model
        """
        context_chunks = []
        
        if use_rag:

            context_chunks = self.search_context(query, n_results=5)
            context_str = "\n\n---\n\n".join(context_chunks)
        
            prompt = f"""Tu es un assistant personnel intelligent. Tu dois répondre à la question en te basant sur le contexte fourni ci-dessous.

<contexte>
{context_str}
</contexte>

<règles>
- Utilise TOUTES les informations pertinentes du contexte pour construire une réponse complète
- Pour les questions sur une personne (ex: "Qui est X?", "Parle-moi de X"), présente un profil complet avec: formation, compétences, expérience, contact si disponibles
- Structure ta réponse de manière claire et lisible
- Si l'information n'est pas dans le contexte, dis "Je ne trouve pas cette information dans les documents"
- Sois naturel et conversationnel dans tes réponses
</règles>

<question>
{query}
</question>

Réponse:"""
        else:
           
            prompt = query
        
        # 3. Appeler Claude Haiku (le moins cher)
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            answer = response.content[0].text
            
        except Exception as e:
            print(f"❌ Erreur Claude: {e}")
            answer = f"Erreur lors de la génération: {str(e)}"
        
        return {
            "answer": answer,
            "sources": context_chunks,
            "mode": "RAG" if use_rag else "Direct",
            "model": "claude-3-haiku-20240307",
            "context_used": len(context_chunks) > 0
        }
    
    def get_stats(self) -> dict:
        """Retourne les statistiques de la base de documents."""
        return {
            "total_chunks": self.collection.count(),
            "model": "claude-3-haiku-20240307"
        }


# =============================================================================
# TEST LOCAL
# =============================================================================
if __name__ == "__main__":
    from dotenv import load_dotenv
    
    # Charger les variables d'environnement
    load_dotenv()
    
    print("=" * 50)
    print("🧪 Test du RAG Engine avec Claude")
    print("=" * 50)
    
    rag = RAGEngine()
    
    doc_python = """
    Python est un langage de programmation créé par Guido van Rossum en 1991.
    Il est caractérisé par sa syntaxe claire et lisible.
    Python est très populaire en data science, machine learning et développement web.
    Les frameworks populaires incluent Django, Flask et FastAPI.
    Python utilise l'indentation pour définir les blocs de code.
    """
    
    doc_claude = """
    Claude est une intelligence artificielle créée par Anthropic.
    Anthropic a été fondée en 2021 par Dario Amodei et Daniela Amodei.
    Claude est conçu pour être utile, honnête et inoffensif.
    Il existe plusieurs versions: Claude Haiku, Claude Sonnet et Claude Opus.
    Claude Haiku est le modèle le plus rapide et le moins cher.
    """
    
    doc_rag = """
    RAG signifie Retrieval-Augmented Generation.
    Cette technique combine la recherche d'information avec la génération de texte.
    Le RAG permet de réduire les hallucinations des modèles de langage.
    ChromaDB est une base de données vectorielle souvent utilisée pour le RAG.
    Les embeddings permettent de représenter le texte sous forme de vecteurs.
    """
    
    rag.add_document(doc_python, "python_info")
    rag.add_document(doc_claude, "claude_info")
    rag.add_document(doc_rag, "rag_info")
    
    print("\n" + "=" * 50)
    print("📊 Statistiques:", rag.get_stats())
    print("=" * 50)
    
    # Test avec RAG
    print("\n🤖 Test AVEC RAG:")
    print("-" * 30)
    question = "Qui a créé Python et en quelle année?"
    result = rag.generate_answer(question, use_rag=True)
    print(f"Q: {question}")
    print(f"R: {result['answer']}")
    print(f"Sources: {len(result['sources'])} chunk(s)")
    
    # Test sans RAG
    print("\n🤖 Test SANS RAG:")
    print("-" * 30)
    result_no_rag = rag.generate_answer(question, use_rag=False)
    print(f"Q: {question}")
    print(f"R: {result_no_rag['answer']}")
    
    print("\n✅ Tests terminés!")