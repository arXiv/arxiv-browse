// bibtex citation modal 
$(document).ready(function() {
    var cached_value=null
    var cached_provider=null
    var setup=0
    var API_CROSSREF_CITE='https://dx.doi.org/'

    var provider_desc={
        arxiv: 'arXiv API',
        doi: 'Crossref Citation Formating Service'
    }

    var provider_url={
        arxiv: 'https://arxiv.org/help/api/index',
        doi: 'https://www.crossref.org/labs/citation-formatting-service/'
    }

    var format_crossref=function(res){
        //TODO
        return res
    }
    
    $('#bib-cite-trigger').click(function(){
        $('#bib-cite-loading').show()
        
        metaid =  document.head.querySelector(`[name="citation_arxiv_id"]`)
        id = metaid ? metaid.content: ''

        metadoi =  document.head.querySelector(`[name="citation_doi"]`)
        doi = metadoi ? metadoi.content: ''

        if(!setup){
            $('.bib-modal-close').click(function(){$('#bib-cite-modal').hide()})
            $('<link>').appendTo('head').attr({type:'text/css',rel: 'stylesheet',href: $('#bib-cite-css').attr('href')})
            setup = 1
        }

        var do_modal=function(result, provider){
            $('#bib-cite-loading').hide()
            $('#bib-cite-target').val(result)
            $('#bib-cite-source-api').text(provider_desc[provider]).attr('href', provider_url[provider])
            $('#bib-cite-modal').show()
        }

        if(cached_value){
            do_modal(cached_value, cached_provider)
        }else if(doi){
            $.ajax({url: API_CROSSREF_CITE + doi,
                    headers: {Accept: `text/bibliography; style=bibtex`},
                    success: function(result){
                        cached_value = format_crossref(result)
                        cached_provider = 'doi'
                        do_modal( cached_value, cached_provider )}})
        }else{
            $.ajax({url: "/bibtex/" + id,
                    success: function(result){
                        cached_value = result
                        cached_provider = 'arxiv'
                        do_modal( cached_value, cached_provider)}})
        }
    })
})
