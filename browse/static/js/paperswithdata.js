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
    pwc: '<svg xmlns="http://www.w3.org/2000/svg" class="pwc-icon pwc-icon-primary" viewBox="0 0 512 512" ><path stroke="#21cbce" fill="#21cbce" d="M88 128h48v256H88zM232 128h48v256h-48zM160 144h48v224h-48zM304 144h48v224h-48zM376 128h48v256h-48z"></path><path stroke="#21cbce" fill="#21cbce" d="M104 104V56H16v400h88v-48H64V104zM408 56v48h40v304h-40v48h88V56z"></path></svg>'
  }

  function modalityPrettyPrint(mod){
    if (mod === "Images") {
      return "Image";
    } else if (mod === "Videos") {
      return "Video";
    } else {
      return mode;
    }
  }

  function numberWithCommas(x) {
    return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  }

  function makePWCCard (dataObj) {
    let cardDiv = $('<div class="pwc-data-card">');

    // line with the name
    let nameA = $('<a class="pwc-data-name" target="_blank">');
    let datasetImage = $('<img>');
    datasetImage.attr("src", dataObj.image);
    nameA.attr("href", dataObj.url);
    nameA.append(dataObj.name);

    // assemble the first line
    cardDiv.append(datasetImage)
           .append(" ")
           .append(nameA)
           .append($('<br>'));

    let metaSpan = $('<div>');

    if (dataObj.modalities.length > 0) {
      let mainMod = dataObj.modalities[0];
      metaSpan.append(document.createTextNode(modalityPrettyPrint(mainMod).concat(' dataset')));
      metaSpan.append(' &middot; ');
    }
    metaSpan.append(document.createTextNode("used by ".concat(numberWithCommas(dataObj.num_papers)).concat(" papers")));

    cardDiv.append(metaSpan);

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

    // Common "Provided by..." component
    let pProvided = $('<p class="pwc-provided">');
    let aProvided = $('<a target="_blank">paperswithcode.com</a>');
    aProvided.attr('href', data.paper_url);

    pProvided.append('Data provided by ')
             .append(icons['pwc'])
             .append(aProvided);

    // Datasets introduced by this paper
    if (data.introduced.length > 0) {
      $output.append('<h3>Datasets Introduced</h3>');
      //$output.append(pProvided);

      for (const dataObj of data.introduced) {
        $output.append(makePWCCard(dataObj));
      }

    }

    // Datasets used in this paper
    if (data.mentioned.length > 0) {
      $output.append('<h3>Datasets Used</h3>');
      //$output.append(pProvided);

      for (const dataObj of data.mentioned) {
        $output.append(makePWCCard(dataObj));
      }
    }
  }
})();
