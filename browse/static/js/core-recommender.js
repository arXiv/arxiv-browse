(function (window, userInput, options) {
  if (userInput == null) userInput = {};
  if (options == null) options = {};

  // Options processing

  var document = window.document;
  var baseUrl = 'https://core.ac.uk';
  var cookieName = options.cookieName || "arxiv_core_recommender";
  var scriptId = options.scriptId || "recommender-embed";
  var apiKey = options.apiKey || "24c597";


  // Generic cookie manipulations

  function setCookie(name, value, days) {
    if (!name && !value) return false;
  
    if (days) {
      var date = new Date();
      date.setTime(date.getTime()+(days * 24 * 60 * 60 * 1000));
      var expires = "; expires=" + date.toGMTString();
    } else {
      var expires = "";
    }

    document.cookie = name + "=" + value + expires +"; path=/";
    return true;
  }

  function getCookie(name) {
    var nameEq = name + "=";
    var begin = document.cookie.indexOf(nameEq);
    if (begin < 0) return null;

    var end = document.cookie.indexOf(";", begin);
    if (end < 0) end = document.cookie.length;

    var value = decodeURIComponent(document.cookie.substring(begin + nameEq.length, end));
    return value;
  }


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

  function getRecommenderStatus() {
    const cookieValue = getCookie(cookieName) || "enabled";
    return cookieValue === "enabled";
  }

  function setRecommenderStatus(enabled) {
    const value = enabled ? "enabled" : "disabled";
    setCookie(cookieName, value, 365);
  }

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

  function renderToggleButtonText(status) {
    var buttonElement = document.getElementById("core-recommender-toggle");
    const caption = (status ? "Disable" : "Enable") + " CORE Recommendations";
    buttonElement.innerHTML = caption;
  }

  function toggleRecommender(forceStatus) {
    var nextStatus = forceStatus != null ? forceStatus : !getRecommenderStatus();
    
    setRecommenderStatus(nextStatus);

    renderToggleButtonText(nextStatus);
    if (nextStatus)
      loadRecommender(baseUrl);
    else
      unloadRecommender();
  }

  function initRecommender() {
    var isEnabled = getRecommenderStatus();
    toggleRecommender(isEnabled);
  }

  window.toggleCORERecommender = toggleRecommender;
  window.addEventListener('load', initRecommender);
}(window));
