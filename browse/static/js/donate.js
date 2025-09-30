//last update 2025-08-13
function setCookie(bannerName){   
    var delay_days = 7;
    var date = new Date();
    date.setTime(date.getTime()+(delay_days*3600*24*1000));
    var expires = "; expires="+date.toGMTString();    
    document.cookie = `seenBanner_${bannerName}=1` + expires + '; path=/; domain=' + window.location.hostname + ';';
}

function hasCookie(bannerName){
  return document.cookie.indexOf(`seenBanner_${bannerName}=`) !== -1;
}

function parseEasternToUTC(dateStr) {
    // Expecting dateStr = "YYYYMMDDHHMM"
    const year   = parseInt(dateStr.slice(0, 4), 10);
    const month  = parseInt(dateStr.slice(4, 6), 10) - 1; 
    const day    = parseInt(dateStr.slice(6, 8), 10);
    const hour   = parseInt(dateStr.slice(8, 10), 10);
    const minute = parseInt(dateStr.slice(10, 12), 10);

    const easternOffset = 4; 
    return new Date(year, month, day, hour - easternOffset, minute, 0);
}

$(document).ready(
    function() {

      //get the config data for the banner
      const configEl = document.getElementById("banner-config");

      if (!configEl) {
          // No banner config present → no banner
          $(".slider-wrapper").hide();
          return;
      }
      const bannerName = configEl.dataset.bannerName; 
      const bannerEndStr = configEl.dataset.bannerEnd; // form: "202508142340"
      const bannerEnd = parseEasternToUTC(bannerEndStr);
      const now = new Date();

      if (now > bannerEnd) {
          $(".slider-wrapper").hide();
          return;
      }

      //check cookie status

      if( hasCookie(bannerName) ){
        $("#cu-identity").slideDown();
        $(".slider-wrapper").slideUp();
       }   
      
      $(".do-close-slider").click(function() {
        $("#cu-identity").slideDown();
        $(".slider-wrapper").slideUp();
        setCookie(bannerName);       
      });

      $(function() {        
        if( !hasCookie(bannerName) && window.innerWidth > 769 ){
            $(".slider-wrapper").delay(1000).slideDown();
            $("#cu-identity").delay(1000).slideUp();
        }
      });

    });
