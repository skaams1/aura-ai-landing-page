# vector_db.py

from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
from config import Config
import time

class VectorDBService:
    def __init__(self):
        self.pc = Pinecone(api_key=Config.PINECONE_API_KEY)
        self.model = SentenceTransformer(Config.EMBEDDING_MODEL)
        self.index_name = Config.PINECONE_INDEX_NAME
        self.index = None
        self._initialize_index()

    def _initialize_index(self):
        """Initialize or connect to Pinecone index"""
        embedding_dim = self.model.get_sentence_embedding_dimension()

        # Check existing indexes
        existing_indexes = [idx.name for idx in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            print(f"Creating new Pinecone index: {self.index_name}")
            self.pc.create_index(
                name=self.index_name,
                dimension=embedding_dim,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=Config.PINECONE_CLOUD,
                    region=Config.PINECONE_REGION
                )
            )
            # Wait for index to be ready
            time.sleep(10)

        self.index = self.pc.Index(self.index_name)
        print(f"Connected to index: {self.index_name}")

    def store_chunks(self, chunks, batch_size=100):
        """Store text chunks in Pinecone"""
        print(f"Storing {len(chunks)} chunks in Pinecone...")

        vectors = []
        for i, chunk in enumerate(chunks):
            text = chunk["text"]
            embedding = self.model.encode(text).tolist()

            vectors.append({
                "id": f"chem-{i:06d}",
                "values": embedding,
                "metadata": {
                    "text": text,
                    "source": chunk.get("source", "unknown"),
                    "type": chunk.get("type", "chemistry")
                }
            })

            # Upsert in batches
            if len(vectors) >= batch_size:
                self.index.upsert(vectors=vectors)
                print(f"Uploaded {i + 1} chunks...")
                vectors = []

        # Upload remaining vectors
        if vectors:
            self.index.upsert(vectors=vectors)

        print(f"Successfully stored all {len(chunks)} chunks!")

    def query(self, question, top_k=5):
        """Query the vector database for relevant context"""
        # Generate embedding for the question
        query_embedding = self.model.encode(question).tolist()

        # Query Pinecone
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )

        # Extract and format relevant chunks
        relevant_texts = []
        for match in results.matches:
            if match.score > 0.3:  # Relevance threshold
                text = match.metadata.get("text", "")
                source = match.metadata.get("source", "unknown")
                relevant_texts.append({
                    "text": text,
                    "source": source,
                    "score": match.score
                })

        return relevant_texts

    def format_context(self, relevant_chunks):
        """Format retrieved chunks into context for the LLM"""
        if not relevant_chunks:
            return ""

        context_parts = ["**Relevant NCERT/JEE Chemistry Context:**\n"]

        for i, chunk in enumerate(relevant_chunks, 1):
            context_parts.append(f"[Source {i}: {chunk['source']}]")
            context_parts.append(chunk['text'])
            context_parts.append("")

        return "\n".join(context_parts)

    def delete_index(self):
        """Delete the Pinecone index"""
        self.pc.delete_index(self.index_name)
        print(f"Deleted index: {self.index_name}")


# Singleton instance
_vector_db = None

def get_vector_db():
    global _vector_db
    if _vector_db is None:
        _vector_db = VectorDBService()
    return _vector_db
