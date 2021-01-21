(function () {

  const $output = $('#connectedpapers-output');

  if ($output.html() != '') {
    // Toggled off
    $output.html('');
    return;
  }

  const script_path = document.getElementById('connectedpapers-toggle').attributes["data-script-url"].value;
  const script_dir = script_path.substr(0, script_path.lastIndexOf('/'));

  const css_loader = '<link rel="stylesheet" type="text/css" href="' + script_dir + '/connectedpapers.css"/>';
  const loading_html = '<p>Loading...</p>';
  
  $output.html(css_loader + loading_html);


  const REST_ADDR = 'https://rest.migration.connectedpapers.com/';
  const CONNECTED_PAPERS_ADDR = 'https://www.connectedpapers.com/';
  const ARXIV_THUMBNAILS_ADDR = CONNECTED_PAPERS_ADDR + 'arxiv_thumbnails/';
  const NUMBER_OF_THUMBNAILS = 18;
  
  const arxivId = window.location.pathname.split('/').reverse()[0];
  const arxivIdToCPIdUrl = REST_ADDR + '?arxiv=' + arxivId;
  const communicationErrorHtml = '<p>Oops, seems like communication with the Connected Papers server is down.</p>';
  const idNotRecognizedHtml = '<p>Seems like this paper is still not in our database. Please try again in a few days.</p>';
  
  
  $.get(arxivIdToCPIdUrl).done(translationResponse => {
    if ($output.html() == '') {
      // Toggled off
      return;
    }
    if (translationResponse == null) {
      $output.html(css_loader + idNotRecognizedHtml);
      return;
    }
    const paperId = translationResponse.paperId;
    const title = translationResponse.title;

    if (paperId.length == 0 || title.length == 0) {
      $output.html(css_loader + idNotRecognizedHtml);
      return;
    }

    const versionsFetchUrl = REST_ADDR + '?versions=' + paperId;

    $.get(versionsFetchUrl).done(versionsResponse => {
      if ($output.html() == '') {
        // Toggled off
        return;
      }

      const graphUrl = CONNECTED_PAPERS_ADDR + 'main/' + paperId + '/arxiv';
      const buildGraphLinkHtml = '<p style="margin: 0">' + title + '</p><p style="margin-top: 5px"><a href="' + graphUrl + '" target="_blank">View graph</a></p>';
      
      // Future compatible support for different messages for existing and nonexisting graphs
      const seeGraphLinkHtml = buildGraphLinkHtml;
      const graphNotVisual = '<p>Seems like this paper is still not in our database. Please try again in a few days.</p>';

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

      const selected_thumbnail_num = Math.abs(cyrb53(arxivId)) % NUMBER_OF_THUMBNAILS;

      const chosenGraph = ARXIV_THUMBNAILS_ADDR + 'g' + selected_thumbnail_num + '.jpg';
      const choserGraphHtml = '<a href="' + graphUrl + '" target="_blank"><img src="' + chosenGraph + '" alt="' +
                              'Example graph image" width="120" height="100" style="border: 1px solid #D2D2D2;"></a>';

      const containerDivStyle = '"display: flex; flex-flow: row; padding: 24px 10px;"';
      const infoLine = '<p class="info-line">See related papers to:</p>';

      const textDivOpen = '<div style="display: flex; flex-flow: column; padding: 0px 25px;">';
      const buildGraphTextDiv = textDivOpen + infoLine + buildGraphLinkHtml + '</div>';
      const seeGraphTextDiv = textDivOpen + infoLine + seeGraphLinkHtml + '</div>';

      const buildGraphHtml = '<div style=' + containerDivStyle + '>' + choserGraphHtml + buildGraphTextDiv + '</div>';
      const seeGraphHtml = '<div style=' + containerDivStyle + '>' + choserGraphHtml + seeGraphTextDiv + '</div>';

      if (versionsResponse == null) {
        // Graph not yet built ever
        $output.html(css_loader + buildGraphHtml);
        return;
      }
      const versionsData = versionsResponse.result_dates;
      if (versionsData.length == 0) {
        // Graph not yet built ever
        $output.html(css_loader + buildGraphHtml);
        return;
      }
      const mostRecentVersion = versionsData[versionsData.length - 1];
      if (mostRecentVersion.visual) {
        // Graph already built, ready to be shown
        $output.html(css_loader + seeGraphHtml);
        return;
      }
      if (versionsResponse.rebuild_available) {
        // Graph non-available, but rebuild available
        $output.html(css_loader + buildGraphHtml);
        return;
      }
      // Graph non-available
      $output.html(graphNotVisual);
    }).fail(versionsResponse => {
      $output.html(css_loader + communicationErrorHtml);
    })
  }).fail(translationResponse => {
    $output.html(css_loader + communicationErrorHtml);
  });
})();
