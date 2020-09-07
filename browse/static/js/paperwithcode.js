(function () {
  console.log('paperwithcode.js');

  var styleUrl = $('#paperwithcode-toggle').data('style-url');
  var linkElement = document.createElement('link');
  linkElement.setAttribute('rel', 'stylesheet');
  linkElement.setAttribute('type', 'text/css');
  linkElement.setAttribute('href', styleUrl);
  document.head.appendChild(linkElement);

  var arxivId = window.location.pathname.split('/').reverse()[0];
  var pwcApiUrl = 'https://arxiv.paperswithcode.com/api/v0/papers/' + arxivId;
  var $output = $('#pwc-output');
  $.get(pwcApiUrl).done(function (response) {
    render(response);
  });

  var icons = {
    github: '<svg xmlns="http://www.w3.org/2000/svg" class="pwc-icon" viewBox="0 0 512 512"><path d="M256 32C132.3 32 32 134.9 32 261.7c0 101.5 64.2 187.5 153.2 217.9a17.56 17.56 0 003.8.4c8.3 0 11.5-6.1 11.5-11.4 0-5.5-.2-19.9-.3-39.1a102.4 102.4 0 01-22.6 2.7c-43.1 0-52.9-33.5-52.9-33.5-10.2-26.5-24.9-33.6-24.9-33.6-19.5-13.7-.1-14.1 1.4-14.1h.1c22.5 2 34.3 23.8 34.3 23.8 11.2 19.6 26.2 25.1 39.6 25.1a63 63 0 0025.6-6c2-14.8 7.8-24.9 14.2-30.7-49.7-5.8-102-25.5-102-113.5 0-25.1 8.7-45.6 23-61.6-2.3-5.8-10-29.2 2.2-60.8a18.64 18.64 0 015-.5c8.1 0 26.4 3.1 56.6 24.1a208.21 208.21 0 01112.2 0c30.2-21 48.5-24.1 56.6-24.1a18.64 18.64 0 015 .5c12.2 31.6 4.5 55 2.2 60.8 14.3 16.1 23 36.6 23 61.6 0 88.2-52.4 107.6-102.3 113.3 8 7.1 15.2 21.1 15.2 42.5 0 30.7-.3 55.5-.3 63 0 5.4 3.1 11.5 11.4 11.5a19.35 19.35 0 004-.4C415.9 449.2 480 363.1 480 261.7 480 134.9 379.7 32 256 32z"></path></svg>',
    pwc: "<svg xmlns='http://www.w3.org/2000/svg' class='pwc-icon pwc-icon-primary' width='512' height='512' viewBox='0 0 512 512'><title>ionicons-v5-d</title><path d='M384,400.33l35.13-.33A29,29,0,0,0,448,371.13V140.87A29,29,0,0,0,419.13,112l-35.13.33' style='fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px'/><path d='M128,112l-36.8.33c-15.88,0-27.2,13-27.2,28.87V371.47c0,15.87,11.32,28.86,27.2,28.86L128,400' style='fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px'/><line x1='384' y1='192' x2='384' y2='320' style='fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px'/><line x1='320' y1='160' x2='320' y2='352' style='fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px'/><line x1='256' y1='176' x2='256' y2='336' style='fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px'/><line x1='192' y1='160' x2='192' y2='352' style='fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px'/><line x1='128' y1='192' x2='128' y2='320' style='fill:none;stroke-linecap:round;stroke-linejoin:round;stroke-width:32px'/></svg>"
  }

  function render (data) {
    $output.html('');
    if (data.error) return;

    var output = '<h3>Official Code</h3>';

    if (data.official) {
      output += icons.github;
      output += `<a target="_blank" href="${data.official}">${data.official}</a>`;
    } else {
      output += `No official code found; <a target="_blank" href="${data.paper_url}">you can submit it here</a>`;
    }

    output += '<h3>Community Code</h3>';

    if (data.unofficial_count === 0) {
      output += `Submit your reimplementations of this paper on <a target="_blank" href="${data.paper_url}">${icons.pwc} Paper With Code</a>`;
    } else {
      for (var i = 0 ; i < data.top.length ; i++) {
        output += `<img src="${data.top[i].owner.avatar}" class="pwc-avatar" />`;
      }

      output += `<a class="pwc-code-link" target="_blank" href="${data.paper_url}#code">`;
      output += data.top.slice(0, 2).map(item => item.owner.name).join(', ');

      if (data.unofficial_count > 2) {
        output += `and ${data.unofficial_count - 2} others reimplemented this paper`
      }

      output += '</a>';
    }

    $output.html(output);
  }
})();
