from helper import flatten
import itertools, logging
def clean_title(title:str) -> str:
    '''
    ensure the title string is utf-8.
    '''
    if isinstance(title, str):
        title = title.replace('\r', '')
    else:
        title = title.decode('utf-8', errors="ignore").replace('\r', '')
    return title

def get_outline_page_range(pdf: object, outline: object, next_outline: object) -> tuple:
    try:
        from_page = pdf.getDestinationPageNumber(outline)
    except AttributeError:
        from_page = None
    try:
        to_page = pdf.getDestinationPageNumber(next_outline) - 1 if next_outline is not None else from_page
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
    next_outlines = itertools.chain(itertools.islice(next_outlines, 1, None), [None])

    toc = {}

    for outline, next_outline in zip(outlines, next_outlines):
        title = clean_title(outline.title)      
        from_page, to_page = get_outline_page_range(pdf, outline, next_outline)
        logging.debug(f'{title.capitalize()}: {from_page} - {to_page}')
        toc[title.capitalize()] = f'{from_page} - {to_page}'

    return toc

if __name__ == "__main__":
    import get_pdf
    logging.basicConfig(level=logging.DEBUG)
    d = {'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0515/2020051500209.pdf': 45,}
    for url, page_num in d.items():
        pdf = get_pdf.by_pypdf(url)
        get_toc(pdf)
        

