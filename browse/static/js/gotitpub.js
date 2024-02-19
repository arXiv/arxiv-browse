 (function () {
     const container = document.getElementById("gotitpub-output")
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

     const gotitpubApi = `https://gotit.pub/api/status/${arxivPaperId}`;
     const gotitpubUrl = `https://gotit.pub/pdf/${arxivPaperId}`;
     

     (async () => {
       let response = await fetch(gotitpubApi);
       console.log('response', response);
       if (!response.ok) {
         console.error(`Unable to fetch data from ${gotitpubApi}`)
         render(0);
         return;
       }
       let result = await response.json();
       if (result.conversations && result.conversations > 0) {
         render(result.conversations);
         return;
       }
       render(0);
     })()

     // Generate HTML, sanitize it to prevent XSS, and inject into the DOM
     function render(conversations) {
       container.innerHTML = window.DOMPurify.sanitize(`
       <h2 class="gotitpub-logo">gotit.pub</h2>
           ${summary(conversations)}
       `, { ADD_ATTR: ['target'] })
     }

     function summary(conversations) {
       switch (conversations) {
         case 0:
           return `<h3 class="gotitpub-summary">No conversations found for this paper</h3>
           <p> Annotate this article with questions or comments at <a href="${gotitpubUrl}" target="_blank">Gotit.pub</a>.</p>`
           break
         case 1:
           return `<h3 class="gotitpub-summary">There is 1 conversation for this paper on Gotit.pub</h3>
           <p> See more on <a href="${gotitpubUrl}" target="_blank">Gotit.pub</a>.</p>`
           break
         default:
          return `<h3 class="gotitpub-summary">There are ${conversations} conversations for this paper on Gotit.pub</h3>
          <p> See more on <a href="${gotitpubUrl}" target="_blank">Gotit.pub</a>.</p>`
       }
     }
})();
