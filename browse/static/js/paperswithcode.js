(function () {
  var arxivId = window.location.pathname.split('/').reverse()[0];
  var pwcApiUrl = 'https://arxiv.paperswithcode.com/api/v0/repos-and-datasets/' + arxivId;
  var $outputCode = $('#pwc-output');
  var $outputData = $('#pwc-data-output');

  if ($outputCode.html() != '') {
    // Toggled off
    $outputCode.html('');
    $outputData.html('');
    $outputCode.attr("style", "display:none");
    $outputData.attr("style", "display:none");
    return;
  } else {
    $outputCode.attr("style", "");
    $outputData.attr("style", "");
  }

  $.get(pwcApiUrl).done(function (response) {
    renderCode($outputCode, response["code"]);
    renderData($outputData, response["data"]);
  }).fail(function (response) {
    renderCode($outputCode, null);
    $outputData.attr("style", "display:none");
  });

  var icons = {
    github: '<svg xmlns="http://www.w3.org/2000/svg" class="pwc-icon" viewBox="0 0 512 512"><path d="M256 32C132.3 32 32 134.9 32 261.7c0 101.5 64.2 187.5 153.2 217.9a17.56 17.56 0 003.8.4c8.3 0 11.5-6.1 11.5-11.4 0-5.5-.2-19.9-.3-39.1a102.4 102.4 0 01-22.6 2.7c-43.1 0-52.9-33.5-52.9-33.5-10.2-26.5-24.9-33.6-24.9-33.6-19.5-13.7-.1-14.1 1.4-14.1h.1c22.5 2 34.3 23.8 34.3 23.8 11.2 19.6 26.2 25.1 39.6 25.1a63 63 0 0025.6-6c2-14.8 7.8-24.9 14.2-30.7-49.7-5.8-102-25.5-102-113.5 0-25.1 8.7-45.6 23-61.6-2.3-5.8-10-29.2 2.2-60.8a18.64 18.64 0 015-.5c8.1 0 26.4 3.1 56.6 24.1a208.21 208.21 0 01112.2 0c30.2-21 48.5-24.1 56.6-24.1a18.64 18.64 0 015 .5c12.2 31.6 4.5 55 2.2 60.8 14.3 16.1 23 36.6 23 61.6 0 88.2-52.4 107.6-102.3 113.3 8 7.1 15.2 21.1 15.2 42.5 0 30.7-.3 55.5-.3 63 0 5.4 3.1 11.5 11.4 11.5a19.35 19.35 0 004-.4C415.9 449.2 480 363.1 480 261.7 480 134.9 379.7 32 256 32z"></path></svg>',
    gitlab: '<svg xmlns="http://www.w3.org/2000/svg" class="pwc-icon" viewBox="0 0 512 512"><path d="M494.07 281.6l-25.18-78.08c-.13-.72-.34-1.42-.61-2.1l-50.5-156.94c-2.76-8.31-10.49-13.88-19.17-13.82-8.66-.05-16.34 5.6-18.95 13.94l-48.14 149.55H179.56L131.34 44.59c-2.59-8.31-10.23-13.95-18.86-13.94h-.11c-8.69 0-16.39 5.62-19.12 13.95L42.7 201.73c0 .14-.11.26-.16.4l-25.63 79.48c-3.86 11.96.35 25.07 10.44 32.46l221.44 162.41c4 2.92 9.41 2.89 13.38-.07l221.48-162.34c10.09-7.39 14.3-20.51 10.42-32.47m-330.99-64.51l61.72 191.76L76.63 217.09m209.64 191.8l59.19-183.84 2.55-7.96h86.52L300.47 390.44M398.8 59.31l43.37 134.83h-86.82m-31.19 22.87l-43 133.58-25.66 79.55L186.94 217M112.27 59.31l43.46 134.83H68.97M40.68 295.58a6.186 6.186 0 01-2.21-6.9l19.03-59.03 139.58 180.62m273.26-114.69L313.92 410.22l.52-.69L453.5 229.64l19.03 59c.84 2.54-.05 5.34-2.19 6.92"></path></svg>',
    bitbucket: '<svg xmlns="http://www.w3.org/2000/svg" class="pwc-icon" viewBox="0 0 512 512"><path d="M483.13 32.23a19.81 19.81 0 00-2.54-.23h-449C23 31.88 16.12 38.88 16 47.75a11.52 11.52 0 00.23 2.8l65.3 411.25a22.54 22.54 0 007 12.95 20 20 0 0013.5 5.25h313.15a15.46 15.46 0 0015.34-13.42l38.88-247.91H325.19l-18.46 112H205.21l-25.73-148h295.58l20.76-132c1.27-8.75-4.38-17.04-12.69-18.44z"></path></svg>',
    pwc: '<svg xmlns="http://www.w3.org/2000/svg" class="pwc-icon pwc-icon-primary" viewBox="0 0 512 512" ><path stroke="#21cbce" fill="#21cbce" d="M88 128h48v256H88zM232 128h48v256h-48zM160 144h48v224h-48zM304 144h48v224h-48zM376 128h48v256h-48z"></path><path stroke="#21cbce" fill="#21cbce" d="M104 104V56H16v400h88v-48H64V104zM408 56v48h40v304h-40v48h88V56z"></path></svg>'
  }

  function renderCode ($output, data) {
    $output.html('');
    if (data === null) {
      $output.html('<p>This paper has not been found in the Papers with Code database. If you are one of the registered authors of this paper, you can link your code and data on your <a href="https://arxiv.org/user">arxiv user page</a></p>');
      return
    }
    if (data.error) return;

    $output.append('<h3>Official Code</h3>');

    if (data.all_official.length > 0) {
      for (const implementation of data.all_official) {
        let icon = icons.github;
        if (implementation.url.includes('gitlab')) icon = icons.gitlab;
        if (implementation.url.includes('bitbucket')) icon = icons.bitbucket;
        let p = $('<p>');
        let link = $('<a target="_blank"></a>');
        link.attr('href', implementation.url);
        link
          .append(icon)
          .append(document.createTextNode(implementation.url));
        p.append(link);
        $output.append(p);
      }
    } else {
      let link = $('<a target="_blank">you can submit it here</a>');
      link.attr('href', data.paper_url);
      $output
        .append('No official code found; ')
        .append(link);
    }

    if (data.unofficial_count === 0) {
      $output.append('<h3 class="pwc-community-nocode">Community Code</h3>');
      let link = $(`<a target="_blank">${icons.pwc}Papers With Code</a>`);
      link.attr('href', data.paper_url);
      $output
        .append('Submit your implementations of this paper on ')
        .append(link);
    } else {
      $output.append('<h3 class="pwc-community-code">Community Code</h3>');
      let link = $('<a class="pwc-code-link" target="_blank"></a>');
      link.attr('href', data.paper_url);
      link
        .append(icons.pwc)
        .append(document.createTextNode(data.unofficial_count))
        .append(` code implementation${data.unofficial_count > 1 ? 's': ''}`);

      if (data.frameworks.length === 1) {
        link
          .append(' (in ')
          .append(document.createTextNode(data.frameworks[0]))
          .append(')');
      } else if (data.frameworks.length === 2) {
        link
          .append(' (in ')
          .append(document.createTextNode(data.frameworks.join(' and ')))
          .append(')');
      } else if (data.frameworks.length > 2) {
        link
          .append(' (in ')
          .append(document.createTextNode(data.frameworks.slice(0, -1).join(', ')))
          .append(' and ')
          .append(document.createTextNode(data.frameworks[data.frameworks.length - 1]))
          .append(')');
      }

      $output.append(link);
    }
  }

  function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  function mapPWCModalityToDefaultColor(modalities) {
    if(modalities.length > 0) {
      const colors = {
        "images": "#A395C6",
        "audio": "#7A9FB8",
        "videos": "#F37668",
        "interactive": "#A28497",
        "tabular": "#62AEE4",
        "time series": "#FF6B6B",
        "graphs": "#90B06D",
        "texts": "#CD933C",
        "geospatial": "#C87E91",
        "3d": "#DF7C87",
        "parallel corpus": "#8CB369",
      }

      let modality_lower = modalities[0].toLowerCase();
      if (modality_lower in colors) {
        return colors[modality_lower];
      }
    }

    // default color
    return "#A59F78";
  }

  // Create a dataset card
  function makePWCCard (dataObj, isIntroduced) {
    let cardDiv = $('<div class="pwc-data-card">');

    // image
    let imageDiv = $('<div class="pwc-data-card-image">');
    if (dataObj.image !== null) {
      let datasetImage = $('<img>');
      datasetImage.attr("src", dataObj.image);
      imageDiv.append(datasetImage);
    } else {
      // show placeholder image
      let placeholderDiv = $('<div class="pwc-data-card-image-placeholder">');
      let placeholderText = $('<span>');
      placeholderText.append(document.createTextNode(dataObj.name[0]));
      placeholderDiv.append(placeholderText);
      placeholderDiv.attr("style", "background-color:"+mapPWCModalityToDefaultColor(dataObj.modalities));
      imageDiv.append(placeholderDiv);
    }

    // name
    let nameDiv = $('<div class="pwc-data-card-name">');
    let nameA = $('<a class="pwc-data-name" target="_blank">');
    nameA.attr("href", dataObj.url);
    nameA.append(document.createTextNode(dataObj.name));

    // meta line
    let num_papers = dataObj.num_papers - 1;
    let metaDiv = $('<div class="pwc-data-name-meta">');
    if (num_papers === 1) {
      metaDiv.append(document.createTextNode(numberWithCommas(num_papers).concat(" paper also uses this dataset")));
    } else if (num_papers > 1) {
      metaDiv.append(document.createTextNode(numberWithCommas(num_papers).concat(" papers also use this dataset")));
    }

    // assemble name div
    nameDiv.append(nameA);

    // additional is introduced line
    if (isIntroduced) {
      let introDiv = $('<div class="pwc-data-name-introduced">');
      introDiv.append("&starf; introduced in this paper");
      nameDiv.append(introDiv);
    }

    if (num_papers > 0 ) {
      nameDiv.append(metaDiv);
    }
    cardDiv.append(imageDiv);
    cardDiv.append(nameDiv);

    return cardDiv;

  }

  function renderData ($output, data) {
    if (data.error) return;
    $output.html('');

    // don't show anything for non-ml/cs/stats when there are no datasets
    var portal_name = data["portal_name"];
    if ( portal_name !== "ml" && portal_name !== "cs" && portal_name !== "stat" && data.introduced.length === 0 && data.mentioned.length === 0){
      $outputData.attr("style", "display:none");
      return;
    }

    $output.append('<h3>Datasets Used</h3>');

    // If there is nothing just put a simple message
    if (data.introduced.length === 0 && data.mentioned.length === 0) {
      let link = $('<a target="_blank">link datasets here</a>');
      link.attr('href', data.paper_url);
      let p = $('<span>');
      p.append('No dataset metadata found, you can ')
       .append(link)
       .append(".");
      $output.append(p);
      return;
    }

    // Datasets introduced by this paper
    if (data.introduced.length > 0) {
      for (const dataObj of data.introduced) {
        $output.append(makePWCCard(dataObj, true));
      }

    }

    // Datasets used in this paper
    if (data.mentioned.length > 0) {
      for (const dataObj of data.mentioned) {
        $output.append(makePWCCard(dataObj, false));
      }
    }

  }
})();
