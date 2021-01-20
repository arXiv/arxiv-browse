(function () {
  var $output = $('#connectedpapers-output');

  if ($output.html() != '') {
    // Toggled off
    $output.html('');
    return;
  }

  $output.html('<p>Loading...</p>');

  const REST_ADDR = 'https://rest.migration.connectedpapers.com/';
  const CONNECTED_PAPERS_ADDR = 'https://www.connectedpapers.com/';
  const ARXIV_THUMBNAILS_ADDR = CONNECTED_PAPERS_ADDR + 'arxiv_thumbnails/';
  const NUMBER_OF_THUMBNAILS = 18;
  
  var arxivId = window.location.pathname.split('/').reverse()[0];
  var arxivIdToCPIdUrl = REST_ADDR + '?arxiv=' + arxivId;
  var communicationErrorHtml = '<p>Oops, seems like communication with the Connected Papers server is down.</p>';
  var idNotRecognizedHtml = '<p>Seems like this paper is still not in our database. Please try again in a few days.</p>';
  
  
  $.get(arxivIdToCPIdUrl).done(translationResponse => {
    if ($output.html() == '') {
      // Toggled off
      return;
    }
    if (translationResponse == null) {
      $output.html(idNotRecognizedHtml);
      return;
    }
    var paperId = translationResponse.paperId;
    var title = translationResponse.title;

    if (paperId.length == 0 || title.length == 0) {
      $output.html(idNotRecognizedHtml);
      return;
    }

    var versionsFetchUrl = REST_ADDR + '?versions=' + paperId;

    $.get(versionsFetchUrl).done(versionsResponse => {
      if ($output.html() == '') {
        // Toggled off
        return;
      }

      var graphUrl = CONNECTED_PAPERS_ADDR + 'main/' + paperId + '/arxiv';
      var buildGraphLinkHtml = '<a href="' + graphUrl + '" target="_blank"><p style="margin:0;">View graph for ' + 
                                title + '</p></a>';
      var seeGraphLinkHtml = '<a href="' + graphUrl + '" target="_blank"><p style="margin:0;">View graph for ' +
                              title + '</p></a>';
      var graphNotVisual = '<p>Seems like this paper is still not in our database. Please try again in a few days.</p>';

      // A string to int hash algorithm
      // https://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript
      function cyrb53(str, seed = 0) {
        var h1 = 0xdeadbeef ^ seed, h2 = 0x41c6ce57 ^ seed;
        for (var i = 0; i < str.length; i++) {
          var ch = str.charCodeAt(i);
          h1 = Math.imul(h1 ^ ch, 2654435761);
          h2 = Math.imul(h2 ^ ch, 1597334677);
        }
        h1 = Math.imul(h1 ^ (h1>>>16), 2246822507) ^ Math.imul(h2 ^ (h2>>>13), 3266489909);
        h2 = Math.imul(h2 ^ (h2>>>16), 2246822507) ^ Math.imul(h1 ^ (h1>>>13), 3266489909);
        return 4294967296 * (2097151 & h2) + (h1>>>0);
      };

      var selected_thumbnail_num = Math.abs(cyrb53(arxivId)) % NUMBER_OF_THUMBNAILS;

      var chosenGraph = ARXIV_THUMBNAILS_ADDR + 'g' + selected_thumbnail_num + '.jpg';
      var choserGraphHtml = '<a href="' + graphUrl + '" target="_blank"><img src="' + chosenGraph +
                            '" alt="Example graph image" width="120" height="100" style="border: 1px solid #D2D2D2;"></a>';

      var containerDivStyle = '"display: flex; flex-flow: row; padding: 24px 10px;"';
      var infoLine = '<p style="font-size: 12px; opacity: 0.5; margin-top: 0; margin-bottom: 10px;">See related papers to:</p>';

      var textDivOpen = '<div style="display: flex; flex-flow: column; padding: 0px 25px;">';
      var buildGraphTextDiv = textDivOpen + infoLine + buildGraphLinkHtml + '</div>';
      var seeGraphTextDiv = textDivOpen + infoLine + seeGraphLinkHtml + '</div>';

      var buildGraphHtml = '<div style=' + containerDivStyle + '>' + choserGraphHtml + buildGraphTextDiv + '</div>';
      var seeGraphHtml = '<div style=' + containerDivStyle + '>' + choserGraphHtml + seeGraphTextDiv + '</div>';

      if (versionsResponse == null) {
        // Graph not yet built ever
        $output.html(buildGraphHtml);
        return;
      }
      var versionsData = versionsResponse.result_dates;
      if (versionsData.length == 0) {
        // Graph not yet built ever
        $output.html(buildGraphHtml);
        return;
      }
      var mostRecentVersion = versionsData[versionsData.length - 1];
      if (mostRecentVersion.visual) {
        // Graph already built, ready to be shown
        $output.html(seeGraphHtml);
        return;
      }
      if (versionsResponse.rebuild_available) {
        // Graph non-available, but rebuild available
        $output.html(buildGraphHtml);
        return;
      }
      // Graph non-available
      $output.html(graphNotVisual);
    }).fail(versionsResponse => {
      $output.html(communicationErrorHtml);
    })
  }).fail(translationResponse => {
    $output.html(communicationErrorHtml);
  });
})();
