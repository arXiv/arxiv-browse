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
    catalyzex: '<svg xmlns="http://www.w3.org/2000/svg" class="cx-icon" viewBox="0 0 466 466"><path stroke="none" fill="#000000" transform="translate(0.000000,466.000000) scale(0.100000,-0.100000)" d="M 3690 3700.9961 L 3690 3554.9951 L 3690 3410.0049 L 3844.9951 3410.0049 L4000.0049 3410.0049 L 4000.0049 2384.9951 L 4000.0049 1360 L 3972.9932 1360 C 3956.9932 1359 3889.0048 1357.9971 3820.0049 \
      1356.9971 L 3694.9951 1355.0049 L 3692.0068 1206.9971 L 3689.0039 1059.0039 L 3947.0068 1062.0068 C 4243.0065 1065.0068 4255.9981 1069.0001 4297.998 1150 L 4320 1195 L 4317.9932 2397.0068 C 4314.9932 3593.0056 4314.999 3598.9961 4293.999 3625.9961 C 4282.999 3640.9961 4260.9961 3662.999 4245.9961 3673.999 C 4219.9961 3693.999 4202.9939 3694.9932 3953.9941 3697.9932 L 3690 3700.9961 z M 2077.998 3700 C 1889.9982 3699 1817.0049 3695.9961 1795.0049 3685.9961 C 1779.0049 3678.9961 1757.0019 3662.9971 1747.002 3651.9971 C 1700.002 3599.9971 1700.9951 3625.0036 1699.9951 2390.0049 C 1699.9951 1582.0057 1702.9961 1212.9951 1710.9961 1184.9951 C 1724.9961 1134.9952 1773.9952 1083.0049 1819.9951 1070.0049 C 1838.9951 1065.0049 1961.9982 1060 2092.998 1060 L 2331.0059 1060 L 2328.0029 1207.9932 L 2325 1355.0049 L 2200.0049 1356.9971 C 2131.005 1356.9971 2064.9932 1358.0039 2052.9932 1359.0039 L 2029.9951 1360 L 2029.9951 2384.9951 L 2029.9951 3410.0049 L 2179.9951 3410.0049 L 2329.9951 3410.0049 L 2329.9951 3554.9951 \
      L 2329.9951 3700 L 2077.998 3700 z M 865.00488 3699.0039 C 530.00522 3699.0039 427.99998 3695.9961 405 3685.9961 C 363.00004 3667.9961 321.99316 3617.0019 312.99316 3572.002 C 308.99317 3552.002 304.99512 3089.9995 304.99512 2545 L 304.99512 1555 L 330 1510.9961 C 345.99998 1482.9961 368.99514 1459.001 394.99512 1446.001 C 432.99508 1426.001 452.00331 1425.0068 828.00293 1422.0068 C 1272.0025 1419.0068 1314.9961 1422.9942 1365.9961 1473.9941 C 1383.9961 1491.9941 1403.0039 1523.9951 1409.0039 1544.9951 C 1416.0039 1569.9951 1420.0049 1699.0031 1420.0049 1888.0029 L 1420.0049 2189.9951 L 1255.0049 2189.9951 L 1090.0049 2189.9951 L 1090.0049 1949.9951 L 1090.0049 1709.9951 L 865.00488 1709.9951 L 640.00488 1709.9951 L 640.00488 2564.9951 L 640.00488 3419.9951 L 865.00488 3419.9951 L 1090.0049 3419.9951 L 1090.0049 3194.9951 L 1090.0049 2969.9951 L 1256.001 2969.9951 L 1421.001 2969.9951 L 1417.998 3277.9932 C 1414.998 3566.9929 1414.0039 3587.0049 1394.0039 3620.0049 C 1383.0039 3639.0049 1356.0039 3665.002 1334.0039 3677.002 C 1295.0039 3700.0019 \
      1292.0045 3700.0039 865.00488 3699.0039 z M 2682.9932 2890 C 2592.9933 2890 2520 2886.998 2520 2882.998 C 2520 2877.9981 2590.0059 2718.9969 2676.0059 2526.9971 L 2832.9932 2180.0049 L 2655.9961 1806.001 C 2558.9962 1601.0012 2479.9951 1430.0059 2479.9951 1426.0059 C 2479.9951 1423.0059 2557.0011 1421.0068 2651.001 1422.0068 L 2823.0029 1424.9951 L 2913.0029 1652.998 C 2962.0029 1777.9979 3006.0049 1880.0049 3010.0049 1880.0049 C 3014.0049 1880.0049 3057 1776.995 3105 1649.9951 L 3191.9971 1420 L 3366.0059 1420 C 3462.0058 1420 3540 1422.0029 3540 1423.0029 C 3540 1425.0029 3460.995 1594.9953 3364.9951 1799.9951 C 3268.9952 2005.9949 3190.0049 2177.9971 3190.0049 2181.9971 C 3190.0049 2189.9971 3492.9971 2859.9981 3506.9971 2882.998 C 3508.9971 2886.998 3436.996 2890 3345.9961 2890 L 3182.0068 2890 L 3098.9941 2680 C 3053.9942 2565.0001 3014.0049 2470 3010.0049 2470 C 3006.0049 2470 2967.0039 2565.0001 2924.0039 2680 L 2845.0049 2890 L 2682.9932 2890 z"/></svg>',
    github: '<svg xmlns="http://www.w3.org/2000/svg" class="pwc-icon" viewBox="0 0 512 512"><path d="M256 32C132.3 32 32 134.9 32 261.7c0 101.5 64.2 187.5 153.2 217.9a17.56 17.56 0 003.8.4c8.3 0 11.5-6.1 11.5-11.4 0-5.5-.2-19.9-.3-39.1a102.4 102.4 0 01-22.6 2.7c-43.1 0-52.9-33.5-52.9-33.5-10.2-26.5-24.9-33.6-24.9-33.6-19.5-13.7-.1-14.1 1.4-14.1h.1c22.5 2 34.3 23.8 34.3 23.8 11.2 19.6 26.2 25.1 39.6 25.1a63 63 0 0025.6-6c2-14.8 7.8-24.9 14.2-30.7-49.7-5.8-102-25.5-102-113.5 0-25.1 8.7-45.6 23-61.6-2.3-5.8-10-29.2 2.2-60.8a18.64 18.64 0 015-.5c8.1 0 26.4 3.1 56.6 24.1a208.21 208.21 0 01112.2 0c30.2-21 48.5-24.1 56.6-24.1a18.64 18.64 0 015 .5c12.2 31.6 4.5 55 2.2 60.8 14.3 16.1 23 36.6 23 61.6 0 88.2-52.4 107.6-102.3 113.3 8 7.1 15.2 21.1 15.2 42.5 0 30.7-.3 55.5-.3 63 0 5.4 3.1 11.5 11.4 11.5a19.35 19.35 0 004-.4C415.9 449.2 480 363.1 480 261.7 480 134.9 379.7 32 256 32z"></path></svg>',
    gitlab: '<svg xmlns="http://www.w3.org/2000/svg" class="pwc-icon" viewBox="0 0 512 512"><path d="M494.07 281.6l-25.18-78.08c-.13-.72-.34-1.42-.61-2.1l-50.5-156.94c-2.76-8.31-10.49-13.88-19.17-13.82-8.66-.05-16.34 5.6-18.95 13.94l-48.14 149.55H179.56L131.34 44.59c-2.59-8.31-10.23-13.95-18.86-13.94h-.11c-8.69 0-16.39 5.62-19.12 13.95L42.7 201.73c0 .14-.11.26-.16.4l-25.63 79.48c-3.86 11.96.35 25.07 10.44 32.46l221.44 162.41c4 2.92 9.41 2.89 13.38-.07l221.48-162.34c10.09-7.39 14.3-20.51 10.42-32.47m-330.99-64.51l61.72 191.76L76.63 217.09m209.64 191.8l59.19-183.84 2.55-7.96h86.52L300.47 390.44M398.8 59.31l43.37 134.83h-86.82m-31.19 22.87l-43 133.58-25.66 79.55L186.94 217M112.27 59.31l43.46 134.83H68.97M40.68 295.58a6.186 6.186 0 01-2.21-6.9l19.03-59.03 139.58 180.62m273.26-114.69L313.92 410.22l.52-.69L453.5 229.64l19.03 59c.84 2.54-.05 5.34-2.19 6.92"></path></svg>',
    bitbucket: '<svg xmlns="http://www.w3.org/2000/svg" class="pwc-icon" viewBox="0 0 512 512"><path d="M483.13 32.23a19.81 19.81 0 00-2.54-.23h-449C23 31.88 16.12 38.88 16 47.75a11.52 11.52 0 00.23 2.8l65.3 411.25a22.54 22.54 0 007 12.95 20 20 0 0013.5 5.25h313.15a15.46 15.46 0 0015.34-13.42l38.88-247.91H325.19l-18.46 112H205.21l-25.73-148h295.58l20.76-132c1.27-8.75-4.38-17.04-12.69-18.44z"></path></svg>',
    pwc: '<svg xmlns="http://www.w3.org/2000/svg" class="pwc-icon pwc-icon-primary" viewBox="0 0 512 512" ><path stroke="#21cbce" fill="#21cbce" d="M88 128h48v256H88zM232 128h48v256h-48zM160 144h48v224h-48zM304 144h48v224h-48zM376 128h48v256h-48z"></path><path stroke="#21cbce" fill="#21cbce" d="M104 104V56H16v400h88v-48H64V104zM408 56v48h40v304h-40v48h88V56z"></path></svg>'
  }

  const fetchCatalyzeXCode = async () => {
    const controller = new AbortController();
    var response = null
    try {
      setTimeout(() => controller.abort(), 2000);
      response = await fetch('https://www.catalyzex.com/api/code?' + new URLSearchParams({
        'extension': 'true',
        'paper_arxiv_id': arxivId
      }), {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        signal: controller.signal
      } ).then( response => {
        if (response.ok) {
          return response.json();
        } else {
          return false;
        }
      }).catch( err => {
        console.clear();
      });
    } catch (err) {
      console.log(err)
    }

    return response;
  }

  async function renderCode ($output, data) {
    const catalyzexCode = await fetchCatalyzeXCode();
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

    if (data.unofficial_count === 0 && catalyzexCode === false) {
      $output.append('<h3 class="pwc-community-nocode">Community Code</h3>');
      let link = $(`<a target="_blank">${icons.pwc}Papers With Code</a>`);
      link.attr('href', data.paper_url);
      $output
        .append('Submit your implementations of this paper on ')
        .append(link);
    } else {
      $output.append('<h3 class="pwc-community-code">Community Code</h3>');
      if (data.unofficial_count > 0) {
        let p = $('<p>');
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
        p.append(link)
        $output.append(p);
      }
      if (catalyzexCode && Object.keys(catalyzexCode).length > 0) {
        let p = $('<p>');
        let link = $('<a target="_blank"></a>');
        link.attr('href', `https://www.catalyzex.com/paper/arxiv:${arxivId}/code`);
        link
          .append(icons.catalyzex)
          .append(document.createTextNode(Object.keys(catalyzexCode).length))
          .append(` code implementation${Object.keys(catalyzexCode).length > 1 ? 's': ''} on CatalyzeX`);
        p.append(link)
        $output.append(p);
        $output.append(link);
      }
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
