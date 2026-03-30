from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import faiss
from langchain_community.embeddings import HuggingFaceEmbeddings

class LocalVectorStore:
    def __init__(self):
        # Dense index
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.dim = 384 # Dimension for all-MiniLM-L6-v2
        self.faiss_index = faiss.IndexFlatIP(self.dim)
        
        # Sparse index
        self.vectorizer = TfidfVectorizer(stop_words='english')
        
        self.chunks = []
        self.tfidf_matrix = None

    def build_index(self, chunks: List[Dict[str, Any]]):
        """
        Builds both Dense (FAISS) and Sparse (TF-IDF) indices.
        """
        self.chunks = chunks
        if not chunks:
            return

        texts = [c["text"] for c in chunks]
        
        # 1. Build Sparse (TF-IDF)
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        
        # 2. Build Dense (FAISS)
        # Normalize vectors for cosine similarity (InnerProduct on normalized vectors)
        embeddings = np.array(self.embeddings.embed_documents(texts)).astype('float32')
        faiss.normalize_L2(embeddings)
        
        self.faiss_index = faiss.IndexFlatIP(self.dim)
        self.faiss_index.add(embeddings)

    def search(self, query: str, top_k: int = 5, file_filter: List[str] = None, hybrid_weight: float = 0.5) -> List[Dict[str, Any]]:
        """
        Hybrid search combining Dense (FAISS) and Sparse (TF-IDF).
        Optimized via candidate pooling.
        """
        if not self.chunks or self.tfidf_matrix is None:
            return []
            
        # Candidate pool size
        pool_k = 50
            
        # 1. Sparse Scan (Full scan is fast for TF-IDF)
        query_tfidf = self.vectorizer.transform([query])
        sparse_scores = cosine_similarity(query_tfidf, self.tfidf_matrix).flatten()
        
        # 2. Dense Search (FAISS)
        query_dense = np.array([self.embeddings.embed_query(query)]).astype('float32')
        faiss.normalize_L2(query_dense)
        
        # Pull candidate indices from dense index
        dense_scores, dense_indices = self.faiss_index.search(query_dense, min(pool_k, len(self.chunks)))
        candidate_indices = set(dense_indices[0]) - {-1}
        
        # Add top sparse candidates to pool
        sparse_top_idx = np.argsort(sparse_scores)[::-1][:pool_k]
        candidate_indices.update(sparse_top_idx)
        
        # 3. Hybrid Scoring on Pool Only
        results = []
        for idx in candidate_indices:
            chunk = self.chunks[idx]
            
            # Apply file filter
            if file_filter and chunk["file_id"] not in file_filter:
                continue
                
            # Compute/Map scores for this candidate
            s_score = sparse_scores[idx]
            
            # Find dense score if it was in FAISS results
            d_score = 0.0
            if idx in dense_indices[0]:
                d_pos = np.where(dense_indices[0] == idx)[0][0]
                d_score = float(dense_scores[0][d_pos])
            else:
                # If not in top dense, we could compute it but IP is expensive. 
                # For safety and speed, we treat as 0 or use heuristic.
                d_score = 0.0 
            
            h_score = (hybrid_weight * d_score) + ((1 - hybrid_weight) * s_score)
            
            if h_score > 0:
                results.append({
                    **chunk,
                    "score": float(h_score)
                })
        
        # Sort results and take top_k
        return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

    def deduplicate_chunks(self, threshold: float = 0.95) -> List[Dict[str, Any]]:
        """
        Removes exact duplicates via hashing, then near-identical chunks via sparse cosine similarity.
        """
        if not self.chunks:
            return []

        # 1. Exact Deduplication (Fast)
        unique_chunks = []
        seen_hashes = set()
        import hashlib
        
        for c in self.chunks:
            text_hash = hashlib.md5(c["text"].strip().lower().encode('utf-8')).hexdigest()
            if text_hash not in seen_hashes:
                seen_hashes.add(text_hash)
                unique_chunks.append(c)
        
        self.chunks = unique_chunks
        # MUST rebuild TF-IDF matrix here so near-duplicate check uses current indexing
        self.build_index(self.chunks)

        # 2. Near-Duplicate removal (Semantic/Sparse)
        if self.tfidf_matrix is None or self.tfidf_matrix.shape[0] < 2:
            return self.chunks
            
        sim_matrix = cosine_similarity(self.tfidf_matrix)
        keep = np.ones(len(self.chunks), dtype=bool)
        
        # Track counts per file to avoid removing only evidence
        file_counts = {}
        for c in self.chunks:
            fid = c["file_id"]
            file_counts[fid] = file_counts.get(fid, 0) + 1

        for i in range(len(self.chunks)):
            if not keep[i]:
                continue
            for j in range(i + 1, len(self.chunks)):
                if sim_matrix[i, j] > threshold:
                    # Only remove if file j has other chunks
                    fid_j = self.chunks[j]["file_id"]
                    if file_counts.get(fid_j, 0) > 1:
                        keep[j] = False
                        file_counts[fid_j] -= 1
                    
        self.chunks = [c for idx, c in enumerate(self.chunks) if keep[idx]]
        # Rebuild index after dedup
        self.build_index(self.chunks)
        return self.chunks
