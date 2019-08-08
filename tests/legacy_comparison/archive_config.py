"""Functions go generate /archive URLs."""
from response_comparisons import compare_status

res_comparisons = [compare_status]
text_comparisons = []
html_comparisons = []


def ng_id_to_url_fn(id: str) -> str:
    """Generate a local /archive URL given a paper ID."""
    return 'http://localhost:5000/archive/' + id


def legacy_id_to_url_fn(id: str) -> str:
    """Generate an arxiv.org/archive URL given a paper ID."""
    return 'https://arxiv.org/archive/' + id
