import logging
from typing import List, Dict, Any, Tuple
from src.ingest.embeddings import LocalVectorStore

logger = logging.getLogger(__name__)

# Global variable to hold the lazy-loaded cross-encoder to avoid reloading
_CROSS_ENCODER = None

def get_cross_encoder():
    global _CROSS_ENCODER
    if _CROSS_ENCODER is None:
        try:
            logger.info("Lazy-loading multilingual Cross-Encoder (BAAI/bge-reranker-v2-m3 or fallback)...")
            from sentence_transformers import CrossEncoder
            # Lightweight multilingual model
            _CROSS_ENCODER = CrossEncoder('cross-encoder/mmarco-mMiniLMv2-L6-H384-v1')
            logger.info("Cross-Encoder loaded successfully.")
        except ImportError:
            logger.warning("sentence-transformers not installed. Skipping Cross-Encoder reranking.")
            _CROSS_ENCODER = "UNAVAILABLE"
        except Exception as e:
            logger.warning(f"Failed to load Cross-Encoder: {str(e)}. Proceeding without reranking.")
            _CROSS_ENCODER = "UNAVAILABLE"
    return _CROSS_ENCODER

class RetrievalEngine:
    def __init__(self, chunks: List[Dict[str, Any]], file_index: List[Dict[str, Any]] = None):
        self.vector_store = LocalVectorStore()
        self.vector_store.build_index(chunks)
        self.vector_store.deduplicate_chunks(threshold=0.96)
        self.file_index = file_index or []

    def get_evidence_pack(
        self,
        section_name: str,
        section_desc: str,
        primary_files: List[str],
        k_per_source: int = 2,
        total_cap: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Builds a deterministic, multi-source evidence pack.
        No LLM calls. Ensures each primary source is represented up to a cap.
        """
        if not primary_files:
            primary_files = list({c["file_id"] for c in self.vector_store.chunks})

        # 1. Generate Deterministic Queries
        queries = [
            section_name,
            f"{section_name} {section_desc}".strip(),
        ]

        # Enhanced retrieval for generic headings: add keywords from primary sources
        generic_terms = {
            "introduction", "background", "context", "overview",
            "preface", "executive summary",
        }
        is_generic = any(t in section_name.lower() for t in generic_terms)

        if is_generic:
            source_keywords = []
            for item in self.file_index:
                if item["file_id"] in primary_files:
                    source_keywords.extend(item.get("keywords", []))
            if source_keywords:
                unique_kw = list(dict.fromkeys(source_keywords))[:10]
                queries.append(" ".join(unique_kw))

        # Keyword-based query from name/desc
        import re
        words = re.findall(r'\w+', (section_name + " " + section_desc).lower())
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
            'to', 'in', 'of', 'for', 'with', 'on', 'at', 'by', 'from',
            'synthesis', 'overview',
        }
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        if keywords:
            queries.append(" ".join(keywords[:5]))

        # 2. Multi-Pass Retrieval (Expand initial search pool for Extreme Volume 5+ docs)
        all_results = []
        for q in queries:
            all_results.extend(self.vector_store.search(q, top_k=40))
            for fid in primary_files:
                all_results.extend(
                    self.vector_store.search(q, top_k=k_per_source, file_filter=[fid])
                )

        # 3. Deduplicate and Diversity Filter
        seen_chunks = {}
        for res in all_results:
            cid = res["chunk_id"]
            if cid not in seen_chunks or res["score"] > seen_chunks[cid]["score"]:
                seen_chunks[cid] = res

        # Group by source
        by_source: Dict[str, List[Dict[str, Any]]] = {}
        unique_results = list(seen_chunks.values())

        # 3.5 Cross-Encoder Reranking (High-Volume Noise Filter)
        reranker = get_cross_encoder()
        if reranker and reranker != "UNAVAILABLE" and unique_results:
            try:
                # Structure input pairs: (Query, Chunk Text)
                # Using the primary section name + desc as the definitive query
                base_query = f"{section_name} {section_desc}".strip()
                pairs = [[base_query, res["text"]] for res in unique_results]
                
                # Predict relevance scores
                scores = reranker.predict(pairs)
                
                # Update chunk scores with cross-encoder precision
                for res, score in zip(unique_results, scores):
                    res["score"] = float(score)  # Overwrite dense/sparse with cross-score
                    
            except Exception as e:
                logger.error(f"Reranking failed: {e}")

        for res in unique_results:
            fid = res["file_id"]
            if fid not in by_source:
                by_source[fid] = []
            by_source[fid].append(res)

        # Select top chunks while enforcing per-source diversity
        final_pack = []
        per_source_cap = max(2, total_cap // max(1, len(primary_files)))

        for fid in by_source:
            by_source[fid] = sorted(
                by_source[fid], key=lambda x: x["score"], reverse=True
            )

        # Balanced round-robin
        source_ids = list(by_source.keys())
        added_count = 0

        while added_count < total_cap:
            added_this_round = 0
            for fid in source_ids:
                if (
                    len(by_source[fid]) > 0
                    and len([c for c in final_pack if c["file_id"] == fid]) < per_source_cap
                ):
                    final_pack.append(by_source[fid].pop(0))
                    added_count += 1
                    added_this_round += 1
                if added_count >= total_cap:
                    break
            if added_this_round == 0:
                break

        return sorted(final_pack, key=lambda x: x["score"], reverse=True)

    # ── CRAG-style Evidence Quality Assessment ───────────────────────────────

    def assess_evidence_quality(
        self,
        evidence_pack: List[Dict[str, Any]],
        min_chunks: int = 2,
        min_avg_score: float = 0.15,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluates whether retrieved evidence is strong enough.
        Returns (is_strong, diagnostics).
        """
        if not evidence_pack:
            return False, {
                "reason": "no_evidence",
                "chunk_count": 0,
                "avg_score": 0.0,
            }

        scores = [e.get("score", 0.0) for e in evidence_pack]
        avg_score = sum(scores) / len(scores)
        chunk_count = len(evidence_pack)

        is_strong = chunk_count >= min_chunks and avg_score >= min_avg_score

        return is_strong, {
            "reason": "ok" if is_strong else "weak",
            "chunk_count": chunk_count,
            "avg_score": round(avg_score, 4),
            "min_score": round(min(scores), 4),
            "max_score": round(max(scores), 4),
        }

    # ── CRAG-style Retrieval Repair ──────────────────────────────────────────

    def repair_evidence(
        self,
        section_name: str,
        section_desc: str,
        primary_files: List[str],
        current_evidence: List[Dict[str, Any]],
        expanded_pool_k: int = 80,
    ) -> List[Dict[str, Any]]:
        """
        Broadens retrieval when evidence is weak.
        Strategy:
          1. Add document-level keywords from file_index to query
          2. Increase candidate pool size
          3. Re-search with broadened queries targeted to each primary source
          4. Merge with existing evidence (dedup)
        """
        existing_cids = {e["chunk_id"] for e in current_evidence}

        # Build broadened queries from file_index keywords
        extra_keywords = []
        for item in self.file_index:
            if item["file_id"] in primary_files:
                extra_keywords.extend(item.get("keywords", []))
        unique_kw = list(dict.fromkeys(extra_keywords))[:8]

        broad_queries = [
            f"{section_name} {' '.join(unique_kw)}".strip(),
            f"{section_desc} {' '.join(unique_kw[:4])}".strip(),
            " ".join(unique_kw) if unique_kw else section_name,
        ]

        new_results = []
        for q in broad_queries:
            # Search with larger pool
            results = self.vector_store.search(
                q, top_k=8, hybrid_weight=0.4  # lean more toward sparse for keyword match
            )
            new_results.extend(results)

            # Per-source targeted
            for fid in primary_files:
                targeted = self.vector_store.search(
                    q, top_k=3, file_filter=[fid], hybrid_weight=0.4
                )
                new_results.extend(targeted)

        # Dedup against existing + self
        seen = set(existing_cids)
        augmented = list(current_evidence)
        for res in new_results:
            if res["chunk_id"] not in seen:
                seen.add(res["chunk_id"])
                augmented.append(res)

        return sorted(augmented, key=lambda x: x.get("score", 0), reverse=True)

    # ── Coverage Check ───────────────────────────────────────────────────────

    def check_coverage(
        self,
        retrieval_map: Dict[str, List[Dict[str, Any]]],
        primary_files: List[str],
    ) -> List[str]:
        """
        Returns a list of file IDs that are NOT covered in the retrieval map.
        """
        covered_files = set()
        for chunks in retrieval_map.values():
            if isinstance(chunks, dict):
                chunks = chunks.get("evidence", [])
            for chunk in chunks:
                covered_files.add(chunk["file_id"])

        return [fid for fid in primary_files if fid not in covered_files]
