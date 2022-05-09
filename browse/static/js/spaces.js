// Labs integration for displaying machine learning demos from huggingface.co/spaces

(function () {
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

  const huggingfaceApiHost = "https://huggingface.co/api";
  const huggingfaceSpacesHost = "https://huggingface.co/spaces";
  const huggingfaceModelsFromPaperApi = `${huggingfaceApiHost}/models?filter=arxiv:${arxivPaperId}`;

  // Search the HF Spaces API for models that implement this paper

  (async () => {
    let response = await fetch(huggingfaceModelsFromPaperApi);
    if (!response.ok) {
      console.error(`Unable to fetch model data from ${huggingfaceModelsFromPaperApi}`)
      render([]);
      return;
    }
    let models = await response.json();
    if (models.length === 0) {
      render([]);
      return;
    }
    const model_ids = models.map(m => m.id).join(",");
    const huggingfaceSpacesFromModelsApi = `${huggingfaceApiHost}/spaces?models=or:${model_ids}&full=true&sort=likes&direction=-1`;
    response = await fetch(huggingfaceSpacesFromModelsApi);
    if (!response.ok) {
      console.error(`Unable to fetch spaces data from ${huggingfaceSpacesFromModelsApi}`)
      render([]);
      return;
    }
    const spaces_data = await response.json();
    render(spaces_data);
  })()

  // Generate HTML, sanitize it to prevent XSS, and inject into the DOM
  function render(models) {
    container.innerHTML = window.DOMPurify.sanitize(`
        ${summary(models)}
        ${renderModels(models)}
      `)
  }

  function summary(models) {
    switch (models.length) {
      case 0:
        return `<p class="spaces-summary">
        No Spaces demos found for this article. You can <a href="https://huggingface.co/new-space">add one here</a>.
        </p>`
        break
      case 1:
        return `<p class="spaces-summary">@${models[0].author} has implemented an open-source demo based on this paper. Run it on Spaces:</p>`
        break
      default:
        return `<p class="spaces-summary">There are ${models.length} open-source demos based on this paper. Run them on Spaces:</p>`
    }
  }

  function renderModels(models) {
    const visibleModels = 10;
    return models.slice(0, visibleModels).map(m => renderModel(m)).join("\n") + (models.length > visibleModels ? `
      <input id="spaces-load-all-checkbox" class="spaces-load-all-checkbox" type="checkbox">
      <label for="spaces-load-all-checkbox" class="spaces-load-all-label">
          Load all demos
      </label>
      <div class="spaces-all-demos">
        ${models.slice(visibleModels).map(m => renderModel(m)).join("\n")}
      </div>
    `: "")
  }

  function renderModel(model) {
    const huggingfaceSpaceThumbnail = `https://thumbnails.huggingface.co/social-thumbnails/spaces/${model.id}.png`;
    return `
      <div class="spaces-model">
        <a href="${huggingfaceSpacesHost}/${model.id}">
          <img class="spaces-thumbnail" src=${huggingfaceSpaceThumbnail}>
        </a>
        <div class="spaces-model-details">
          <a href="${huggingfaceSpacesHost}/${model.id}">
            <h3 class="spaces-model-details-heading">${model.id}</h3>
          </a>
          <p class="spaces-model-title">${model.cardData.title}</p>
          <p class="spaces-model-subheader">Created ${(new Date(model.lastModified)).toLocaleDateString()} &bull; ${model.sdk}</p>
        </div>
      </div>
    `
  }
})();