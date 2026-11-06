"""Recherche vectorielle TF-IDF, baseline du RAG hybride."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .corpus import Document, normalize

FRENCH_STOPWORDS = [
    "au", "aux", "avec", "ce", "ces", "dans", "de", "des", "du", "elle", "en",
    "et", "eux", "il", "ils", "je", "la", "le", "les", "leur", "lui", "ma",
    "mais", "me", "même", "mes", "moi", "mon", "ne", "nos", "notre", "nous",
    "on", "ou", "par", "pas", "pour", "qu", "que", "qui", "sa", "se", "ses",
    "son", "sur", "ta", "te", "tes", "toi", "ton", "tu", "un", "une", "vos",
    "votre", "vous", "c", "d", "j", "l", "à", "m", "n", "s", "t", "y", "été",
    "étée", "étées", "étés", "étant", "suis", "es", "est", "sommes", "êtes",
    "sont", "sera", "seront", "avoir", "ayant", "eu", "eue", "eues", "eus",
    "est-ce", "cette", "cet", "plus", "moins", "très", "tout", "tous", "toute",
    "toutes", "aussi", "comme", "donc", "alors", "ainsi", "dont", "où",
]


@dataclass
class SearchHit:
    document: Document
    score: float
    sentence: str = ""

    def to_dict(self) -> dict:
        return {
            "doc_id": self.document.id,
            "title": self.document.title,
            "score": round(float(self.score), 4),
            "sentence": self.sentence or self.document.snippet,
        }


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [part.strip() for part in parts if len(part.strip()) > 30]


class TfidfVectorStore:
    """Index TF-IDF documents + phrases, avec similarité cosinus."""

    def __init__(self, documents: Iterable[Document], max_features: int = 6000):
        self.documents = list(documents)
        self.by_id = {doc.id: doc for doc in self.documents}
        self.doc_texts = [normalize(doc.text) for doc in self.documents]
        self.doc_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
            max_features=max_features,
            stop_words=FRENCH_STOPWORDS,
            token_pattern=r"(?u)\b[a-zA-Z0-9][a-zA-Z0-9'\-]+\b",
        )
        self.doc_matrix = self.doc_vectorizer.fit_transform(self.doc_texts)

        self.sentence_rows: list[tuple[Document, str]] = []
        for doc in self.documents:
            for sentence in split_sentences(doc.text):
                self.sentence_rows.append((doc, sentence))
        self.sentence_texts = [normalize(sentence) for _, sentence in self.sentence_rows]
        self.sentence_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=1,
            max_features=max_features,
            stop_words=FRENCH_STOPWORDS,
            token_pattern=r"(?u)\b[a-zA-Z0-9][a-zA-Z0-9'\-]+\b",
        )
        self.sentence_matrix = self.sentence_vectorizer.fit_transform(self.sentence_texts)

    def search(self, query: str, top_k: int = 4) -> list[SearchHit]:
        if not query.strip() or self.doc_matrix.shape[0] == 0:
            return []
        try:
            q = self.doc_vectorizer.transform([normalize(query)])
        except ValueError:
            return []
        scores = cosine_similarity(q, self.doc_matrix).ravel()
        order = np.argsort(scores)[::-1][:top_k]
        return [
            SearchHit(document=self.documents[int(i)], score=float(scores[int(i)]))
            for i in order
            if scores[int(i)] > 0
        ]

    def search_sentences(
        self,
        query: str,
        top_k: int = 6,
        doc_ids: list[str] | None = None,
    ) -> list[SearchHit]:
        if not query.strip() or self.sentence_matrix.shape[0] == 0:
            return []
        allowed = set(doc_ids or [])
        try:
            q = self.sentence_vectorizer.transform([normalize(query)])
        except ValueError:
            return []
        scores = cosine_similarity(q, self.sentence_matrix).ravel()
        order = np.argsort(scores)[::-1]
        hits: list[SearchHit] = []
        for idx in order:
            doc, sentence = self.sentence_rows[int(idx)]
            if allowed and doc.id not in allowed:
                continue
            if scores[int(idx)] <= 0:
                continue
            hits.append(SearchHit(document=doc, score=float(scores[int(idx)]), sentence=sentence))
            if len(hits) >= top_k:
                break
        return hits

    def document_frequency(self, term: str) -> int:
        term = normalize(term)
        return sum(1 for text in self.doc_texts if term in text)

    def top_terms(self, doc_id: str, top_n: int = 8) -> list[str]:
        try:
            idx = [doc.id for doc in self.documents].index(doc_id)
        except ValueError:
            return []
        row = self.doc_matrix[idx].toarray().ravel()
        names = self.doc_vectorizer.get_feature_names_out()
        order = np.argsort(row)[::-1][:top_n]
        return [str(names[i]) for i in order if row[i] > 0]
