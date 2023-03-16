(function (window, userInput, options) {
    // console.log("Influence flower function call");
    const paperTitle = document.head.querySelector("[name~=citation_title][content]").content;
    const INF_FLOWER_REST_URL = 'https://influencemap.cmlab.dev';
    const flowerQuery = `${INF_FLOWER_REST_URL}/query?title=${paperTitle}`;

    function loadStylesheet(id, url) {
      if (document.getElementById(id) != undefined) return;
      var linkElement = document.createElement('link');
      linkElement.setAttribute('rel', 'stylesheet');
      linkElement.setAttribute('type', 'text/css');
      linkElement.setAttribute('href', url);
      linkElement.id = id;
      document.head.appendChild(linkElement);
      return linkElement;
    }

    function loadScript(id, url) {
      if (document.getElementById(id) != undefined) return;
      var scriptElement = document.createElement('script');
      scriptElement.defer = 'defer';
      scriptElement.type = 'text/javascript';
      scriptElement.src = url;
      scriptElement.id = id;
      document.head.appendChild(scriptElement);
      return scriptElement;
    }

    function unloadScript(id) {
      if (document.getElementById(id) != undefined)
        document.getElementById(id).remove();
    }

    var output = document.getElementById('influenceflower-output');
    var output_graph = document.getElementById('influenceflower-output-graph');
    const scriptPath = document.getElementById('influenceflower-toggle').attributes['data-script-url'].value;
    const scriptDir = scriptPath.substr(0, scriptPath.lastIndexOf('/'));
    var flowerData = undefined;

    function loadInfluenceFlowers() {
      loadStylesheet('inf-style', `${scriptDir}/inf-style.css`);
      loadScript('inf-script', `${scriptDir}/inf-script.js`);

      const infflowerLoading = '<p>Generating influence flowers....</p>';
      output.innerHTML = infflowerLoading;

      $.get(flowerQuery).done(function (response) {
        if (response['status'] === 'Success') {
          output.innerHTML = '<p>Influence flowers are visualizations for citation influences '
            + 'among academic entities, including papers, authors, institutions, and research topics. '
            + 'See <a href="https://influencemap.cmlab.dev/" target="_blank">here</a> for more detail.</p>';
          output_graph.style.display='block';
          flowerData = response;
          drawInfluenceFlowers(response);
        } else {
          output.innerHTML = '<p>' + response['status'] + '</p>';
        }
      }).fail(function (response) {
        output.innerHTML = '<p>We are experiencing an internal server error. Please try again later.</p>';
        return;
      });
    }

    function unloadInfluenceFlowers() {
      output.style.display='block';
      output_graph.style.display='none';
      if (output.innerHTML != '') {
        output.innerHTML = '';
        return;
      }
      unloadScript('inf-style');
      unloadScript('inf-script');
    }

    function reloadInfluenceFlowers() {
      if (flowerData === undefined) {
        unloadInfluenceFlowers();
        loadInfluenceFlowers();
      } else {
        drawInfluenceFlowers(flowerData);
      }
    }

    function toggleInfluenceFlowers() {
      var influenceFlowerToggle = document.getElementById('influenceflower-toggle');
      var toggleEnabled = influenceFlowerToggle.classList.contains("enabled");
      if (toggleEnabled) loadInfluenceFlowers();
      else unloadInfluenceFlowers();
    };

    if (window.document.readyState == 'loading') {
      window.addEventListener('load', toggleInfluenceFlowers);
    } else {
      toggleInfluenceFlowers();
      window.addEventListener('resize', reloadInfluenceFlowers);
    }

})(window);
