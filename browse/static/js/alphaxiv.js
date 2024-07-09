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
     const urlList = window.location.pathname.split('/').reverse()
     let arxivPaperId = urlList[0]
     if (!arxivPaperId) return

    // include the hep-th, math, etc subject tag
    if (urlList.length > 0 && urlList[1] != 'abs') {
        arxivPaperId = (urlList[1] + "_") + arxivPaperId  
    }

    let versionlessPaperId = arxivPaperId;
    if (versionlessPaperId.includes("v")) {
        versionlessPaperId = versionlessPaperId.substring(0, versionlessPaperId.indexOf("v"))
    }

    const alphaxivApi = `https://alphaxiv.org/api/prod/getpaperinfo/${arxivPaperId}`
    let alphaXivUrl = `https://alphaxiv.org/abs/${versionlessPaperId}`;


    (async () => {
       let response = await fetch(alphaxivApi);
       if (!response.ok) {
         console.error(`Unable to fetch data from ${alphaxivApi}`)
         render(0, false);
         return;
       }
       let result = await response.json();
       if (result.returnVersion > 0) {
         alphaXivUrl = alphaXivUrl + "v" + result.returnVersion;
         render(result.numQuestions, result.hasClaimedAuthorship);
         return;
       }
       render(0, false);
    })()

     // Generate HTML, sanitize it to prevent XSS, and inject into the DOM
     function render(numComments, hasClaimedAuthorship) {
       container.innerHTML = window.DOMPurify.sanitize(`
       <h2 class="alphaxiv-logo">alphaXiv</h2>
           ${html(numComments, hasClaimedAuthorship)}
       `, { ADD_ATTR: ['target'] })
     }

     function html(numComments, hasClaimedAuthorship) {
        let resultStr = ""
        if (numComments == 0) {
            resultStr += `<h3 class="alphaxiv-summary">Comment directly on top of arXiv papers</h3>
            <p> No comments yet for this paper. View recent comments <a href="https://alphaxiv.org/explore" target="_blank">on other papers here</a>.</p>`
        } else if (numComments == 1) {
            resultStr += `<h3 class="alphaxiv-summary">There is 1 comment on this paper</h3>
            <p> View comments on <a href="${alphaXivUrl}" target="_blank">alphaXiv</a> and add your own!</p>`
        } else {
            resultStr += `<h3 class="alpahxiv-summary">There are ${numComments} comments for this paper on alphaXiv</h3>
            <p> View comments on <a href="${alphaXivUrl}" target="_blank">alphaXiv</a>.</p>`
        }
        if (hasClaimedAuthorship == true) {
            resultStr += `<p> For this paper, the author is present on alphaXiv and will be notified of new comments.`
            if (numComments == 0) {
                resultStr += ` See <a href="${alphaXivUrl}" target="_blank">here</a>.</p>`
            } else {
                resultStr += `</p>`
            }
        }

        return resultStr
     }
})();
