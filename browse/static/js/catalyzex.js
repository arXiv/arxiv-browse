(async () => {
  const arxivId = document.head.querySelector("[name~=citation_arxiv_id][content]").content;
  const paperTitle = document.querySelector("h1.title")?.innerText;
  const paperUrl = window.location.href.split('?')[0];
  const $output = $("#catalyzex-output");

  const url = new URL(location.href);
  let cxToken = url.searchParams.get('cx_token');

  if(cxToken) {
    localStorage.setItem('@cx/token', cxToken)
    url.searchParams.delete('cx_token')
    window.history.replaceState({}, document.title, url.href);
  } else {
    cxToken = localStorage.getItem('@cx/token')
  }

  if ($output.html() != "") {
    // Toggled off
    $output.html("");
    $output.attr("style", "display:none");
    return;
  } else {
    $output.attr("style", "");
  }

  const icons = {
    github: '<svg xmlns="http://www.w3.org/2000/svg" class="cx-icon" viewBox="0 0 512 512"><path d="M256 32C132.3 32 32 134.9 32 261.7c0 101.5 64.2 187.5 153.2 217.9a17.56 17.56 0 003.8.4c8.3 0 11.5-6.1 11.5-11.4 0-5.5-.2-19.9-.3-39.1a102.4 102.4 0 01-22.6 2.7c-43.1 0-52.9-33.5-52.9-33.5-10.2-26.5-24.9-33.6-24.9-33.6-19.5-13.7-.1-14.1 1.4-14.1h.1c22.5 2 34.3 23.8 34.3 23.8 11.2 19.6 26.2 25.1 39.6 25.1a63 63 0 0025.6-6c2-14.8 7.8-24.9 14.2-30.7-49.7-5.8-102-25.5-102-113.5 0-25.1 8.7-45.6 23-61.6-2.3-5.8-10-29.2 2.2-60.8a18.64 18.64 0 015-.5c8.1 0 26.4 3.1 56.6 24.1a208.21 208.21 0 01112.2 0c30.2-21 48.5-24.1 56.6-24.1a18.64 18.64 0 015 .5c12.2 31.6 4.5 55 2.2 60.8 14.3 16.1 23 36.6 23 61.6 0 88.2-52.4 107.6-102.3 113.3 8 7.1 15.2 21.1 15.2 42.5 0 30.7-.3 55.5-.3 63 0 5.4 3.1 11.5 11.4 11.5a19.35 19.35 0 004-.4C415.9 449.2 480 363.1 480 261.7 480 134.9 379.7 32 256 32z"></path></svg>',
    catalyzex: '<svg xmlns="http://www.w3.org/2000/svg" id="cx-logo" class="cx-icon" viewBox="0 0 466 466"><path stroke="none" fill="#000000" transform="translate(0.000000,466.000000) scale(0.100000,-0.100000)" d="M 3690 3700.9961 L 3690 3554.9951 L 3690 3410.0049 L 3844.9951 3410.0049 L4000.0049 3410.0049 L 4000.0049 2384.9951 L 4000.0049 1360 L 3972.9932 1360 C 3956.9932 1359 3889.0048 1357.9971 3820.0049 \ 1356.9971 L 3694.9951 1355.0049 L 3692.0068 1206.9971 L 3689.0039 1059.0039 L 3947.0068 1062.0068 C 4243.0065 1065.0068 4255.9981 1069.0001 4297.998 1150 L 4320 1195 L 4317.9932 2397.0068 C 4314.9932 3593.0056 4314.999 3598.9961 4293.999 3625.9961 C 4282.999 3640.9961 4260.9961 3662.999 4245.9961 3673.999 C 4219.9961 3693.999 4202.9939 3694.9932 3953.9941 3697.9932 L 3690 3700.9961 z M 2077.998 3700 C 1889.9982 3699 1817.0049 3695.9961 1795.0049 3685.9961 C 1779.0049 3678.9961 1757.0019 3662.9971 1747.002 3651.9971 C 1700.002 3599.9971 1700.9951 3625.0036 1699.9951 2390.0049 C 1699.9951 1582.0057 1702.9961 1212.9951 1710.9961 1184.9951 C 1724.9961 1134.9952 1773.9952 1083.0049 1819.9951 1070.0049 C 1838.9951 1065.0049 1961.9982 1060 2092.998 1060 L 2331.0059 1060 L 2328.0029 1207.9932 L 2325 1355.0049 L 2200.0049 1356.9971 C 2131.005 1356.9971 2064.9932 1358.0039 2052.9932 1359.0039 L 2029.9951 1360 L 2029.9951 2384.9951 L 2029.9951 3410.0049 L 2179.9951 3410.0049 L 2329.9951 3410.0049 L 2329.9951 3554.9951 \ L 2329.9951 3700 L 2077.998 3700 z M 865.00488 3699.0039 C 530.00522 3699.0039 427.99998 3695.9961 405 3685.9961 C 363.00004 3667.9961 321.99316 3617.0019 312.99316 3572.002 C 308.99317 3552.002 304.99512 3089.9995 304.99512 2545 L 304.99512 1555 L 330 1510.9961 C 345.99998 1482.9961 368.99514 1459.001 394.99512 1446.001 C 432.99508 1426.001 452.00331 1425.0068 828.00293 1422.0068 C 1272.0025 1419.0068 1314.9961 1422.9942 1365.9961 1473.9941 C 1383.9961 1491.9941 1403.0039 1523.9951 1409.0039 1544.9951 C 1416.0039 1569.9951 1420.0049 1699.0031 1420.0049 1888.0029 L 1420.0049 2189.9951 L 1255.0049 2189.9951 L 1090.0049 2189.9951 L 1090.0049 1949.9951 L 1090.0049 1709.9951 L 865.00488 1709.9951 L 640.00488 1709.9951 L 640.00488 2564.9951 L 640.00488 3419.9951 L 865.00488 3419.9951 L 1090.0049 3419.9951 L 1090.0049 3194.9951 L 1090.0049 2969.9951 L 1256.001 2969.9951 L 1421.001 2969.9951 L 1417.998 3277.9932 C 1414.998 3566.9929 1414.0039 3587.0049 1394.0039 3620.0049 C 1383.0039 3639.0049 1356.0039 3665.002 1334.0039 3677.002 C 1295.0039 3700.0019 \ 1292.0045 3700.0039 865.00488 3699.0039 z M 2682.9932 2890 C 2592.9933 2890 2520 2886.998 2520 2882.998 C 2520 2877.9981 2590.0059 2718.9969 2676.0059 2526.9971 L 2832.9932 2180.0049 L 2655.9961 1806.001 C 2558.9962 1601.0012 2479.9951 1430.0059 2479.9951 1426.0059 C 2479.9951 1423.0059 2557.0011 1421.0068 2651.001 1422.0068 L 2823.0029 1424.9951 L 2913.0029 1652.998 C 2962.0029 1777.9979 3006.0049 1880.0049 3010.0049 1880.0049 C 3014.0049 1880.0049 3057 1776.995 3105 1649.9951 L 3191.9971 1420 L 3366.0059 1420 C 3462.0058 1420 3540 1422.0029 3540 1423.0029 C 3540 1425.0029 3460.995 1594.9953 3364.9951 1799.9951 C 3268.9952 2005.9949 3190.0049 2177.9971 3190.0049 2181.9971 C 3190.0049 2189.9971 3492.9971 2859.9981 3506.9971 2882.998 C 3508.9971 2886.998 3436.996 2890 3345.9961 2890 L 3182.0068 2890 L 3098.9941 2680 C 3053.9942 2565.0001 3014.0049 2470 3010.0049 2470 C 3006.0049 2470 2967.0039 2565.0001 2924.0039 2680 L 2845.0049 2890 L 2682.9932 2890 z"/></svg>'
  }

  const fetchCatalyzeXCode = async () => {
    const cxApiUrl =  new URL("https://www.catalyzex.com/api/code")
    const queryParams = {
      src: 'arxiv',
      paper_arxiv_id: arxivId,
      paper_url: paperUrl,
      paper_title: paperTitle
    }

    Object.entries(queryParams).forEach(([key, val]) => {
      cxApiUrl.searchParams.set(key, val);
    })

    try {
      result = await $.ajax({ 
        url: cxApiUrl, 
        timeout: 2000, 
        dataType: "json",
        headers: cxToken ? { 'Authorization': `Bearer ${cxToken}`} : undefined
      });
    } catch (error) {
      result = error?.responseJSON || {};
    }

    return result;
  };

  $output.html('');

  const { count: implementations, cx_url: cxImplementationsUrl, is_alert_active: isAlertActive, authed_user_id: authedUserId } = await fetchCatalyzeXCode()
  $output.append("<h2>CatalyzeX</h2>");

  const addCodeURL = new URL("https://www.catalyzex.com/add_code");
  addCodeURL.searchParams.set('title', paperTitle);
  addCodeURL.searchParams.set('paper_url', paperUrl);

  const submitItHereLink = `<a target="_blank" href="${addCodeURL}" style="font-weight:bold">submit it here</a>`;

  if (implementations) {
    const codeLink = $(`<a target="_blank"></a>`);
    codeLink.attr("href", cxImplementationsUrl);
    codeLink
      .append(icons.github)
      .append(`${implementations} code implementation${implementations > 1 ? "s" : ""} found on`)
      .append(icons.catalyzex)
      .append("CatalyzeX");

    $output.append(window.DOMPurify.sanitize(codeLink))
  } else {
    $output.append(`<p>No code found for this paper just yet.</p>`)
  }
  $output.append(window.DOMPurify.sanitize(`<p>If you have code to share with the arXiv community, please ${submitItHereLink} to benefit all researchers & engineers.</p>`))
  if(isAlertActive) {
    $output.append(window.DOMPurify.sanitize(`
      <p>You've set up an alert for this paper, and we'll notify you once new code becomes available. Manage all your alerts <a target="_blank" href="https://www.catalyzex.com/users/${authedUserId}/alerts">here</a>. 🚀
   `))
  } else {
    const createAlertUrl = new URL("https://www.catalyzex.com/alerts/code/create");
    const queryParams = {
      paper_arxiv_id: arxivId,
      paper_url: paperUrl,
      paper_title: paperTitle,
      redirect_url: paperUrl
    }
    Object.entries(queryParams).forEach(([key, val]) => {
      createAlertUrl.searchParams.set(key, val);
    })
    $output.append(window.DOMPurify.sanitize(`<p><a href="${createAlertUrl}">Create an alert</a> to get notified when new code is available for this paper.</p>`))
  }
})();