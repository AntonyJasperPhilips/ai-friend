"""Vector database integration with Pinecone."""
from typing import List, Dict
import pinecone
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from config import settings


class VectorDB:
    """Handle vector database operations with Pinecone."""
    
    def __init__(self):
        """Initialize Pinecone connection and embeddings."""
        # Initialize Pinecone
        pinecone.init(
            api_key=settings.pinecone_api_key,
            environment=settings.pinecone_environment
        )
        
        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key
        )
        
        self.index_name = settings.pinecone_index_name
        
        # Create index if it doesn't exist
        self._ensure_index_exists()
    
    def _ensure_index_exists(self):
        """Ensure the Pinecone index exists."""
        if self.index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=self.index_name,
                dimension=1536,  # OpenAI embedding dimension
                metric="cosine"
            )
    
    def store_chunks(self, chunks: List[Dict], textbook_metadata: Dict):
        """
        Store text chunks in Pinecone.
        
        Args:
            chunks: List of chunks with text and metadata
            textbook_metadata: Metadata about the textbook
        """
        texts = [chunk["text"] for chunk in chunks]
        metadatas = []
        
        for chunk in chunks:
            metadata = {
                **chunk["metadata"],
                "textbook_title": textbook_metadata.get("title", ""),
                "subject": textbook_metadata.get("subject", ""),
                "grade_level": textbook_metadata.get("grade_level", ""),
                "teacher_notes": textbook_metadata.get("teacher_notes", "")
            }
            metadatas.append(metadata)
        
        # Use Langchain's PineconeVectorStore for easy integration
        PineconeVectorStore.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas,
            index_name=self.index_name
        )
    
    def search_similar_chunks(
        self,
        query: str,
        textbook_id: str,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Search for similar chunks in Pinecone.
        
        Args:
            query: Query text
            textbook_id: ID of the textbook to search within
            top_k: Number of results to return
            
        Returns:
            List of similar chunks with metadata
        """
        # Initialize vector store
        vectorstore = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings
        )
        
        # Search with filter for specific textbook
        results = vectorstore.similarity_search_with_score(
            query=query,
            k=top_k,
            filter={"textbook_id": textbook_id}
        )
        
        # Format results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "text": doc.page_content,
                "metadata": doc.metadata,
                "similarity_score": float(score)
            })
        
        return formatted_results
    
    def delete_textbook_chunks(self, textbook_id: str):
        """
        Delete all chunks for a specific textbook.
        
        Args:
            textbook_id: ID of the textbook to delete
        """
        index = pinecone.Index(self.index_name)
        
        # Delete by filtering on textbook_id
        index.delete(filter={"textbook_id": textbook_id})


# Global instance
vector_db = VectorDB()
