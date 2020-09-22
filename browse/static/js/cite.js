// bibtex citation modal 

$(document).ready(function() {
    $('.bib-modal-close').click(function() {
        $('#bib-cite-modal').hide();
    });


    var cssloaded=0;
    $('#bib-cite-trigger').click(function(){
        meta =  document.head.querySelector(`[name="citation_arxiv_id"]`);
        id = meta ? meta.content: '';

        if( ! cssloaded ){
            $('<link>').appendTo('head')  //load css for cite modal
                .attr({type:'text/css',
                       rel: 'stylesheet',
                       href: $('#bib-cite-css').attr('href')});
            cssloaded = 1;
        }

        $.ajax({url: "/bibtex/" + id,
                success:function(result){
                    $('#bib-cite-target').val(result);
                    $('#bib-cite-modal').show();
                }
               } );
    } );
});
