(function () {
  var arxivId = window.location.pathname.split('/').reverse()[0];
  var pwcApiUrl = 'https://arxiv-beta.paperswithcode.com/api/v0/datasets/' + arxivId;
  var $output = $('#pwc-data-output');
  $.get(pwcApiUrl).done(function (response) {
    render(response);
  }).fail(function (response) {
    render(null);
  });

  var icons = {
    pwc: '<svg xmlns="http://www.w3.org/2000/svg" class="pwc-icon pwc-icon-primary" viewBox="0 0 512 512" ><path stroke="#21cbce" fill="#21cbce" d="M88 128h48v256H88zM232 128h48v256h-48zM160 144h48v224h-48zM304 144h48v224h-48zM376 128h48v256h-48z"></path><path stroke="#21cbce" fill="#21cbce" d="M104 104V56H16v400h88v-48H64V104zM408 56v48h40v304h-40v48h88V56z"></path></svg>',
    datadefault: '<svg xmlns="http://www.w3.org/2000/svg" class="" viewBox="0 0 512 512" ><path stroke="#cccccc" fill="#cccccc" d="M88 128h48v256H88zM232 128h48v256h-48zM160 144h48v224h-48zM304 144h48v224h-48zM376 128h48v256h-48z"></path><path stroke="#cccccc" fill="#cccccc" d="M104 104V56H16v400h88v-48H64V104zM408 56v48h40v304h-40v48h88V56z"></path></svg>'
  }

  function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
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
      imageDiv.append(icons['datadefault']);
    }

    // name
    let nameDiv = $('<div class="pwc-data-card-name">');
    let nameA = $('<a class="pwc-data-name" target="_blank">');
    nameA.attr("href", dataObj.url);
    nameA.append(dataObj.name);

    // meta line
    let metaDiv = $('<div class="pwc-data-name-meta">');
    if (dataObj.num_papers === 1) {
      metaDiv.append(document.createTextNode(numberWithCommas(dataObj.num_papers).concat(" paper also use this dataset")));
    } else {
      metaDiv.append(document.createTextNode(numberWithCommas(dataObj.num_papers).concat(" papers also use this dataset")));
    }

    // assemble name div
    nameDiv.append(nameA);

    // additional is introduced line
    if (isIntroduced) {
      let introDiv = $('<div class="pwc-data-name-introduced">');
      introDiv.append("&starf; introduced in this paper");
      nameDiv.append(introDiv);
    }

    nameDiv.append(metaDiv);
    cardDiv.append(imageDiv);
    cardDiv.append(nameDiv);

    return cardDiv;

  }

  function render (data) {
    $output.html('');
    if (data === null) {
      $output.html('<p>This paper has not been found in the Papers with Code database. If you are one of the authors of this paper, you can link data on your <a href="https://arxiv.org/user">arxiv user page</a></p>');
      return;
    }
    if (data.error) return;

    // If there is nothing just put a simple message
    if (data.introduced.length === 0 && data.mentioned.length === 0) {
      let link = $('<a target="_blank">submit datasets used and introduced here</a>');
      link.attr('href', data.paper_url);
      let p = $('<p>');
      p.append('No dataset metadata found, you can ')
       .append(link)
       .append(".");
      $output.append(p);
      return;
    }

    $output.append('<h3>Datasets</h3>');

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

    // Attribution
    let pProvided = $('<p class="pwc-provided">');
    let aProvided = $('<a target="_blank">paperswithcode.com</a>');
    aProvided.attr('href', data.paper_url);

    pProvided.append('&nbsp;via ')
             .append(icons['pwc'])
             .append(aProvided);

    $output.append(pProvided);
  }
})();
