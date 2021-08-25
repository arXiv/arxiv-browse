(function () {
    const metadoi = document.head.querySelector(`[name="citation_doi"]`);
    const doi = metadoi ? metadoi.content : '';

    const scriptPath = document.getElementById('scite-toggle').attributes["data-script-url"].value;
    const scriptDir = scriptPath.substr(0, scriptPath.lastIndexOf('/'));
    const cssTag = `<link rel="stylesheet" type="text/css" href="${scriptDir}/scite.css"/>`;

    const $output = $('#scite-open-in');
    if ($output.html() != '') {
        // Toggled off
        $output.html('');
        return;
    }

    if (doi) {
        $output.html(cssTag + `
            <div
                class="scite-badge"
                data-doi="${doi}"
                data-layout="vertical"
                data-show-zero="false"
                data-small="false"
                data-show-labels="true"
                data-campaign="arxiv"
                data-tooltip-placement="right"
            >
            </div>
            <script async type="application/javascript" src="https://cdn.scite.ai/badge/scite-badge-latest.min.js"></script>
        `);
        return;
    }

    $output.html(cssTag + `
        <div class="scite-no-doi">
            <img class="scite-tally-logo" width="100px" src="https://cdn.scite.ai/assets/images/logo.svg">
            <h3 class="scite-no-doi-header">No DOI found</h3>
            <p class="scite-no-doi-explainer">
                scite only processes publications with a DOI and there is no DOI available for this paper. Please check back when a DOI is available.
                In the meantime, here is an example of what scite Smart Citations look like: <a href="https://scite.ai/reports/association-between-amygdala-hyperactivity-to-gVamGz?utm_campaign=arxiv" rel="noopener" target="_blank">Example Report</a></p></div>
            </p>
        <div>
    `);
})();
