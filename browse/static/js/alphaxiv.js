 (function () {
     const container = document.getElementById("alphaxiv-output")
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

     let versionlessPaperId = arxivPaperId;
     if (versionlessPaperId.includes("v")) {
        versionlessPaperId = versionlessPaperId.substring(0, versionlessPaperId.indexOf("v"))
     }

     const alphaxivApi = `https://dev.alphaxiv.org/api/dev/getpaperinfo/${arxivPaperId}`
     let alphaXivUrl = `https://alphaxiv.org/abs/${versionlessPaperId}`;

     (async () => {
       let response = await fetch(alphaxivApi);
       console.log('response', response);
       if (!response.ok) {
         console.error(`Unable to fetch data from ${alphaxivApi}`)
         render(0);
         return;
       }
       let result = await response.json();
       if (result.numQuestions && result.numQuestions > 0) {
          alphaXivUrl = alphaXivUrl + result.returnVersion;
         render(result.numQuestions);
         return;
       }
       render(0);
     })()

     // Generate HTML, sanitize it to prevent XSS, and inject into the DOM
     function render(conversations) {
       container.innerHTML = window.DOMPurify.sanitize(`
       <h2 class="alphaxiv-logo">alphaXiv</h2>
           ${summary(conversations)}
       `, { ADD_ATTR: ['target'] })
     }

     function summary(conversations) {
       switch (conversations) {
         case 0:
           return `<h3 class="alphaxiv-summary">No comments found for this paper</h3>
           <p> Leave comments or public reviews at <a href="${alphaXivUrl}" target="_blank">alphaXiv</a>.</p>`
           break
         case 1:
           return `<h3 class="alphaxiv-summary">There is 1 comment on this paper</h3>
           <p> View comments on <a href="${alphaXivUrl}" target="_blank">alphaXiv</a>.</p>`
           break
         default:
          return `<h3 class="alpahxiv-summary">There are ${conversations} comments for this paper on alphaXiv</h3>
          <p> See more on <a href="${alphaXivUrl}" target="_blank">alphaXiv</a>.</p>`
       }
     }
})();
