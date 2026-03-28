from src.crawler import Crawler


def test_extract_visible_text_from_quote_page() -> None:
    html = """
    <html>
      <head><title>Quotes</title></head>
      <body>
        <div class="quote">
          <span class="text">“A witty saying proves nothing.”</span>
          <small class="author">Voltaire</small>
          <div class="tags">
            <a class="tag">wisdom</a>
            <a class="tag">humour</a>
          </div>
        </div>
      </body>
    </html>
    """

    crawler = Crawler("https://quotes.toscrape.com/")
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")

    text = crawler._extract_visible_text(soup)

    assert "A witty saying proves nothing." in text
    assert "Voltaire" in text
    assert "wisdom" in text
    assert "humour" in text


def test_extract_links_only_keeps_allowed_internal_pages() -> None:
    html = """
    <html>
      <body>
        <a href="/page/2/">Next</a>
        <a href="/login">Login</a>
        <a href="/author/Albert-Einstein">Author</a>
        <a href="https://example.com/page/1/">External</a>
      </body>
    </html>
    """

    crawler = Crawler("https://quotes.toscrape.com/")
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")

    links = crawler._extract_links(soup, "https://quotes.toscrape.com/")

    assert links == ["https://quotes.toscrape.com/page/2/"]


def test_crawl_collects_documents_from_mocked_pages(requests_mock) -> None:
    page_1 = """
    <html>
      <head><title>Page 1</title></head>
      <body>
        <div class="quote">
          <span class="text">“Quote one.”</span>
          <small class="author">Author One</small>
          <div class="tags">
            <a class="tag">life</a>
          </div>
        </div>
        <a href="/page/2/">Next</a>
      </body>
    </html>
    """

    page_2 = """
    <html>
      <head><title>Page 2</title></head>
      <body>
        <div class="quote">
          <span class="text">“Quote two.”</span>
          <small class="author">Author Two</small>
          <div class="tags">
            <a class="tag">friendship</a>
          </div>
        </div>
      </body>
    </html>
    """

    requests_mock.get("https://quotes.toscrape.com/", text=page_1)
    requests_mock.get("https://quotes.toscrape.com/page/2/", text=page_2)

    crawler = Crawler("https://quotes.toscrape.com/", politeness_delay=0.0)
    documents = crawler.crawl()

    assert len(documents) == 2

    urls = [doc["url"] for doc in documents]
    assert "https://quotes.toscrape.com/" in urls
    assert "https://quotes.toscrape.com/page/2/" in urls

    combined_text = " ".join(doc["text"] for doc in documents)
    assert "Author One" in combined_text
    assert "Author Two" in combined_text
    assert "life" in combined_text
    assert "friendship" in combined_text


def test_crawl_skips_failed_pages(requests_mock) -> None:
    page_1 = """
    <html>
      <head><title>Page 1</title></head>
      <body>
        <div class="quote">
          <span class="text">“Quote one.”</span>
          <small class="author">Author One</small>
        </div>
        <a href="/page/2/">Next</a>
      </body>
    </html>
    """

    requests_mock.get("https://quotes.toscrape.com/", text=page_1)
    requests_mock.get("https://quotes.toscrape.com/page/2/", status_code=404)

    crawler = Crawler("https://quotes.toscrape.com/", politeness_delay=0.0)
    documents = crawler.crawl()

    assert len(documents) == 1
    assert documents[0]["url"] == "https://quotes.toscrape.com/"