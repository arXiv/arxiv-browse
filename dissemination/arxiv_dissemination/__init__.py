from arxiv_dissemination.services.article_store import ArticleStore

article_store:ArticleStore = ArticleStore(None, None, None)
"""ArticleStore for use by code in the app.

This works because it is thread safe and not bound to the app context.

Must be set in the app factory."""
