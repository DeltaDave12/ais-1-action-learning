from typing import List, Tuple

def get_answer_references(answer: str, max_results: int = 3) -> List[Tuple[str, str]]:
    """
    Given an answer string, search DuckDuckGo and return a list of (title, url) tuples.
    """
    try:
        from ddgs import DDGS
    except ImportError:
        return [("Install ddgs to enable references.", "https://pypi.org/project/ddgs/")]
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(answer, max_results=max_results):
            if 'title' in r and 'href' in r:
                results.append((r['title'], r['href']))
            if len(results) >= max_results:
                break
    return results 