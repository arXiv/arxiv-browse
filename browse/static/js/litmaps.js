(function () {
    const arxivId = document.head.querySelector("[name~=citation_arxiv_id][content]").content;
    const litmapsBaseUrl = 'https://api.litmaps.co';
    const litmapsAppUrl = 'https://app.litmaps.co';
    const litmapsCheckSeed = `${litmapsBaseUrl}/article/arxiv:${arxivId}/seed/`;
    const litmapsFetchArticle = `${litmapsBaseUrl}/article/arxiv:${arxivId}/`;
    const scriptPath = document.getElementById('litmaps-toggle').attributes["data-script-url"].value;
    const scriptDir = scriptPath.substr(0, scriptPath.lastIndexOf('/'));
    const cssTag = `<link rel="stylesheet" type="text/css" href="${scriptDir}/litmaps.css"/>`;
    var $output = $('#litmaps-open-in');
  
    if ($output.html() != '') {
        // Toggled off
        $output.html('');
        return;
    }

    $output.html(cssTag + `<div id="litmaps_error_group"><img id="litmaps_error_logo" src="https://www.litmaps.co/litmaps_logo_black.svg" alt="Litmaps Logo" /><p id="litmaps_body">Loading...</p></div>`);

    $.get(litmapsCheckSeed).done(function (checkResponse) {
        $.get(litmapsFetchArticle).done(function (response) {
            console.log(response);
            renderCard($output, response, checkResponse);
        })
    }).fail(function (response) {
        renderNotFoundError();
        return;
    });

    function renderCard($output, articleDetails, isGoodSeedResponse) {
        $output.html('');
        if (isGoodSeedResponse['goodSeedArticle'] === false) {
            $output.html(cssTag + `<div id="litmaps_error_group"><img id="litmaps_error_logo" src="https://www.litmaps.co/litmaps_logo_black.svg" alt="Litmaps Logo" /><p id="litmaps_body">This article does not have many references or citations, therefore it is not an ideal seed article. <a href="${litmapsAppUrl}?seedId=${articleDetails.id}" title="Build Literature Map from “${articleDetails.title}”" rel="noopener noreferrer" target="_blank">Try anyway?</a></p></div>`);
            return; 
        }
        if (articleDetails === null) {
            renderNotFoundError();
            return;
        }
        $output.html(cssTag + `<div id="litmaps_card_container"><a id="litmaps_card_link" href="${litmapsAppUrl}?seedId=${articleDetails.id}" title="Build Literature Map from “${articleDetails.title}”" rel="noopener noreferrer" target="_blank"><div id="litmaps_card"><img id="litmaps_map_placeholder" src="https://www.litmaps.co/arxiv-litmaps-placeholder.png" alt="Placeholder image of Literature Map for “${articleDetails.title}”" /><h3 id="litmaps_card_title">Build Literature Map from “${articleDetails.title}”</h3><img id="litmaps_card_logo" src="https://www.litmaps.co/litmaps_logo_black.svg" alt="Litmaps Logo" /></div></a></div>`);
        return;
    }

    function renderNotFoundError() {
        $output.html(cssTag + `<div id="litmaps_error_group"><img id="litmaps_error_logo" src="https://www.litmaps.co/litmaps_logo_black.svg" alt="Litmaps Logo" /><p id="litmaps_body">This article is not currently in the Litmaps database. Please check again in a few days.</p></div>`);
    }
})();
