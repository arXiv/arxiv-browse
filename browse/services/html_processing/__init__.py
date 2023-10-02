from typing import List, Tuple
from bs4 import BeautifulSoup
import re
from browse.services.documents import get_doc_service

from ..listing import ListingItem

LIST_ITEM_RE = re.compile(r'<\!--\s(.+)\s-->\nLIST:(.+)\n')

def parse_conference_html(html:str) -> Tuple[str, str,List[ListingItem]]:
    split=html.split("\n")
    title=split[5].replace("<h1>","").replace("</h1>","")
    extra_data=""
    
    #pull out all the extra info before paper listings start
    for i in range (6, len(split)):
        line=split[i]
        if line[0:4] =="LIST" or line[0:4]=="<!--":
            break
        extra_data+= line+"\n"
        
    lis=get_lis_for_papers(get_listing_ids(html))
    
    return title, extra_data, lis

def get_listing_ids (html: str) -> List[str]:
    """ Return list of arxiv_ids for LIST: entries in the html """
    return list(map(lambda x: x.group(2), re.finditer(LIST_ITEM_RE, html)))

def get_lis_for_papers (arxiv_ids: List[str]) -> List[ListingItem]:
    lis = []
    for i, id in enumerate(arxiv_ids):
        metadata = get_doc_service().get_abs(id)
        li = ListingItem(
                id,
                'new',
                metadata.primary_category.canonical or metadata.primary_category
            )
        setattr(li, 'article', metadata)
        setattr(li, 'list_index', i + 1)
        lis.append(li)
    return lis

