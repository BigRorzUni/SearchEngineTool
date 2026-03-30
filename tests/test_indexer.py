from src.indexer import InvertedIndex


def test_tokenize_lowercases_and_removes_punctuation() -> None:
    text = "Good friends, GOOD books, and a sleepy conscience."
    tokens = InvertedIndex.tokenize(text)

    assert tokens == ["good", "friends", "good", "books", "and", "a", "sleepy", "conscience"]


def test_tokenize_keeps_apostrophes_inside_words() -> None:
    text = "Don't stop believing."
    tokens = InvertedIndex.tokenize(text)

    assert tokens == ["don't", "stop", "believing"]


def test_add_document_stores_document_metadata() -> None:
    index = InvertedIndex()

    index.add_document(
        url="https://example.com/page1",
        text="Hello world hello",
        title="Page 1",
    )

    assert index.documents["https://example.com/page1"]["title"] == "Page 1"
    assert index.documents["https://example.com/page1"]["word_count"] == 3


def test_add_document_tracks_term_frequency_and_positions() -> None:
    index = InvertedIndex()

    index.add_document(
        url="https://example.com/page1",
        text="hello world hello",
        title="Page 1",
    )

    hello = index.get_postings("hello")
    assert hello is not None
    assert hello["doc_freq"] == 1
    assert hello["postings"]["https://example.com/page1"]["term_freq"] == 2
    assert hello["postings"]["https://example.com/page1"]["positions"] == [0, 2]

    world = index.get_postings("world")
    assert world is not None
    assert world["doc_freq"] == 1
    assert world["postings"]["https://example.com/page1"]["term_freq"] == 1
    assert world["postings"]["https://example.com/page1"]["positions"] == [1]


def test_doc_frequency_counts_documents_not_occurrences() -> None:
    index = InvertedIndex()

    index.add_document("doc1", "life life life", "Doc 1")
    index.add_document("doc2", "life is good", "Doc 2")

    life = index.get_postings("life")
    assert life is not None
    assert life["doc_freq"] == 2


def test_get_postings_is_case_insensitive() -> None:
    index = InvertedIndex()
    index.add_document("doc1", "Good friends", "Doc 1")

    lower = index.get_postings("good")
    upper = index.get_postings("GOOD")

    assert lower == upper
    assert lower is not None
    assert lower["doc_freq"] == 1


def test_add_empty_document_still_stores_metadata_but_no_terms() -> None:
    index = InvertedIndex()

    index.add_document("doc1", "", "Empty Doc")

    assert index.documents["doc1"]["title"] == "Empty Doc"
    assert index.documents["doc1"]["word_count"] == 0
    assert index.index == {}


def test_find_documents_containing_all_returns_intersection() -> None:
    index = InvertedIndex()

    index.add_document("doc1", "good friends are here", "Doc 1")
    index.add_document("doc2", "good books are here", "Doc 2")
    index.add_document("doc3", "good friends and good books", "Doc 3")

    result = index.find_documents_containing_all(["good", "friends"])

    assert result == ["doc1", "doc3"]


def test_find_documents_containing_all_returns_empty_if_term_missing() -> None:
    index = InvertedIndex()

    index.add_document("doc1", "good friends", "Doc 1")

    result = index.find_documents_containing_all(["good", "missing"])

    assert result == []


def test_find_documents_containing_all_ignores_blank_terms() -> None:
    index = InvertedIndex()

    index.add_document("doc1", "good friends", "Doc 1")
    index.add_document("doc2", "good books", "Doc 2")

    result = index.find_documents_containing_all(["good", "   "])

    assert result == ["doc1", "doc2"]


def test_rank_documents_by_term_frequency_sorts_by_score_descending() -> None:
    index = InvertedIndex()

    index.add_document("doc1", "good good friends", "Doc 1")
    index.add_document("doc2", "good friends", "Doc 2")
    index.add_document("doc3", "friends friends good", "Doc 3")

    docs = index.find_documents_containing_all(["good", "friends"])
    ranked = index.rank_documents_by_term_frequency(["good", "friends"], docs)

    assert ranked == [("doc1", 3), ("doc3", 3), ("doc2", 2)]


def test_to_dict_and_from_dict_round_trip() -> None:
    index = InvertedIndex()
    index.add_document("doc1", "hello world hello", "Doc 1")

    data = index.to_dict()
    restored = InvertedIndex.from_dict(data)

    assert restored.index == index.index
    assert restored.documents == index.documents

def test_document_count_returns_number_of_documents() -> None:
    index = InvertedIndex()
    index.add_document("doc1", "hello world", "Doc 1")
    index.add_document("doc2", "good friends", "Doc 2")

    assert index.document_count() == 2


def test_inverse_document_frequency_is_higher_for_rarer_terms() -> None:
    index = InvertedIndex()
    index.add_document("doc1", "common rare", "Doc 1")
    index.add_document("doc2", "common", "Doc 2")
    index.add_document("doc3", "common", "Doc 3")

    common_idf = index.inverse_document_frequency("common")
    rare_idf = index.inverse_document_frequency("rare")

    assert rare_idf > common_idf


def test_rank_documents_by_tfidf_returns_ranked_results() -> None:
    index = InvertedIndex()
    index.add_document("doc1", "good good friends", "Doc 1")
    index.add_document("doc2", "good friends", "Doc 2")

    docs = index.find_documents_containing_all(["good", "friends"])
    ranked = index.rank_documents_by_tfidf(["good", "friends"], docs)

    assert len(ranked) == 2
    assert ranked[0][0] in {"doc1", "doc2"}
    assert ranked[1][0] in {"doc1", "doc2"}
    assert ranked[0][0] != ranked[1][0]
    assert ranked[0][1] >= ranked[1][1]