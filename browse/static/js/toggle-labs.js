// vanilla toggle script for LABS enabling
$(document).ready(function() {
  var labsCookie = Cookies.getJSON("arxiv_labs");
  if ( labsCookie ) {
    for ( var key in labsCookie ) {
      if ( labsCookie[key] == "enabled" ) {
        $("#"+key+".lab-toggle").toggleClass("enabled", true);
      }
    }
  }

  $(".lab-toggle").on("click", function() {
    var labsCookie = Cookies.getJSON("arxiv_labs");
    var bibexCookie = Cookies.getJSON("arxiv_bibex");

    var cookie_val = "disabled";
    var bibex_key = "active";
    var bibex_val = false;
    $(this).toggleClass("enabled");
    if ( $(this).hasClass("enabled") ) {
      cookie_val = "enabled";
      bibex_val = true;
    }
    if ( $(this).attr("id") == "bibex-toggle" ) {
      bibexCookie[bibex_key] = bibex_val;
      Cookies.set("arxiv_bibex", bibexCookie);
    }

    labsCookie[$(this).attr("id")] = cookie_val;
    Cookies.set("arxiv_labs", labsCookie);
  });
});
