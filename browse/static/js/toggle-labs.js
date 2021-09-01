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
    "paperwithcode": $('#paperwithcode-toggle').data('script-url') + "?20210727",
    "litmaps": $('#litmaps-toggle').data('script-url'),
    "scite": $('#scite-toggle').data('script-url'),
    "connectedpapers": $('#connectedpapers-toggle').data('script-url'),
    "influenceflower": $('#influenceflower-toggle').data('script-url'),
    "bibex": {
      "url": "https://static.arxiv.org/js/bibex/bibex.js?20210223",
      "container": "#bib-main"
    },
    "core-recommender": {
      "url": "https://static.arxiv.org/js/core/core-recommender.js?20200716.1",
      "container": "#coreRecommenderOutput"
    }
  };

  var pwcEnabled = true;

  var labsCookie = Cookies.getJSON("arxiv_labs");
  if (labsCookie) {
    has_enabled = false;
    if ( labsCookie["last_tab"] ){
      $("input#"+labsCookie["last_tab"]).click();
    }
    for (var key in labsCookie) {
      if (labsCookie[key] && labsCookie[key] == "enabled") {
        has_enabled = true;
        $("#" + key + ".lab-toggle").toggleClass("enabled", true);
        if (key == "bibex-toggle") {
          $.cachedScript(scripts["bibex"]["url"]).done(function(script, textStatus) {
            console.log(textStatus);
          });
        } else if (key == "litmaps-toggle") {
          $.cachedScript(scripts["litmaps"]).done(function(script, textStatus) {
            console.log(textStatus);
          });
        } else if (key == "scite-toggle") {
          $.cachedScript(scripts["scite"]).done(function(script, textStatus) {
            console.log(textStatus);
          });
        } else if (key == "core-recommender-toggle") {
          $.cachedScript(scripts["core-recommender"]["url"]).done(function(script, textStatus) {
            console.log(textStatus);
          });
        } else if (key === "paperwithcode-toggle") {
          $.cachedScript(scripts["paperwithcode"]).done(function(script, textStatus) {
            console.log(textStatus);
          });
        } else if (key === "connectedpapers-toggle") {
          $.cachedScript(scripts["connectedpapers"]).done(function(script, textStatus) {
            console.log(textStatus);
          });
        } else if (key === "influenceflower-toggle") {
          $.cachedScript(scripts["influenceflower"]).done(function(script, textStatus) {
            console.log(textStatus);
          });
        }
      } else if (labsCookie[key] && labsCookie[key] == "disabled"){
        if (key === "paperwithcode-toggle") {
          pwcEnabled = false;
        }
      }
    }
  } else {
    Cookies.set("arxiv_labs", { sameSite: "strict" });
  }

  if(pwcEnabled){
    $("#paperwithcode-toggle.lab-toggle").toggleClass("enabled",true);
    $.cachedScript(scripts["paperwithcode"]).done(function(script, textStatus) {
      console.log(textStatus);
    });
  }
  // record last-clicked tab
  $("div.labstabs input[name='tabs']").on("click", function() {
    var labsCookie = Cookies.getJSON("arxiv_labs") || {};
    labsCookie["last_tab"] = $(this).attr("id");
    Cookies.set("arxiv_labs", labsCookie, { sameSite: "strict" });
  });

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
    } else if ($(this).attr("id") == "litmaps-toggle") {
      $.cachedScript(scripts["litmaps"]).done(function(script, textStatus) {
        console.log(textStatus);
      });
    } else if ($(this).attr("id") == "scite-toggle") {
      $.cachedScript(scripts["scite"]).done(function(script, textStatus) {
        console.log(textStatus);
      });
    } else if ($(this).attr("id") == "core-recommender-toggle" && $(this).hasClass("enabled")) {
        $.cachedScript(scripts["core-recommender"]["url"]).done(function(script, textStatus) {});
    } else if ($(this).attr("id") == "paperwithcode-toggle") {
      $.cachedScript(scripts["paperwithcode"]).done(function(script, textStatus) {
        console.log(textStatus);
      });
    } else if ($(this).attr("id") == "connectedpapers-toggle") {
      $.cachedScript(scripts["connectedpapers"]).done(function(script, textStatus) {
        console.log(textStatus);
      });
    } else if ($(this).attr("id") == "influenceflower-toggle") {
      $.cachedScript(scripts["influenceflower"]).done(function(script, textStatus) {
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
