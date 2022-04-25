// Labs integration for displaying machine learning demos from huggingface.co/spaces

(function () {
  console.log("run spaces")

  const container = document.getElementById("spaces-output")
  const containerAlreadyHasContent = container.innerHTML.trim().length > 0

  // This script is invoked every time the Labs toggle is toggled, even when
  // it's toggled to disabled. So this check short-circuits the script if the
  // container already has content.
  if (containerAlreadyHasContent) {
    container.innerHTML = ""
    container.setAttribute("style", "display:none")
    return
  } else {
    container.setAttribute("style", "display:block")
  }

  // Get the arXiv paper ID from the URL, e.g. "2103.17249"
  // (this can be overridden for testing by passing a override_paper_id query parameter in the URL)
  const params = new URLSearchParams(document.location.search)
  const arxivPaperId = params.get("override_paper_id") || window.location.pathname.split('/').reverse()[0]
  if (!arxivPaperId) return

  const huggingfaceHost = "https://huggingface.co"
  const spacesHost = `${huggingfaceHost}/spaces`
  // const spacesApiUrl = `${spacesHost}/api/models?filter=arxiv:${arxivPaperId}`
  const spacesApiUrl = `${huggingfaceHost}/api/spaces/flax-community/dalle-mini`

  // Search the HF Spaces API for models that implement this paper
  fetch(spacesApiUrl).then(response => {
    if (response.ok) {
      return response.json()
    } else {
      console.error(`Unable to fetch model data from ${spacesHost}`)
      return Promise.reject(response.status)
    }
  })
    .then(data => render([data]))
    .catch(error => console.log(error))

  // Generate HTML, sanitize it to prevent XSS, and inject into the DOM
  function render(models) {
    container.innerHTML = window.DOMPurify.sanitize(`
        ${summary(models)}
        ${noModelsFound(models)}
        ${models.map(model => renderModel(model)).join("\n")}
      `)
  }

  function summary(models) {
    switch (models.length) {
      case 0:
        return ``
        break
      case 1:
        return `<p>@${models[0].author} has implemented an open-source demo based on this paper. Run it on Spaces:</p>`
        break
      default:
        return `<p>${new Intl.ListFormat().format(models.map(model => `@${model.author}`))} have implemented open-source demos based on this paper. Run them on Spaces:</p>`
    }
  }

  function noModelsFound(models) {
    if (models.length === 0) {
      return `<p>
        No demos found for this article. You can <a href="https://huggingface.co/new-space">add one here</a>.
      </p>`
    } else {
      return ``
    }
  }

  function renderModel(model) {
    console.log(model)
    return `
      <div class="spaces-model">
        <a class="spaces-card" href="${spacesHost}/${model.id}" 
          style="background: -webkit-linear-gradient(315deg,${model.cardData.colorFrom},${model.cardData.colorTo}); background: linear-gradient(315deg,${model.cardData.colorFrom},${model.cardData.colorTo});"
        >
          <span class="spaces-emoji">${model.cardData.emoji}</span>
          <span class="spaces-title">${model.cardData.title}</span>
        </a>
        <div class="spaces-model-details">
          <a href="${spacesHost}/${model.id}">
            <h3 class="spaces-model-details-heading">${model.id}</h3>
          </a>
          <p>A ${model.cardData.sdk} demo</p>
        </div>
      </div>
    `
  }
})();