// Labs integration for displaying machine learning demos from replicate.com

(function() {
  // Get the arXiv paper ID from the URL, e.g. "2103.17249"
  // (this can be overridden for testing by passing a override_paper_id query parameter in the URL)
  const params = new URLSearchParams(document.location.search)
  const arxivPaperId = params.get("override_paper_id") || window.location.pathname.split('/').reverse()[0]
  if (!arxivPaperId) return

  const replicateHost = "https://replicate.com"
  const replicateApiUrl = `${replicateHost}/api/v1/models?arxiv_paper_id=${arxivPaperId}`
  const container = document.getElementById("replicate-output")

  // This script is run whenever the Labs toggle input is clicked, regardless of
  // whether the toggle is enabled or disabled. If content already exists, 
  // we know the toggle was just disabled, so remove content and hide container.
  if (container.innerHTML.trim().length) {
    container.innerHTML = ""
    container.setAttribute("style", "display:none")
    return
  } else {
    container.setAttribute("style", "display:block")
  }

  // Search the Replicate API for models that implement this paper
  fetch(replicateApiUrl).then(response => {
    if (response.ok) {
        return response.json()
    } else {
        console.error(`Unable to fetch model data from ${replicateHost}`)
        return Promise.reject(response.status)
    }
  })
    .then(data => render(data))
    .catch(error => console.log(error))

  // Generate HTML, sanitize it to prevent XSS, and inject into the DOM
  function render({ models }) {
      container.innerHTML = window.DOMPurify.sanitize(`
        ${noModelsFound(models)}
        ${models.map(model => renderModel(model))}
      `)
  }

  function noModelsFound(models) {
    if (models.length === 0) {
      return `<p>
        No demos found for this article. You can <a href="https://replicate.com/docs">add one here</a>.
      </p>`
    } else {
      return ``
    }
  }

  function renderModel(model) {
    return `
      <div class="replicate-model">
        <a href="${model.absolute_url}">
          <img src="${model.cover_image}" class="replicate-model-image" />
        </a>
        <div class="replicate-model-details">
          <a href="${model.absolute_url}">
            <h4 class="replicate-model-details-heading">${model.absolute_url.replace("https://", "")}</h4>
          </a>
          <p>${model.description}</p>
        </div>
      </div>
    `
  }

})();