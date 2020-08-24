from helper import flatten, get_title_liked_txt, consecutive_int_list, search_pattern_from_txt, unique
import itertools
import logging
import re


def clean_title(title: str) -> str:
    '''
    ensure the title string is utf-8.
    '''
    if not isinstance(title, str):
        title = title.decode('utf-8', errors="ignore")
    return re.sub(r'\r|\n', '', title)


def _get_outline_page_range(pdf: object, outline: object, next_outline: object) -> tuple:
    try:
        from_page = pdf.getDestinationPageNumber(outline)
    except AttributeError:
        from_page = None
    try:
        to_page = pdf.getDestinationPageNumber(
            next_outline) - 1 if next_outline is not None else from_page
    except AttributeError:
        to_page = None
    return from_page, to_page


def get_toc(pdf: object) -> dict:
    '''
    get the TOC with page number from a pypdf2 object
    '''
    outlines = pdf.getOutlines()
    outlines = flatten(outlines)
    if not outlines:
        logging.warning('Outline is unavailable.')
    outlines, next_outlines = itertools.tee(outlines, 2)
    next_outlines = itertools.chain(
        itertools.islice(next_outlines, 1, None), [None])

    toc = {}

    for outline, next_outline in zip(outlines, next_outlines):
        title = clean_title(outline.title)
        from_page, to_page = _get_outline_page_range(
            pdf, outline, next_outline)
        logging.debug(f'{title.capitalize()}: {from_page} - {to_page}')
        toc[title.capitalize()] = f'{from_page} - {to_page}'
    # print(toc)
    return toc


def get_pages_by_outline(toc: dict, title_pattern: str) -> tuple:
    '''
    search outline title pattern, return the respective outline page range in list.
    '''
    pageRange = []
    for outline, page_range in toc.items():
        if re.search(title_pattern, outline, flags=re.IGNORECASE):
            pageRange.append(page_range.split(' - '))
    if len(pageRange) != 1:
        logging.debug(f'{len(pageRange)} pair of page range is found.')
        return None
    from_page, to_page = pageRange[0]
    return int(from_page), int(to_page)


###################################

def _get_toc(pdf: object) -> dict:
    '''
    under development
    get the TOC with page number from a pypdf2 object
    '''
    outlines = pdf.getOutlines()
    outlines = flatten(outlines)
    if not outlines:
        logging.warning('Outline is unavailable.')
    outlines, next_outlines = itertools.tee(outlines, 2)
    next_outlines = itertools.chain(
        itertools.islice(next_outlines, 1, None), [None])

    toc = {}

    for outline, next_outline in zip(outlines, next_outlines):
        title = clean_title(outline.title)
        from_page, to_page = _get_outline_page_range(
            pdf, outline, next_outline)
        logging.info(f'{title.capitalize()}: {from_page} - {to_page}')
        toc[title.capitalize()] = (sorted([from_page, to_page]))
    return toc

def _get_page_by_outline(toc, title_pattern, to_page=True) -> list:
    '''
    return a list of matched title pattern page range
    '''
    # print('from outline')
    # if to_page:
    #     return [page_range[-1] for outline, page_range in toc.items() if re.search(title_pattern, outline, flags=re.IGNORECASE)] 
    # else:
        # return [page_range for outline, page_range in toc.items() if re.search(title_pattern, outline, flags=re.IGNORECASE)] 
    # return [list(range(page_range[0], page_range[1] + 1)) for outline, page_range in toc.items() if re.search(title_pattern, outline, flags=re.IGNORECASE)] 
    pages = flatten([list(range(page_range[0], page_range[1] + 1)) for outline, page_range in toc.items() if re.search(title_pattern, outline, flags=re.IGNORECASE)])
    consecutive_pages = [tuple(li) for li in consecutive_int_list(unique(pages))]
    return consecutive_pages
    # return [page_range for outline, page_range in toc.items() if re.search(title_pattern, outline, flags=re.IGNORECASE)] 


def _get_page_by_page_title_search(pdfplumber_obj, keywords_pattern=None, verbose=False) -> list:
    '''
    return a list of pages that contains title_pattern
    '''
    if verbose:
        print(f'searching by page!')
    if keywords_pattern is None:
        keywords_pattern =  r'^(?!.*internal)(?=.*report).*auditor.*$'
    pages = []
    for p, page in enumerate(pdfplumber_obj.pages):
        if verbose:
            print(f'searching p.{p}')
        try:
            title_alike_txts = get_title_liked_txt(page)
        except KeyError:
            logging.warning('Non textual page')
            continue
        for txt in title_alike_txts:
            if search_pattern_from_txt(txt, keywords_pattern):
                pages.append(p)
                if verbose: print(f'with pattern: found {txt}on p.{p}!')
    # consecutive_pages = pages
    consecutive_pages = [tuple(li) for li in consecutive_int_list(unique(pages))]
    # consecutive_pages = sorted(flatten([li for li in consecutive_int_list(list(set(pages))) if len(li) > 1]))
    # consecutive_pages = [tuple(li) for li in consecutive_int_list(list(set(pages))) if len(li) > 1]
    return consecutive_pages


if __name__ == "__main__":
    import get_pdf
    from test_cases import test_cases
    from hkex import get_data
    from helper import write_to_csv
    # logging.basicConfig(level=logging.INFO)
    for data in get_data():
        result = {}
        url = data.file_link
        csv = 'indpt_audit_report_2.csv'
        pdf_obj = get_pdf.byte_obj_from_url(url)
        try:
            py_pdf = get_pdf.by_pypdf(pdf_obj)
        except:
            continue
        toc = _get_toc(pdf)
        # print(toc)
        pattern =  r'^(?!.*internal)(?=.*report|responsibilities).*auditor.*$'
        pages = _get_page_by_outline(toc, pattern) or _get_page_by_page_title_search(get_pdf.by_pdfplumber(pdf_obj), pattern)
        result['result'] = pages
        result['toc'] = 'available' if toc else 'unavailable'
        result['url'] = url
        write_to_csv(result, csv)
        pdf_obj.close()