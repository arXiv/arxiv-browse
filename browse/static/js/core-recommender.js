(function (window, userInput, options) {
  if (userInput == null) userInput = {};
  if (options == null) options = {};

  // Options processing

  var document = window.document;
  var baseUrl = 'https://core.ac.uk';
  var scriptId = options.scriptId || "recommender-embed";
  var apiKey = options.apiKey || "24c597";


  // Generic DOM manipulations

  function appendStylesheet(url, id) {
    var linkElement = document.createElement('link');
    linkElement.setAttribute('rel', 'stylesheet');
    linkElement.setAttribute('type', 'text/css');
    linkElement.setAttribute('href', url);
    if (id != null) linkElement.id = id;

    document.head.appendChild(linkElement);
    return linkElement;
  }

  function appendScript(url, id) {
    var scriptElement = document.createElement('script');
    scriptElement.type = "text/javascript";
    scriptElement.src = url;
    if (id != null) scriptElement.id = id;

    document.body.appendChild(scriptElement);
    return scriptElement;
  }


  // CORE Recommender

  function loadRecommender(baseUrl, userInput, options) {
    if (options == null) options = {};
    if (userInput == null) userInput = {};

    appendStylesheet(baseUrl + '/recommender/embed-arxiv-style.css', scriptId);
    appendScript(baseUrl + '/recommender/embed.js');

    localStorage.setItem('idRecommender', apiKey);
    localStorage.setItem('userInput', JSON.stringify(userInput));
    if (options.overrideLocale)
      localStorage.setItem('overridelocale', "en_GB");
  }

  function unloadRecommender() {
    document.getElementById(scriptId).remove();
    document.getElementById("coreRecommenderOutput").innerHTML = "";
  }

  function toggleRecommender(isEnabled) {
    if (isEnabled)
      loadRecommender(baseUrl);
    else
      unloadRecommender();
  }

  function initRecommender() {
    toggleRecommender(true);
  }


  // Initialization

  if (window.document.readyState == 'loading')
    window.addEventListener('load', initRecommender);
  else
    initRecommender();
}(window));
