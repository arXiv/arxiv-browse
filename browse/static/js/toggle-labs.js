// toggle logic for arXivLabs integrations
$(document).ready(function() {

  jQuery.cachedScript = function(url, options) {
    // Allow user to set any option except for dataType, cache, and url
    options = $.extend(options || {}, {
      dataType: "script",
      cache: true,
      url: url
    });
    return jQuery.ajax(options);
  };

  var scripts = {
    "paperwithcode": $('#paperwithcode-toggle').data('script-url'),
    "bibex": {
      "url": "https://static.arxiv.org/js/bibex-dev-tabs/bibex.js?20200709",
      "container": "#bib-main"
    },
    "core-recommender": {
      "url": "https://static.arxiv.org/js/core/core-recommender.js?20200716.1",
      "container": "#coreRecommenderOutput"
    }
  };

  var labsCookie = Cookies.getJSON("arxiv_labs");
  if (labsCookie) {
    has_enabled = false;
    for (var key in labsCookie) {
      if (labsCookie[key] && labsCookie[key] == "enabled") {
        has_enabled = true;
        $("#" + key + ".lab-toggle").toggleClass("enabled", true);
        if (key == "bibex-toggle") {
          $.cachedScript(scripts["bibex"]["url"]).done(function(script, textStatus) {
            console.log(textStatus);
          });
        }
        else if (key == "core-recommender-toggle") {
          $.cachedScript(scripts["core-recommender"]["url"]).done(function(script, textStatus) {
            console.log(textStatus);
          });
        } else if (key === "paperwithcode-toggle") {
          $.cachedScript(scripts["paperwithcode"]).done(function(script, textStatus) {
            console.log(textStatus);
          });
        }
      }
    }
    if (has_enabled) {
      $('.labs-display').show();
    }
  } else {
    Cookies.set("arxiv_labs", { sameSite: "strict" });
  }

  $(".lab-toggle").on("click", function() {
    var labsCookie = Cookies.getJSON("arxiv_labs") || {};
    var bibexCookie = Cookies.getJSON("arxiv_bibex") || {};

    var cookie_val = "disabled";
    var bibex_key = "active";
    var bibex_val = false;
    $(this).toggleClass("enabled");
    if ($(this).hasClass("enabled")) {
      cookie_val = "enabled";
      bibex_val = true;
    }
    labsCookie[$(this).attr("id")] = cookie_val;
    Cookies.set("arxiv_labs", labsCookie, { sameSite: "strict" });

    if ($(this).attr("id") == "bibex-toggle") {
      bibexCookie[bibex_key] = bibex_val;
      Cookies.set("arxiv_bibex", bibexCookie);
      if (bibex_val) {
        $.cachedScript(scripts["bibex"]["url"]).done(function(script, textStatus) {
          console.log(textStatus);
        });
      }
    } else if ($(this).attr("id") == "core-recommender-toggle" && $(this).hasClass("enabled") ) {
        $.cachedScript(scripts["core-recommender"]["url"]).done(function(script, textStatus) {});
    } else if ($(this).attr("id") == "paperwithcode-toggle") {
      $.cachedScript(scripts["paperwithcode"]).done(function(script, textStatus) {
        console.log(textStatus);
      });
    }

    // TODO: clean this up
    if (cookie_val == 'disabled') {
      if ($(this).attr("id") == "core-recommender-toggle") {
        $('#coreRecommenderOutput').empty();
      }
      else if ($(this).attr("id") == "bibex-toggle") {
        $('#bib-main').remove();
        location.reload();
      }
    }
  });
});
