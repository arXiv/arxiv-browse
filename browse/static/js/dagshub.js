(function() {
	const container = document.getElementById("dagshub-output")
	const containerAlreadyHasContent = container.innerHTML.trim().length > 0
	console.log("Invoked!")
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
	
	const dagshubAPIHost = "https://dagshub.com/api/v1"
	const dagshubRepositoryFromPaperApi = `${dagshubAPIHost}/repos/arxiv/${arxivPaperId}`;
	
	// Search DagsHub for a project that implements the paper
	(async () => {
		let response = await fetch(dagshubRepositoryFromPaperApi);
		if (!response.ok) {
		  console.error(`Unable to fetch data from ${dagshubRepositoryFromPaperApi}`)
		  render({"DagsHub is not available": "an error occurred while fetching"});
		  return;
		}
		const dagshub_data = await response.json();
		render(dagshub_data);
	  })()

	  // Generate HTML, sanitize it to prevent XSS, and inject into the DOM
	  function render(data) {
		container.innerHTML = window.DOMPurify.sanitize(`
			${summary(data)}
		  `)
	  }
	
	  function summary(data) {
		let output = ``
		for (const key in data) {
			output += `
				<h3>${key}</h3>
				<p>${data[key]}</p>
				`
		}
		return output;
	  }
})();