(function () {
  const $output = $("#txyz-output");
  if ($output.html() != "") {
    // Toggled off
    $output.html("");
    return;
  } else {
    const currentUrl = window.location.href;
    var updatedUrl = currentUrl.replace("arxiv", "arxiw");
    if (currentUrl.includes("127.0.0.1:8080")) {
      updatedUrl = currentUrl.replace("127.0.0.1:8080", "arxiw.org");
    } 
    const html = `Chat with this paper at <a href="${updatedUrl}" target="_blank">txyz.ai</a>`;
    $output.html(html);
  }
})();