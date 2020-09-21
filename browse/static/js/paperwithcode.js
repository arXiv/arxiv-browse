(function () {
  var styleUrl = $('#paperwithcode-toggle').data('style-url');
  var linkElement = document.createElement('link');
  linkElement.setAttribute('rel', 'stylesheet');
  linkElement.setAttribute('type', 'text/css');
  linkElement.setAttribute('href', styleUrl);
  document.head.appendChild(linkElement);

  var arxivId = window.location.pathname.split('/').reverse()[0];
  arxivId = '1909.11065';
  var pwcApiUrl = 'https://arxiv.paperswithcode.com/api/v0/papers/' + arxivId;
  var $output = $('#pwc-output');
  $.get(pwcApiUrl).done(function (response) {
    render(response);
  }).fail(function (response) {
    render(null);
  });

  var icons = {
    github: '<svg xmlns="http://www.w3.org/2000/svg" class="pwc-icon" viewBox="0 0 512 512"><path d="M256 32C132.3 32 32 134.9 32 261.7c0 101.5 64.2 187.5 153.2 217.9a17.56 17.56 0 003.8.4c8.3 0 11.5-6.1 11.5-11.4 0-5.5-.2-19.9-.3-39.1a102.4 102.4 0 01-22.6 2.7c-43.1 0-52.9-33.5-52.9-33.5-10.2-26.5-24.9-33.6-24.9-33.6-19.5-13.7-.1-14.1 1.4-14.1h.1c22.5 2 34.3 23.8 34.3 23.8 11.2 19.6 26.2 25.1 39.6 25.1a63 63 0 0025.6-6c2-14.8 7.8-24.9 14.2-30.7-49.7-5.8-102-25.5-102-113.5 0-25.1 8.7-45.6 23-61.6-2.3-5.8-10-29.2 2.2-60.8a18.64 18.64 0 015-.5c8.1 0 26.4 3.1 56.6 24.1a208.21 208.21 0 01112.2 0c30.2-21 48.5-24.1 56.6-24.1a18.64 18.64 0 015 .5c12.2 31.6 4.5 55 2.2 60.8 14.3 16.1 23 36.6 23 61.6 0 88.2-52.4 107.6-102.3 113.3 8 7.1 15.2 21.1 15.2 42.5 0 30.7-.3 55.5-.3 63 0 5.4 3.1 11.5 11.4 11.5a19.35 19.35 0 004-.4C415.9 449.2 480 363.1 480 261.7 480 134.9 379.7 32 256 32z"></path></svg>',
    pwc: '<svg xmlns="http://www.w3.org/2000/svg" class="pwc-icon pwc-icon-primary" viewBox="0 0 512 512" ><path stroke="#21cbce" fill="#21cbce" d="M88 128h48v256H88zM232 128h48v256h-48zM160 144h48v224h-48zM304 144h48v224h-48zM376 128h48v256h-48z"></path><path stroke="#21cbce" fill="#21cbce" d="M104 104V56H16v400h88v-48H64V104zM408 56v48h40v304h-40v48h88V56z"></path></svg>'
  }

  function render (data) {
    $output.html('');
    if (data === null) {
      $output.html('<p>This paper has not been found in the Papers with Code database. If you are one of the registered authors of this paper, you can link your code on your <a href="https://arxiv.org/user">arxiv user page</a></p>');
      return
    }
    if (data.error) return;

    $output.append('<h3>Official Code</h3>');

    if (data.official) {
      let link = $('<a target="_blank"></a>');
      link.attr('href', data.official.url);
      link
        .append(icons.github)
        .append(document.createTextNode(data.official.url));
      $output.append(link);
    } else {
      let link = $('<a target="_blank">you can submit it here</a>');
      link.attr('href', data.paper_url);
      $output
        .append('No official code found; ')
        .append(link);
    }

    $output.append('<h3>Community Code</h3>');

    if (data.unofficial_count === 0) {
      let link = $('<a target="_blank">${icons.pwc}Papers With Code</a>');
      link.attr('href', data.paper_url);
      $output
        .append('Submit your implementations of this paper on ')
        .append(link);
    } else {
      let link = $('<a class="pwc-code-link" target="_blank"></a>');
      link.attr('href', data.paper_url + '#code');
      link
        .append(icons.pwc)
        .append(' ')
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
})();
