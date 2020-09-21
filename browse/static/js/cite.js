// bibtex citation modal 

$(document).ready(function() {
    $('.bib-modal-close').click(function(){
        console.log('clicking to close');
        $('#bib-cite-modal').hide();
    });

    $('#bib-cite-trigger').click(function(){
        $('<link>').appendTo('head')  //load css for cite modal
             .attr({type:'text/css',
                 rel: 'stylesheet',
                 href: $('#bib-cite-css').attr('href')});

        $.ajax({url: "/bibtex/0704.0526", 
                success:function(result){
                    console.log('success with result: ' + result);
                    $('#bib-cite-target').val(result);
                    $('#bib-cite-modal').show();
                }
               });
    } );
});
