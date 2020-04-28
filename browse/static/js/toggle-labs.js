// vanilla toggle script for LABS enabling
document.addEventListener("DOMContentLoaded", function() {
  Array.prototype.forEach.call(
    document.querySelectorAll('.lab-toggle'),
      function(element) {
          element.onclick = enableSwitch;
      }
  );
  function enableSwitch(element){
   element = this;
    if( element.classList.contains('enabled') ){
    element.classList.remove('enabled');
  } else {
   element.classList.add('enabled');
    }
  }
});
