// Labs integration for displaying machine learning demos from huggingface.co/spaces

(function () {
    console.log("Getting Spaces")
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
    const arxivPaperId = "1810.04805" ///params.get("override_paper_id") || window.location.pathname.split('/').reverse()[0]
    if (!arxivPaperId) return
  
    const huggingfaceApiHost = "https://huggingface.co/api";
    const huggingfaceSpacesHost = "https://huggingface.co/spaces";
    const huggingfaceSpacesFromPaperApi = `${huggingfaceApiHost}/arxiv/${arxivPaperId}/repos`;
  
    // Search the HF Spaces API for demos that cite this paper
  
    (async () => {
      let response = await fetch(huggingfaceSpacesFromPaperApi);
      if (!response.ok) {
        console.error(`Unable to fetch spaces data from ${huggingfaceSpacesFromPaperApi}`)
        render([]);
        return;
      }
      
      let paper_data = await response.json();
      if (! paper_data.hasOwnProperty("spaces")) {
        console.error(`Paper has no spaces associated`)
        render([]);
        return;
      }
      
      let spaces_data = await paper_data.spaces;
      if (spaces_data.length === 0) {
        render([]);
        return;
      }
      // To remove after https://github.com/huggingface/moon-landing/pull/6108 
      let new_data = spaces_data.sort(function(a, b){
          return b.likes - a.likes;
      });

      /// TODO: Update this to use Spaces filter rather than by linked model
      let models = await paper_data.models;
      const model_ids = models.map(m => m.id).join(",");
      const huggingfaceSpacesFromModelsLink = `${huggingfaceSpacesHost}/?sort=likes&models=or:${model_ids}`;

      render(new_data, huggingfaceSpacesFromModelsLink);
    })()
  
    // Generate HTML, sanitize it to prevent XSS, and inject into the DOM
    function render(models, spaces_link) {
      container.innerHTML = window.DOMPurify.sanitize(`
          ${summary(models)}
          ${renderModels(models, spaces_link)}
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
  
    function renderModels(models, spaces_link) {
      const visibleModels = 5;
      return models.slice(0, visibleModels).map(m => renderModel(m)).join("\n") + (models.length > visibleModels ? `
        <a href="${spaces_link}" target="_blank">
          <button class="spaces-load-all-link">
            View all demos
          </button>
        </a>
      `: "")
    }
  
    function renderModel(model) {
      const huggingfaceSpaceThumbnail = `https://thumbnails.huggingface.co/social-thumbnails/spaces/${model.id}.png`;
      return `
        <div class="spaces-model">
          <a target="_blank" href="${huggingfaceSpacesHost}/${model.id}">
            <img class="spaces-thumbnail" src=${huggingfaceSpaceThumbnail}>
          </a>
          <div class="spaces-model-details">
            <a target="_blank" href="${huggingfaceSpacesHost}/${model.id}">
              <h3 class="spaces-model-details-heading">${model.id}</h3>
            </a>
            <p class="spaces-model-title">${model.cardData.title}</p>
            <p class="spaces-model-subheader">Created ${(new Date(model.lastModified)).toLocaleDateString()} &bull; ${model.sdk}</p>
          </div>
        </div>
      `
    }
  })();
