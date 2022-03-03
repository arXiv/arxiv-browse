// Labs integration for displaying machine learning demos from replicate.com

(function() {
  const container = document.getElementById("replicate-output")
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

  const replicateHost = "https://replicate.com"
  const replicateApiUrl = `${replicateHost}/api/v1/models?arxiv_paper_id=${arxivPaperId}`

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
        ${summary(models)}
        ${noModelsFound(models)}
        ${models.map(model => renderModel(model)).join("\n")}
      `)
  }

  function summary(models) {
    switch(models.length) {
      case 0:
        return ``
        break
      case 1:
        return `<p>@${models[0].username} has implemented an open-source model based on this paper. Run it on Replicate:</p>`
        break
      default:
        return `<p>${new Intl.ListFormat().format(models.map(model => `@${model.username}`))} have implemented open-source models based on this paper. Run them on Replicate:</p>`
    }
  }

  function noModelsFound(models) {
    if (models.length === 0) {
      return `<p>
        No demos found for this article. You can <a href="https://replicate.com/docs/arxiv?utm_source=arxiv&arxiv_paper_id=${arxivPaperId}">add one here</a>.
      </p>`
    } else {
      return ``
    }
  }

  function renderModel(model) {
    return `
      <div class="replicate-model">
        <a href="${model.absolute_url}?utm_source=arxiv">
          <img src="${model.cover_image}" class="replicate-model-image" />
        </a>
        <div class="replicate-model-details">
          <a href="${model.absolute_url}?utm_source=arxiv">
            <h3 class="replicate-model-details-heading">${model.username}/${model.name}</h3>
          </a>
          <p>${model.description}</p>

          <p class="replicate-model-prediction-count">
            ${rocketIcon()} 
            ${new Intl.NumberFormat().format(Number(model.prediction_count || 0))} 
            run${Number(model.prediction_count) === 1 ? "" : "s"}
          </p>
        </div>
      </div>
    `
  }

  function rocketIcon() {
    return `
      <svg class="replicate-model-prediction-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
        <path fill-rule="evenodd" d="M20.322.75a10.75 10.75 0 00-7.373 2.926l-1.304 1.23A23.743 23.743 0 0010.103 6.5H5.066a1.75 1.75 0 00-1.5.85l-2.71 4.514a.75.75 0 00.49 1.12l4.571.963c.039.049.082.096.129.14L8.04 15.96l1.872 1.994c.044.047.091.09.14.129l.963 4.572a.75.75 0 001.12.488l4.514-2.709a1.75 1.75 0 00.85-1.5v-5.038a23.741 23.741 0 001.596-1.542l1.228-1.304a10.75 10.75 0 002.925-7.374V2.499A1.75 1.75 0 0021.498.75h-1.177zM16 15.112c-.333.248-.672.487-1.018.718l-3.393 2.262.678 3.223 3.612-2.167a.25.25 0 00.121-.214v-3.822zm-10.092-2.7L8.17 9.017c.23-.346.47-.685.717-1.017H5.066a.25.25 0 00-.214.121l-2.167 3.612 3.223.679zm8.07-7.644a9.25 9.25 0 016.344-2.518h1.177a.25.25 0 01.25.25v1.176a9.25 9.25 0 01-2.517 6.346l-1.228 1.303a22.248 22.248 0 01-3.854 3.257l-3.288 2.192-1.743-1.858a.764.764 0 00-.034-.034l-1.859-1.744 2.193-3.29a22.248 22.248 0 013.255-3.851l1.304-1.23zM17.5 8a1.5 1.5 0 11-3 0 1.5 1.5 0 013 0zm-11 13c.9-.9.9-2.6 0-3.5-.9-.9-2.6-.9-3.5 0-1.209 1.209-1.445 3.901-1.49 4.743a.232.232 0 00.247.247c.842-.045 3.534-.281 4.743-1.49z"></path>
      </svg>
    `
  }

})();