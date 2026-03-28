from __future__ import annotations

import re
from typing import Any


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