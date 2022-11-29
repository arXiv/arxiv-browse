// Labs integration for displaying video casts from sciencecast.org

 (function () {
     const container = document.getElementById("sciencecast-output")
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

     const sciencecastApiHost = "https://sciencecast.org/api/v1";
     const sciencecastCastsUrl = `${sciencecastApiHost}/arxiv/paper/${arxivPaperId}/casts`;

     // Fetch linked casts

     (async () => {
       let response = await fetch(sciencecastCastsUrl);
       if (!response.ok) {
         console.error(`Unable to fetch data from ${sciencecastCastsUrl}`)
         render([]);
         return;
       }
       let casts = await response.json();
       if (casts.length === 0) {
         render([]);
         return;
       }
       render(casts);
     })()

     // Generate HTML, sanitize it to prevent XSS, and inject into the DOM
     function render(casts) {
       container.innerHTML = window.DOMPurify.sanitize(`
           ${summary(casts)}
           ${renderCasts(casts)}
       `, { ADD_ATTR: ['target'] })
     }

     function summary(casts) {
       switch (casts.length) {
         case 0:
           return `<h3 class="sciencecast-summary">No ScienceCasts found for this paper</h3>
           <p> You can <a href="https://sciencecast.org">add one here</a>.</p>`
           break
         case 1:
           return `<h3 class="sciencecast-summary">Related ScienceCast</h3>`
           break
         default:
           return `<p class="sciencecast-summary">Related ScienceCasts (${casts.length})</p>`
       }
     }

     function renderCasts(casts) {
       return casts.map(m => renderCast(m)).join("\n")
     }

     function renderCast(cast) {
       return `
         <div class="sciencecast-cast">
           <a href="${cast.link}" target='_blank'>
             <img class="sciencecast-thumbnail" src=${cast.thumbnail} width='400'>
           </a>
         </div>
       `
     }
})();
