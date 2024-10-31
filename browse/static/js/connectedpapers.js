(function () {

  const $output = $('#connectedpapers-output');

  if ($output.html() != '') {
    // Toggled off
    $output.html('');
    return;
  }

  const scriptPath = document.getElementById('connectedpapers-toggle').attributes["data-script-url"].value;
  const scriptDir = scriptPath.substr(0, scriptPath.lastIndexOf('/'));

  const cssLoader = '<link rel="stylesheet" type="text/css" href="' + scriptDir + '/connectedpapers.css"/>';
  const connectedPapersTitle = '<h3>Connected Papers</h3>';
  const htmlPrefix = cssLoader + connectedPapersTitle;
  const loadingHtml = '<p>Loading...</p>';
  
  $output.html(htmlPrefix + loadingHtml);


  const REST_ADDR = 'https://rest.prod.connectedpapers.com/';
  const CONNECTED_PAPERS_ADDR = 'https://www.connectedpapers.com/';
  const ARXIV_THUMBNAILS_ADDR = CONNECTED_PAPERS_ADDR + 'arxiv_thumbnails/';
  const NUMBER_OF_THUMBNAILS = 18;
  
  const arxivId = window.location.pathname.split('/').reverse()[0];
  const arxivIdToCPIdUrl = REST_ADDR + 'id_translator/arxiv/' + arxivId;
  const communicationErrorHtml = '<p>Oops, seems like communication with the Connected Papers server is down.</p>';
  const idNotRecognizedHtml = '<p>Seems like this paper is still not in our database. Please try again in a few' +
                              ' days.</p>';
  
  
  $.get(arxivIdToCPIdUrl).done(translationResponse => {
    if ($output.html() == '') {
      // Toggled off
      return;
    }
    if (translationResponse == null) {
      $output.html(htmlPrefix + idNotRecognizedHtml);
      return;
    }
    const paperId = translationResponse.paperId;
    const title = translationResponse.title;

    if (paperId.length == 0 || title.length == 0) {
      $output.html(htmlPrefix + idNotRecognizedHtml);
      return;
    }

    const versionsFetchUrl = REST_ADDR + 'versions/' + paperId + '/1';

    $.get(versionsFetchUrl).done(versionsResponse => {
      if ($output.html() == '') {
        // Toggled off
        return;
      }

      const graphUrl = CONNECTED_PAPERS_ADDR + 'main/' + paperId + '/arxiv';
      
      const paperTitleHtml = '<p id="connectedpapers-title">' + title + '</p>';

      // Not enough references and citations parsed to build a graph
      const graphNotVisual = '<p>Seems like this paper is still not in our database. Please try again in a few' +
                             ' days.</p>';

      // A string to int hash algorithm
      // https://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript
      function cyrb53(str, seed = 0) {
        let h1 = 0xdeadbeef ^ seed, h2 = 0x41c6ce57 ^ seed;
        for (let i = 0; i < str.length; i++) {
          let ch = str.charCodeAt(i);
          h1 = Math.imul(h1 ^ ch, 2654435761);
          h2 = Math.imul(h2 ^ ch, 1597334677);
        }
        h1 = Math.imul(h1 ^ (h1>>>16), 2246822507) ^ Math.imul(h2 ^ (h2>>>13), 3266489909);
        h2 = Math.imul(h2 ^ (h2>>>16), 2246822507) ^ Math.imul(h1 ^ (h1>>>13), 3266489909);
        return 4294967296 * (2097151 & h2) + (h1>>>0);
      };

      const selectedThumbnailNum = Math.abs(cyrb53(arxivId)) % NUMBER_OF_THUMBNAILS;

      const chosenGraphThumbnail = ARXIV_THUMBNAILS_ADDR + 'g' + selectedThumbnailNum + '.jpg';
      const chosenGraphThumbnailHtml = '<img src="' + chosenGraphThumbnail + '" alt="Example graph image" id="connectedpapers-img">';

      const infoLine = '<p id="connectedpapers-description">See related papers to:</p>';

      const buildGraphTextDiv = '<div id="connectedpapers-text-cont">' +
                                  infoLine +
                                  paperTitleHtml +
                                '</div>';

      const buildGraphHtml =  '<div id="connectedpapers-width-limiter">' +
                                '<a id="connectedpapers-link" href="' +graphUrl + '" target="_blank">' +
                                  '<div id="connectedpapers-container">' +
                                    chosenGraphThumbnailHtml + buildGraphTextDiv +
                                  '</div>' +
                                '</a>' +
                              '</div>';

      // Future compatability - different message for built graphs
      const seeGraphHtml = buildGraphHtml;

      if (versionsResponse == null) {
        // Graph not yet built ever
        $output.html(htmlPrefix + buildGraphHtml);
        return;
      }
      const versionsData = versionsResponse.graph_versions;
      if (versionsData.length == 0) {
        // Graph not yet built ever
        $output.html(htmlPrefix + buildGraphHtml);
        return;
      }
      const mostRecentVersion = versionsData[versionsData.length - 1];
      if (mostRecentVersion.is_visual) {
        // Graph already built, ready to be shown
        $output.html(htmlPrefix + seeGraphHtml);
        return;
      }
      if (versionsResponse.rebuild_available) {
        // Graph non-available, but rebuild available
        $output.html(htmlPrefix + buildGraphHtml);
        return;
      }
      // Graph non-available
      $output.html(graphNotVisual);
    }).fail(versionsResponse => {
      $output.html(htmlPrefix + communicationErrorHtml);
    })
  }).fail(translationResponse => {
    $output.html(htmlPrefix + communicationErrorHtml);
  });
})();
