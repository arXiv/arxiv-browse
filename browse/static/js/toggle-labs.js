// vanilla toggle script for LABS enabling
$(document).ready(function() {

  jQuery.cachedScript = function(url, options) {

    // Allow user to set any option except for dataType, cache, and url
    options = $.extend(options || {}, {
      dataType: "script",
      cache: true,
      url: url
    });

    // Use $.ajax() since it is more flexible than $.getScript
    // Return the jqXHR object so we can chain callbacks
    return jQuery.ajax(options);
  };

  var labsCookie = Cookies.getJSON("arxiv_labs");
  if (labsCookie) {
    for (var key in labsCookie) {
      if (labsCookie[key] && labsCookie[key] == "enabled") {
        $("#" + key + ".lab-toggle").toggleClass("enabled", true);
      }
    }
  } else {
    Cookies.set("arxiv_labs", {});
  }

  $(".lab-toggle").on("click", function() {
    var labsCookie = Cookies.getJSON("arxiv_labs") || {};
    var bibexCookie = Cookies.getJSON("arxiv_bibex");

    var cookie_val = "disabled";
    var bibex_key = "active";
    var bibex_val = false;
    $(this).toggleClass("enabled");
    if ($(this).hasClass("enabled")) {
      cookie_val = "enabled";
      bibex_val = true;
    }
    if ($(this).attr("id") == "bibex-toggle") {
      bibexCookie[bibex_key] = bibex_val;
      Cookies.set("arxiv_bibex", bibexCookie);
      if (bibex_val) {
        $.cachedScript("/static/browse/0.3.0/bibex/bibex.js").done(function(script, textStatus) {
          console.log(textStatus);
        });
      }
    }

    labsCookie[$(this).attr("id")] = cookie_val;
    Cookies.set("arxiv_labs", labsCookie);
    // TODO: do this without a reload
    if (cookie_val == 'disabled') {
      location.reload();
    }
  });
});
