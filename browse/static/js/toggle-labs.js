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
    "replicate": $('#replicate-toggle').data('script-url'),
    "spaces": $('#spaces-toggle').data('script-url'),
    "litmaps": $('#litmaps-toggle').data('script-url'),
    "scite": $('#scite-toggle').data('script-url'),
    "iarxiv": $('#iarxiv-toggle').data('script-url'),
    "connectedpapers": $('#connectedpapers-toggle').data('script-url'),
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

  const currentCategory = $('.current')?.text()?.toLowerCase();
  const demoCategories = [
    "cs",   // Computer Science
    "eess", // Electrical Engineering and Systems Science
    "stat"  // Statistics
  ]

  const demosEnabled = currentCategory && demoCategories.some(category => currentCategory.startsWith(category));

  if (demosEnabled) {
    document.getElementById("labstabs-demos-input").removeAttribute("disabled");
    document.getElementById("labstabs-demos-label").style.display = "block";
  }

  var replicateEnabled = demosEnabled
  var spacesEnabled = demosEnabled

  var labsCookie = Cookies.getJSON("arxiv_labs");
  if (labsCookie) {
    has_enabled = false;
    if ( labsCookie["last_tab"] ){
      $(`input#${labsCookie["last_tab"]}:not([disabled])`).click();
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
        } else if (key == "iarxiv-toggle") {
          $.cachedScript(scripts["iarxiv"]).done(function(script, textStatus) {
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
        } else if (key === "replicate-toggle") {
          $.cachedScript(scripts["replicate"]).done(function(script, textStatus) {
            // console.log(textStatus, "replicate (on cookie check)");
          }).fail(function() {
            console.error("failed to load replicate script (on cookie check)", arguments)
          });
        } else if (key === "spaces-toggle") {
          $.cachedScript(scripts["spaces"]).done(function(script, textStatus) {
            console.log(textStatus);
          }).fail(function() {
            console.error("failed to load spaces script (on cookie check)", arguments)
          });
        } else if (key === "connectedpapers-toggle") {
          $.cachedScript(scripts["connectedpapers"]).done(function(script, textStatus) {
            console.log(textStatus);
          });
        }
      } else if (labsCookie[key] && labsCookie[key] == "disabled"){
        if (key === "paperwithcode-toggle") {
          pwcEnabled = false;
        }
        if (key === "replicate-toggle") {
          replicateEnabled = false;
        }
        if (key === "spaces-toggle") {
          spacesEnabled = false;
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

  if(replicateEnabled){
    $("#replicate-toggle.lab-toggle").toggleClass("enabled",true);
    $.cachedScript(scripts["replicate"]).done(function(script, textStatus) {
      // console.log(textStatus, "replicate (on load)");
    }).fail(function() {
      console.error("failed to load replicate script (on load)", arguments)
    });;
  }

  if(spacesEnabled){
    $("#spaces-toggle.lab-toggle").toggleClass("enabled",true);
    $.cachedScript(scripts["spaces"]).done(function(script, textStatus) {
      console.log(textStatus);
    }).fail(function() {
      console.error("failed to load spaces script (on load)", arguments)
    });;
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
    } else if ($(this).attr("id") == "iarxiv-toggle") {
      $.cachedScript(scripts["iarxiv"]).done(function(script, textStatus) {
        console.log(textStatus);
      });
    } else if ($(this).attr("id") == "core-recommender-toggle" && $(this).hasClass("enabled")) {
        $.cachedScript(scripts["core-recommender"]["url"]).done(function(script, textStatus) {});
    } else if ($(this).attr("id") == "paperwithcode-toggle") {
      $.cachedScript(scripts["paperwithcode"]).done(function(script, textStatus) {
        console.log(textStatus);
      });
    } else if ($(this).attr("id") == "replicate-toggle") {
      $.cachedScript(scripts["replicate"]).done(function(script, textStatus) {
        // console.log(textStatus, "replicate (on lab toggle)");
      }).fail(function() {
        console.error("failed to load replicate script (on lab toggle)", arguments)
      });
    } else if ($(this).attr("id") == "spaces-toggle") {
      $.cachedScript(scripts["spaces"]).done(function(script, textStatus) {
        // console.log(textStatus, "spaces (on lab toggle)");
      }).fail(function() {
        console.error("failed to load spaces script (on lab toggle)", arguments)
      });
    } else if ($(this).attr("id") == "connectedpapers-toggle") {
      $.cachedScript(scripts["connectedpapers"]).done(function(script, textStatus) {
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
