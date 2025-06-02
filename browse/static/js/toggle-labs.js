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
    "catalyzex": $('#catalyzex-toggle').data('script-url'),
    "huggingface": $('#huggingface-toggle').data('script-url'),
    "replicate": $('#replicate-toggle').data('script-url'),
    "spaces": $('#spaces-toggle').data('script-url'),
    "txyz": $('#txyz-toggle').data('script-url'),
    "dagshub": $('#dagshub-toggle').data('script-url'),
    "litmaps": $('#litmaps-toggle').data('script-url'),
    "scite": $('#scite-toggle').data('script-url'),
    "iarxiv": $('#iarxiv-toggle').data('script-url'),
    "connectedpapers": $('#connectedpapers-toggle').data('script-url'),
    "influenceflower": $('#influenceflower-toggle').data('script-url'),
    "sciencecast": $('#sciencecast-toggle').data('script-url'),
    "gotitpub": $('#gotitpub-toggle').data('script-url'),
    "alphaxiv": $('#alphaxiv-toggle').data('script-url'),
<<<<<<< HEAD
=======
    "summarizepaper": $('#summarizepaper-toggle').data('script-url'),
>>>>>>> Update SummarizePaper toggle functionality and improve UX across project
    "bibex": {
      "url": $('#bibex-toggle').data('script-url'),
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
        } else if (key === "catalyzex-toggle") {
          $.cachedScript(scripts["catalyzex"]).done(function(script, textStatus) {
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
        } else if (key === "txyz-toggle") {
          $.cachedScript(scripts["txyz"]).done(function(script, textStatus) {
            console.log(textStatus);
          }).fail(function() {
            console.error("failed to load txyz script (on cookie check)", arguments)
          });
        } else if (key === "connectedpapers-toggle") {
          $.cachedScript(scripts["connectedpapers"]).done(function(script, textStatus) {
            console.log(textStatus);
          });
        } else if (key === "influenceflower-toggle") {
          $.cachedScript(scripts["influenceflower"]).done(function(script, textStatus) {
            console.log(textStatus);
          });
        } else if (key === "sciencecast-toggle") {
           $.cachedScript(scripts["sciencecast"]).done(function(script, textStatus) {
             console.log(textStatus);
           }).fail(function() {
             console.error("failed to load sciencecast script (on cookie check)", arguments)
           });
        } else if (key === "dagshub-toggle") {
          $.cachedScript(scripts["dagshub"]).done(function(script, textStatus) {
            console.log("DagsHub load: ", textStatus);
          }).fail(function() {
            console.error("failed to load DagsHub script (on cookie check)", arguments)
          });
        } else if (key === "gotitpub-toggle") {
          $.cachedScript(scripts["gotitpub"]).done(function(script, textStatus) {
            console.log(textStatus);
          }).fail(function() {
            console.error("failed to load gotitpub script (on cookie check)", arguments)
          });
        } else if (key === "alphaxiv-toggle") {
          $.cachedScript(scripts["alphaxiv"]).done(function(script, textStatus) {
            console.log(textStatus);
          }).fail(function() {
            console.error("failed to load alphaxiv script (on cookie check)", arguments)
          });
        } else if (key === "huggingface-toggle") {
          $.cachedScript(scripts["huggingface"]).done(function(script, textStatus) {
            console.log(textStatus);
          }).fail(function() {
            console.error("failed to load huggingface script (on cookie check)", arguments)
          });
<<<<<<< HEAD
=======
        } else if (key === "summarizepaper-toggle") {
          $.cachedScript(scripts["summarizepaper"]).done(function(script, textStatus) {
            console.log(textStatus);
          }).fail(function() {
            console.error("failed to load summarizepaper script (on cookie check)", arguments)
          });
>>>>>>> Update SummarizePaper toggle functionality and improve UX across project
        }
      }
    }
  } else {
    Cookies.set("arxiv_labs", { sameSite: "strict", expires: 365 });
  }

  // record last-clicked tab
  $("div.labstabs input[name='tabs']").on("click", function() {
    var labsCookie = Cookies.getJSON("arxiv_labs") || {};
    labsCookie["last_tab"] = $(this).attr("id");
    Cookies.set("arxiv_labs", labsCookie, { sameSite: "strict", expires: 365 });
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
    Cookies.set("arxiv_labs", labsCookie, { sameSite: "strict", expires: 365 });

    if ($(this).attr("id") == "bibex-toggle") {
      bibexCookie[bibex_key] = bibex_val;
      Cookies.set("arxiv_bibex", bibexCookie, { expires: 365 });
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
    } else if ($(this).attr("id") == "catalyzex-toggle") {
      $.cachedScript(scripts["catalyzex"]).done(function(script, textStatus) {
        console.log(textStatus);
      });
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
    } else if ($(this).attr("id") == "txyz-toggle") {
      $.cachedScript(scripts["txyz"]).done(function(script, textStatus) {
      }).fail(function() {
        console.error("failed to load txyz script (on lab toggle)", arguments)
      });
    } else if ($(this).attr("id") == "connectedpapers-toggle") {
      $.cachedScript(scripts["connectedpapers"]).done(function(script, textStatus) {
        console.log(textStatus);
      });
    } else if ($(this).attr("id") == "influenceflower-toggle") {
      $.cachedScript(scripts["influenceflower"]).done(function(script, textStatus) {
        console.log(textStatus);
      });
    } else if ($(this).attr("id") == "sciencecast-toggle") {
       $.cachedScript(scripts["sciencecast"]).done(function(script, textStatus) {
         console.log(textStatus, "sciencecast (on lab toggle)");
       }).fail(function() {
         console.error("failed to load sciencecast script (on lab toggle)", arguments)
       });
    } else if ($(this).attr("id") == "dagshub-toggle") {
      $.cachedScript(scripts["dagshub"]).done(function(script, textStatus) {
        console.log(textStatus, "dagshub (on lab toggle)");
      }).fail(function() {
        console.error("failed to load dagshub script (on lab toggle)", arguments)
      });
    } else if ($(this).attr("id") == "gotitpub-toggle") {
      $.cachedScript(scripts["gotitpub"]).done(function(script, textStatus) {
        console.log(textStatus, "gotitpub (on lab toggle)");
      }).fail(function() {
        console.error("failed to load gotitpub script (on lab toggle)", arguments)
      });
    } else if ($(this).attr("id") == "alphaxiv-toggle") {
      $.cachedScript(scripts["alphaxiv"]).done(function(script, textStatus) {
        console.log(textStatus, "alphaxiv (on lab toggle)");
      }).fail(function() {
        console.error("failed to load alphaxiv script (on lab toggle)", arguments)
      });
    } else if ($(this).attr("id") == "huggingface-toggle") {
      $.cachedScript(scripts["huggingface"]).done(function(script, textStatus) {
        console.log(textStatus, "huggingface (on lab toggle)");
      }).fail(function() {
        console.error("failed to load huggingface script (on lab toggle)", arguments)
      });
<<<<<<< HEAD
=======
    } else if ($(this).attr("id") == "summarizepaper-toggle") {
      $.cachedScript(scripts["summarizepaper"]).done(function(script, textStatus) {
      }).fail(function() {
        console.error("failed to load summarizepaper script (on lab toggle)", arguments)
      });
>>>>>>> Update SummarizePaper toggle functionality and improve UX across project
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
