// vanilla accordion script. no jquery, dependencies.
var jsaccordion = {
  init : function (target) {
  // initialize the accordion
    var headers = document.querySelectorAll("#" + target + " .toggle-control");
    if (headers.length > 0) { for (var head of headers) {
      head.addEventListener("click", jsaccordion.select);
    }}
  },
  select : function () {
  // fired when user clicks on a header
    var contents = this.nextElementSibling;
    contents.classList.toggle("open");
    var contents = this;
    contents.classList.toggle("open");
  }
};
// runs on page load
window.addEventListener('load', function(){
  jsaccordion.init("toggle-container");
});
