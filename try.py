import requests
import PyPDF2
import io
import itertools


def get_pdf(url):
    response = requests.get(url)
    open_pdf_file = io.BytesIO(response.content)
    pdf = PyPDF2.PdfFileReader(open_pdf_file)
    return pdf


def get_outline_with_page_num(pdf):
    outlines = pdf.getOutlines()
    outlines, next_outlines = itertools.tee(outlines, 2)
    next_outlines = itertools.chain(
        itertools.islice(next_outlines, 1, None), [None])

    for outline, next_outline in zip(outlines, next_outlines):
        title = outline.title
        from_page = pdf.getDestinationPageNumber(outline)
        to_page = pdf.getDestinationPageNumber(
            next_outline) - 1 if next_outline is not None else from_page
        print(f'{title.capitalize()}: {from_page} - {to_page}')


def main(url):
    pdf = get_pdf(url)
    get_outline_with_page_num(pdf)


url = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0728/2020072801178.pdf'
main(url)
