"""handles requests to the catchup page.
Allows users to access something equivalent to the /new page for up to 90 days back
"""
import re
from typing import Tuple, Union, Dict, Any, List
from datetime import date, datetime, timedelta

from http import HTTPStatus
from flask import request, redirect, url_for
from werkzeug.exceptions import BadRequest

from arxiv.document.metadata import DocMetadata
from arxiv.integration.fastly.headers import add_surrogate_key
from arxiv.taxonomy.category import Group, Archive, Category
from arxiv.taxonomy.definitions import CATEGORIES, ARCHIVES, GROUPS, ARCHIVES_ACTIVE

from browse.controllers.archive_page.by_month_form import MONTHS
from browse.controllers.list_page import latexml_links_for_articles, dl_for_articles, authors_for_articles, sub_sections_for_types, Response
from browse.services.database.catchup import get_catchup_data, CATCHUP_LIMIT, get_next_announce_day

def get_catchup_page(subject_str:str, date:str)-> Response:
    """get the catchup page for a given set of request parameters 
    see process_catchup_params for details on parameters
    """
    subject, start_day, include_abs, page=_process_catchup_params(subject_str, date)
    #check for redirects for noncanon subjects
    if subject.id != subject.canonical_id:
        return redirect(
            url_for('catchup', 
                    subject=subject.canonical_id, 
                    date=start_day, 
                    page=page,
                    abs=include_abs), 
            HTTPStatus.MOVED_PERMANENTLY) #type: ignore
    
    headers: Dict[str,str]={}
    headers=add_surrogate_key(headers,["catchup",f"list-{start_day.year:04d}-{start_day.month:02d}-{subject.id}"])
    #get data
    listing=get_catchup_data(subject, start_day, include_abs, page)
    next_announce_day=get_next_announce_day(start_day)

    #format data
    response_data: Dict[str, Any] = {}
    headers.update({'Surrogate-Control': f'max-age={listing.expires}'})
    count= listing.new_count+listing.cross_count+listing.rep_count
    response_data['announced'] = listing.announced
    skip=(page-1)*CATCHUP_LIMIT
    response_data.update(catchup_index_for_types(listing.new_count, listing.cross_count, listing.rep_count,  subject, start_day, include_abs, page))
    response_data.update(sub_sections_for_types(listing, skip, CATCHUP_LIMIT))

    idx = 0
    for item in listing.listings:
        idx = idx + 1
        setattr(item, 'list_index', idx + skip)

    response_data['listings'] = listing.listings
    response_data['author_links'] = authors_for_articles(listing.listings)
    response_data['downloads'] = dl_for_articles(listing.listings)
    response_data['latexml'] = latexml_links_for_articles(listing.listings)

    response_data.update({
        'subject':subject,
        'date': start_day,
        'next_day':next_announce_day,
        'page':page,
        'include_abs': include_abs,
        'count': count,
        'list_type':"new" if include_abs else "catchup", #how the list macro checks to display abstract
        'paging': catchup_paging(subject, start_day, include_abs, page, count)
    })

    def author_query(article: DocMetadata, query: str)->str:
        try:
            if article.primary_archive:
                archive_id = article.primary_archive.id
            elif article.primary_category:
                archive_id = article.primary_category.in_archive
            else:
                archive_id='' 
            return str(url_for('search_archive',
                           searchtype='author',
                           archive=archive_id,
                           query=query))
        except (AttributeError, KeyError):
            return str(url_for('search_archive',
                               searchtype='author',
                               archive=archive_id,
                               query=query))

    response_data['url_for_author_search'] = author_query

    return response_data, 200, headers

def get_catchup_form() -> Response:
    #check for form/parameter requests
    subject = request.args.get('subject')  
    date = request.args.get('date') 
    include_abs = request.args.get('include_abs') 
    if subject and date:
        if include_abs:
            new_address= url_for('.catchup', subject=subject, date=date, abs=include_abs)
        else:
            new_address=url_for('.catchup', subject=subject, date=date)
        return {}, 302, {'Location':new_address}
    
    #otherwise create catchup form
    response_data={}
    response_data['years']= [datetime.now().year, datetime.now().year-1] #only last 90 days allowed anyways
    response_data['months']= MONTHS[1:]
    response_data['current_month']=datetime.now().strftime('%m')
    response_data['days']= [str(day).zfill(2) for day in range(1, 32)]
    response_data['groups']= GROUPS

    return response_data, 200, {}


