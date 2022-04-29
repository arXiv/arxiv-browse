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
    const huggingfaceSpacesFromModelsApi = `${huggingfaceApiHost}/spaces?models=${model_ids}`;
    const response = await fetch(huggingfaceSpacesFromModelsApi);
    if (!response.ok) {
      console.error(`Unable to fetch spaces data from ${huggingfaceSpacesFromModelsApi}`)
      render([]);
      return;
    }
    const spaces = await response.json();
    let spaces_data = [];
    await Promise.all(spaces.map(async (space) => {
      const huggingfaceSpaceApi = `${huggingfaceApiHost}/spaces/${space.id}`
      const response = await fetch(huggingfaceSpaceApi);
      if (!response.ok) {
        console.error(`Unable to fetch data from ${huggingfaceSpaceApi}`);
        return;
      }
      let space_data = await response.json();
      spaces_data.push(space_data);
    }));
    render(spaces_data);
  })()

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
    const tailwind_color_map = {
      slate: "#475569",
      gray: "#4b5563",
      zinc: "#52525b",
      neutral: "#525252",
      stone: "#57534e",
      red: "#dc2626",
      orange: "#ea580c",
      amber: "#d97706",
      yellow: "#ca8a04",
      lime: "#65a30d",
      green: "#16a34a",
      emerald: "#059669",
      teal: "#0d9488",
      cyan: "#0891b2",
      sky: "#0284c7",
      blue: "#2563eb",
      indigo: "#4f46e5",
      violet: "#7c3aed",
      purple: "#9333ea",
      fuchsia: "#475569",
      pink: "#c026d3",
      rose: "#e11d48"
    };
    const getColor = (color) => {
      if (color in tailwind_color_map) {
        return tailwind_color_map[color];
      } else {
        return tailwind_color_map["gray"];
      }
    }
    return `
      <div class="spaces-model">
        <a class="spaces-card" href="${huggingfaceSpacesHost}/${model.id}" 
          style="background: -webkit-linear-gradient(315deg,${getColor(model.cardData.colorFrom)},${getColor(model.cardData.colorTo)}); background: linear-gradient(315deg,${getColor(model.cardData.colorFrom)},${getColor(model.cardData.colorTo)});"
        >
          <span class="spaces-emoji">${model.cardData.emoji}</span>
          <span class="spaces-title">${model.cardData.title}</span>
        </a>
        <div class="spaces-model-details">
          <a href="${huggingfaceSpacesHost}/${model.id}">
            <h3 class="spaces-model-details-heading">${model.id}</h3>
          </a>
          <p class="spaces-model-sdk">A ${model.cardData.sdk} demo.</p>
        </div>
      </div>
    `
  }
})();