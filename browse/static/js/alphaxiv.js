(function () {
  const container = document.getElementById("alphaxiv-output");
  const containerAlreadyHasContent = container.innerHTML.trim().length > 0;

  // This script is invoked every time the Labs toggle is toggled, even when
  // it's toggled to disabled. So this check short-circuits the script if the
  // container already has content.
  if (containerAlreadyHasContent) {
    container.innerHTML = "";
    container.setAttribute("style", "display:none");
    return;
  } else {
    container.setAttribute("style", "display:block");
  }

  // Get the arXiv paper ID from the URL, e.g. "2103.17249" or "astro-ph/9212001"
  const arxivId = window.location.pathname.replace("/abs/", "");

  const alphaxivApi = `https://api.alphaxiv.org/arxiv/v1/${encodeURIComponent(arxivId)}/labs`;
  const alphaXivUrl = `https://alphaxiv.org/abs/${arxivId}`;

  (async () => {
    try {
      let response = await fetch(alphaxivApi);
      if (!response.ok) {
        throw new Error("Not OK response");
      }
      let result = await response.json();
      render(result.summary);
    } catch {
      render(null);
    }
  })();

  // Generate HTML, sanitize it to prevent XSS, and inject into the DOM
  function render(summary) {
    container.innerHTML = window.DOMPurify.sanitize(
      `
       <h2 class="alphaxiv-logo">alphaXiv</h2>
       ${html(summary)}
      `,
      { ADD_ATTR: ["target"] },
    );
  }

  function html(summary) {
    let resultStr = `<h3 class="alphaxiv-summary">Your personalized arXiv assistant</h3><p>Highlight to chat with AI, read visual blog, and discover similar papers <a href="${alphaXivUrl}">here</a>.</p>`;
    if (summary) {
      resultStr += `<div>${summary}</div>`; // 2-4 line ai summary of paper, only available on some papers
    }
    return resultStr;
  }
})();
