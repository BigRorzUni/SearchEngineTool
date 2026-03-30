from __future__ import annotations

import re
from typing import Any
import math


class InvertedIndex:
    def __init__(self) -> None:
        self.index: dict[str, dict[str, Any]] = {}
        self.documents: dict[str, dict[str, Any]] = {}

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """
        Convert text into lowercase word tokens.

        Keeps apostrophes inside words and ignores punctuation.
        Examples:
        - "Good friends." -> ["good", "friends"]
        - "Don't stop" -> ["don't", "stop"]
        """
        return re.findall(r"\b[\w']+\b", text.lower())

    def add_document(self, url: str, text: str, title: str = "") -> None:
        """
        Add a document to the inverted index.

        Stores:
        - document metadata
        - per-term document frequency
        - per-document term frequency
        - positions of each term in the document
        """
        tokens = self.tokenize(text)

        self.documents[url] = {
            "title": title,
            "word_count": len(tokens),
        }

        if not tokens:
            return

        seen_terms: set[str] = set()

        for position, token in enumerate(tokens):
            if token not in self.index:
                self.index[token] = {
                    "doc_freq": 0,
                    "postings": {},
                }

            postings = self.index[token]["postings"]

            if url not in postings:
                postings[url] = {
                    "term_freq": 0,
                    "positions": [],
                }

            postings[url]["term_freq"] += 1
            postings[url]["positions"].append(position)

            if token not in seen_terms:
                self.index[token]["doc_freq"] += 1
                seen_terms.add(token)

    def get_postings(self, term: str) -> dict[str, Any] | None:
        """
        Return the posting information for a term, or None if absent.
        """
        return self.index.get(term.lower())

    def find_documents_containing_all(self, terms: list[str]) -> list[str]:
        """
        Return sorted document URLs that contain all query terms.
        """
        normalised_terms = [term.lower() for term in terms if term.strip()]
        if not normalised_terms:
            return []

        posting_sets: list[set[str]] = []

        for term in normalised_terms:
            term_data = self.index.get(term)
            if term_data is None:
                return []
            posting_sets.append(set(term_data["postings"].keys()))

        common_docs = set.intersection(*posting_sets)
        return sorted(common_docs)

    def rank_documents_by_term_frequency(
        self,
        terms: list[str],
        documents: list[str],
    ) -> list[tuple[str, int]]:
        """
        Rank documents by the sum of term frequencies for the query terms.
        """
        scores: list[tuple[str, int]] = []

        for doc in documents:
            score = 0
            for term in terms:
                term_data = self.index.get(term.lower())
                if term_data is None:
                    continue

                posting = term_data["postings"].get(doc)
                if posting is not None:
                    score += posting["term_freq"]

            scores.append((doc, score))

        scores.sort(key=lambda item: (-item[1], item[0]))
        return scores

    def document_count(self) -> int:
        """
        Return the total number of indexed documents.
        """
        return len(self.documents)

    def inverse_document_frequency(self, term: str) -> float:
        """
        Compute IDF for a term.

        Uses log(1 + N / df) to avoid division issues and keep values stable.
        """
        term_data = self.index.get(term.lower())
        if term_data is None:
            return 0.0

        df = term_data["doc_freq"]
        if df == 0:
            return 0.0

        n_docs = self.document_count()
        return math.log(1 + (n_docs / df))

    def rank_documents_by_tfidf(
        self,
        terms: list[str],
        documents: list[str],
    ) -> list[tuple[str, float]]:
        """
        Rank documents by summed TF-IDF score for the query terms.
        """
        scores: list[tuple[str, float]] = []

        for doc in documents:
            score = 0.0
            doc_meta = self.documents.get(doc, {})
            doc_length = doc_meta.get("word_count", 0)

            for term in terms:
                term_data = self.index.get(term.lower())
                if term_data is None:
                    continue

                posting = term_data["postings"].get(doc)
                if posting is None:
                    continue

                term_freq = posting["term_freq"]

                # Length-normalised term frequency
                tf = term_freq / doc_length if doc_length > 0 else 0.0
                idf = self.inverse_document_frequency(term)

                score += tf * idf

            scores.append((doc, score))

        scores.sort(key=lambda item: (-item[1], item[0]))
        return scores
    
    @staticmethod
    def minimum_position_distance(
        positions_a: list[int],
        positions_b: list[int],
    ) -> int | None:
        """
        Return the minimum absolute distance between two sorted position lists.

        Uses a two-pointer scan for efficiency.
        """
        if not positions_a or not positions_b:
            return None

        i = 0
        j = 0
        min_distance = float("inf")

        while i < len(positions_a) and j < len(positions_b):
            a = positions_a[i]
            b = positions_b[j]
            distance = abs(a - b)

            if distance < min_distance:
                min_distance = distance

            if a < b:
                i += 1
            else:
                j += 1

        return int(min_distance) if min_distance != float("inf") else None
    

    def proximity_bonus(self, terms: list[str], document: str) -> float:
        """
        Compute a proximity bonus for a query in a document.

        For each adjacent pair of query terms, find the minimum distance
        between their positions. Smaller distances produce larger bonuses.

        Bonus formula:
            1 / (1 + distance)

        This keeps the bonus bounded and easy to interpret.
        """
        normalised_terms = [term.lower() for term in terms if term.strip()]
        if len(normalised_terms) < 2:
            return 0.0

        bonus = 0.0

        for i in range(len(normalised_terms) - 1):
            term_a = normalised_terms[i]
            term_b = normalised_terms[i + 1]

            data_a = self.index.get(term_a)
            data_b = self.index.get(term_b)

            if data_a is None or data_b is None:
                continue

            posting_a = data_a["postings"].get(document)
            posting_b = data_b["postings"].get(document)

            if posting_a is None or posting_b is None:
                continue

            positions_a = posting_a["positions"]
            positions_b = posting_b["positions"]

            min_distance = self.minimum_position_distance(positions_a, positions_b)
            if min_distance is None:
                continue

            bonus += 1.0 / (1.0 + min_distance)

        return bonus

    def rank_documents_by_tfidf_with_proximity(
        self,
        terms: list[str],
        documents: list[str],
        proximity_weight: float = 0.5,
    ) -> list[tuple[str, float]]:
        """
        Rank documents by TF-IDF plus a proximity bonus.

        proximity_weight controls how strongly proximity affects ranking.
        """
        scores: list[tuple[str, float]] = []

        for doc in documents:
            tfidf_score = 0.0
            doc_meta = self.documents.get(doc, {})
            doc_length = doc_meta.get("word_count", 0)

            for term in terms:
                term_data = self.index.get(term.lower())
                if term_data is None:
                    continue

                posting = term_data["postings"].get(doc)
                if posting is None:
                    continue

                term_freq = posting["term_freq"]
                tf = term_freq / doc_length if doc_length > 0 else 0.0
                idf = self.inverse_document_frequency(term)

                tfidf_score += tf * idf

            bonus = self.proximity_bonus(terms, doc)
            total_score = tfidf_score + (proximity_weight * bonus)

            scores.append((doc, total_score))

        scores.sort(key=lambda item: (-item[1], item[0]))
        return scores

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "documents": self.documents,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InvertedIndex":
        instance = cls()
        instance.index = data.get("index", {})
        instance.documents = data.get("documents", {})
        return instance