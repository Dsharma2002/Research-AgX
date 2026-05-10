from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
from tavily import TavilyClient
import os
from dotenv import load_dotenv
from rich import print

load_dotenv()

tavily = TavilyClient(os.getenv("TAVILY_API_KEY"))

@tool
def web_search(query: str) -> str:
    """Search the web for most recent and reliable information about the query.
    Returns Title, URL, and Snippets."""
    results = tavily.search(query, max_results=5)
    out = []
    for result in results['results']:
        out.append(f"Title: {result['title']}\nURL: {result['url']}\nSnippet: {result['content'][:300]}\n")
    return "\n".join(out)

@tool
def scrape_url(url: str) -> str:
    """Scrape the url and return clean text content for deep reading."""
    try:
        response = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:3000]
    except Exception as e:
        return f"Error scraping URL: {str(e)}"