def _process_catchup_params(subject_str:str, date_str:str)->Tuple[Union[Group, Archive, Category], date, bool, int]:
    """processes the request parameters to the catchup page
    raises an error or returns usable values

    Returns:
    subject: as a Group, Archive, or Category. Still needs to be checked for canonicalness
    start_day: date (date to catchup on)
    abs: bool (include abstracts or not )
    page: int (which page of results, default is 1)
    """

    #check for valid arguments
    ALLOWED_PARAMS={"abs", "page"}
    unexpected_params = request.args.keys() - ALLOWED_PARAMS
    if unexpected_params:
        raise BadRequest(f"Unexpected parameters. Only accepted parameters are: 'page', and 'abs'")
        
    #subject validation
    subject: Union[Group, Archive, Category]
    if subject_str == "grp_physics":
        subject=GROUPS["grp_physics"]
    elif subject_str in ARCHIVES:
        subject= ARCHIVES[subject_str]
    elif subject_str in CATEGORIES:
        subject= CATEGORIES[subject_str]
    else:
        raise BadRequest("Invalid subject. Subject must be an archive, category or 'grp_physics'")
    
    #date validation
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str): #enforce two digit days and months
        raise BadRequest(f"Invalid date format. Use format: YYYY-MM-DD")
    try:
        start_day= datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise BadRequest(f"Invalid date format. Use format: YYYY-MM-DD")
    #only allow dates within the last 90 days (91 just in case time zone differences)
    today=datetime.now().date()
    earliest_allowed=today - timedelta(days=91)
    if start_day < earliest_allowed:
        #TODO link to earliest allowed date
        raise BadRequest(f"Invalid date: {start_day}. Catchup only allowed for past 90 days")
    elif start_day > today:
        raise BadRequest(f"Invalid date: {start_day}. Can't request date later than today")

    #include abstract or not
    abs_str=request.args.get("abs","False")
    if abs_str == "True":
        include_abs=True
    elif abs_str == "False":
        include_abs=False
    else:
        raise BadRequest(f"Invalid abs value. Use ?abs=True to include abstracts or ?abs=False to not")

    #select page number (each page has 2000 items)
    page_str = request.args.get("page", "1") #page defaults to 1
    if page_str.isdigit():
        page=int(page_str)
    else:
        raise BadRequest(f"Invalid page value. Page value should be a positive integer like ?page=3")
    if page<1:
        raise BadRequest(f"Invalid page value. Page value should be a positive integer like ?page=3")

    return subject, start_day, include_abs, page

def catchup_paging(subject: Union[Group, Archive, Category], day:date, include_abs:bool, page: int, count:int)-> List[Tuple[str,str]]:
    '''creates a dictionary of page links for the case that there is more than one page of data'''
    if CATCHUP_LIMIT >= count: #only one page
        return []
    
    total_pages=count//CATCHUP_LIMIT+1
    url_base=url_for('.catchup', subject=subject.id, date=day.strftime('%Y-%m-%d'), abs=include_abs)
    page_links=[]

    if total_pages <10: #realistically there should be at most 2-3 pages per day
        for i in range(1,total_pages+1):
            if i == page:
                page_links.append((str(i),'no-link'))
            else:
                page_links.append((str(i),url_base+f'&page={i}'))
    
    else: #shouldnt happen but its handled
        if page !=1:
            page_links.append(('1',url_base+f'&page=1'))
        if page >2:
            page_links.append(('...','no-link'))
        page_links.append((str(page),'no-link'))
        if page <total_pages-1:
            page_links.append(('...','no-link'))
        if page !=total_pages:
            page_links.append((str(total_pages), url_base+f'&page={total_pages}'))

    return page_links

def catchup_index_for_types(new_count:int, cross_count:int, rep_count:int,  subject: Union[Group, Archive, Category], day:date, include_abs:bool, page: int) ->Dict[str, Any]:
    """Creates index for types for catchup papers. 
    page count and index both start at 1
    """
    ift = []

    if new_count > 0:
        if page != 1:
            ift.append(('New submissions',
                        url_for('.catchup', subject=subject.id, date=day.strftime('%Y-%m-%d'), abs=include_abs, page=1),
                        1))
        else:
            ift.append(('New submissions', '', 1)) 

    if cross_count > 0:
        cross_start = new_count + 1
        cross_start_page=(cross_start-1)//CATCHUP_LIMIT +1 #item 2000 is on page 1, 2001 is on page 2
        cross_index=cross_start-(cross_start_page-1)*CATCHUP_LIMIT 

        if page==cross_start_page:
            ift.append(('Cross-lists', '', cross_index))
        else:
            ift.append(('Cross-lists',
                        url_for('.catchup', subject=subject.id, date=day.strftime('%Y-%m-%d'), abs=include_abs, page=cross_start_page),
                        cross_index))
            
    if rep_count > 0:
        rep_start = new_count + cross_count+ 1
        rep_start_page=(rep_start-1)//CATCHUP_LIMIT +1 #item 2000 is on page 1, 2001 is on page 2
        rep_index=rep_start-(rep_start_page-1)*CATCHUP_LIMIT 

        if page==rep_start_page:
            ift.append(('Replacements', '', rep_index))
        else:
            ift.append(('Replacements',
                        url_for('.catchup', subject=subject.id, date=day.strftime('%Y-%m-%d'), abs=include_abs, page=rep_start_page),
                        rep_index))

    return {'index_for_types': ift}
