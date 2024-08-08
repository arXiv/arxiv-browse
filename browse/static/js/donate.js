//version 1.11
function setCookie(){   
    var delay_days = 5;
    var date = new Date();
    date.setTime(date.getTime()+(delay_days*3600*24*1000));
    var expires = "; expires="+date.toGMTString();    
    document.cookie = 'seentheDonateBanner=1' + expires + '; path=/; domain=' + window.location.hostname + ';';
}

function hasCookie(){
    return document.cookie.indexOf('seentheDonateBanner=') != -1;
}

$(document).ready(
    function() {

      if( hasCookie() ){
        $("#cu-identity").slideDown();
        $(".slider-wrapper").slideUp();
       }   
      
      $(".close-slider").click(function() {
        $("#cu-identity").slideDown();
        $(".slider-wrapper").slideUp();
        setCookie();       
      });

      $(function() {        
        if( !hasCookie() && window.innerWidth > 769 ){
            $(".slider-wrapper").delay(1000).slideDown();
            $("#cu-identity").delay(1000).slideUp();
        }
      });

    });
