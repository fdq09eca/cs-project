import requests
import PyPDF2
import io
import itertools
import re
# get pdf


def get_pdf(url):
    '''
    get the pdf file from url
    '''
    response = requests.get(url)
    open_pdf_file = io.BytesIO(response.content)
    pdf = PyPDF2.PdfFileReader(open_pdf_file)
    return pdf


# get the TOC with page

def flatten(li) -> list:
    '''
    flatten a irregular list recursively;
    Usecase: for flattening multiple levels of outlines.
    '''
    return sum(map(flatten, li), []) if isinstance(li, list) else [li]


def get_toc(pdf):
    '''
    get the TOC with page number
    '''
    outlines = pdf.getOutlines()
    outlines = flatten(outlines)
    if len(outlines) == 0:
        print('Outline is unavailable.')
    outlines, next_outlines = itertools.tee(outlines, 2)
    next_outlines = itertools.chain(
        itertools.islice(next_outlines, 1, None), [None])

    toc = {}

    for outline, next_outline in zip(outlines, next_outlines):

        title = outline.title
        if isinstance(title, str):
            title = title.replace('\r', '')
        else:
            title = title.decode('utf-8', errors="ignore").replace('\r', '')

        try:
            from_page = pdf.getDestinationPageNumber(outline)
        except AttributeError:
            from_page = None
        try:
            to_page = pdf.getDestinationPageNumber(
                next_outline) - 1 if next_outline is not None else from_page
        except AttributeError:
            to_page = None

        print(f'{title.capitalize()}: {from_page} - {to_page}')
        toc[title.capitalize()] = f'{from_page} - {to_page}'

    return toc

# get the independent auditor report

# search the auditor in the auditor report


def get_auditor(indpt_audit_report, p):
    # get the last page of the indpt_audit_report
    page = indpt_audit_report.getPage(p)
    text = page.extractText()
    text = re.sub('\n+', '', text)
    pattern = r'.*\.((?P<auditor>.*?):?( LLP)?)( ?Certified )?Public Accountants'
    # pattern = r'(:?.*\.[\s\n]?(?P<auditor>.*))[\s\n]?(?:Certified )?Public Accountants'
    auditor = re.search(pattern, text).group('auditor')
    print(auditor)
    return auditor


def main(url, p):
    # get pdf
    pdf = get_pdf(url)
    # get the TOC with page
    get_toc(pdf)
    # split the pdf into sections

    # get the independent auditor report

    # get the auditor firm title
    get_auditor(pdf, p)
    # search particular key audit matters (KAM)
    # insert entry to database


def test(d):
    links = ['/listedco/listconews/sehk/2020/0728/2020072801178.pdf', '/listedco/listconews/sehk/2020/0728/2020072800870.pdf', '/listedco/listconews/sehk/2020/0728/2020072800836.pdf', '/listedco/listconews/sehk/2020/0728/2020072800808.pdf', '/listedco/listconews/sehk/2020/0728/2020072800527.pdf', '/listedco/listconews/sehk/2020/0728/2020072800513.pdf', '/listedco/listconews/sehk/2020/0728/2020072800475.pdf', '/listedco/listconews/sehk/2020/0728/2020072800473.pdf', '/listedco/listconews/sehk/2020/0728/2020072800460.pdf', '/listedco/listconews/sehk/2020/0728/2020072800454.pdf', '/listedco/listconews/sehk/2020/0728/2020072800446.pdf', '/listedco/listconews/sehk/2020/0728/2020072800342.pdf', '/listedco/listconews/sehk/2020/0728/2020072800292.pdf', '/listedco/listconews/sehk/2020/0728/2020072800263.pdf', '/listedco/listconews/sehk/2020/0728/2020072800129.pdf', '/listedco/listconews/sehk/2020/0727/2020072701507.pdf', '/listedco/listconews/sehk/2020/0727/2020072701317.pdf', '/listedco/listconews/sehk/2020/0727/2020072700962.pdf', '/listedco/listconews/sehk/2020/0727/2020072700957.pdf', '/listedco/listconews/sehk/2020/0727/2020072700942.pdf', '/listedco/listconews/sehk/2020/0727/2020072700802.pdf', '/listedco/listconews/sehk/2020/0727/2020072700775.pdf', '/listedco/listconews/sehk/2020/0727/2020072700742.pdf', '/listedco/listconews/sehk/2020/0727/2020072700728.pdf', '/listedco/listconews/sehk/2020/0727/2020072700682.pdf', '/listedco/listconews/sehk/2020/0727/2020072700670.pdf', '/listedco/listconews/sehk/2020/0727/2020072700604.pdf', '/listedco/listconews/sehk/2020/0727/2020072700598.pdf', '/listedco/listconews/sehk/2020/0727/2020072700588.pdf', '/listedco/listconews/sehk/2020/0727/2020072700580.pdf', '/listedco/listconews/sehk/2020/0727/2020072700570.pdf', '/listedco/listconews/sehk/2020/0727/2020072700559.pdf', '/listedco/listconews/sehk/2020/0727/2020072700551.pdf', '/listedco/listconews/sehk/2020/0727/2020072700481.pdf', '/listedco/listconews/sehk/2020/0727/2020072700477.pdf', '/listedco/listconews/sehk/2020/0727/2020072700471.pdf', '/listedco/listconews/sehk/2020/0727/2020072700417.pdf', '/listedco/listconews/sehk/2020/0727/2020072700405.pdf', '/listedco/listconews/sehk/2020/0727/2020072700403.pdf', '/listedco/listconews/sehk/2020/0727/2020072700339.pdf', '/listedco/listconews/sehk/2020/0727/2020072700163.pdf', '/listedco/listconews/sehk/2020/0724/2020072401446.pdf', '/listedco/listconews/sehk/2020/0724/2020072401122.pdf', '/listedco/listconews/sehk/2020/0724/2020072400992.pdf', '/listedco/listconews/sehk/2020/0724/2020072400950.pdf', '/listedco/listconews/sehk/2020/0724/2020072400775.pdf', '/listedco/listconews/sehk/2020/0724/2020072400731.pdf', '/listedco/listconews/sehk/2020/0724/2020072400727.pdf', '/listedco/listconews/sehk/2020/0724/2020072400677.pdf', '/listedco/listconews/sehk/2020/0724/2020072400603.pdf', '/listedco/listconews/sehk/2020/0724/2020072400597.pdf', '/listedco/listconews/sehk/2020/0724/2020072400583.pdf', '/listedco/listconews/sehk/2020/0724/2020072400579.pdf', '/listedco/listconews/sehk/2020/0724/2020072400558.pdf', '/listedco/listconews/sehk/2020/0724/2020072400550.pdf', '/listedco/listconews/sehk/2020/0724/2020072400490.pdf', '/listedco/listconews/sehk/2020/0724/2020072400454.pdf', '/listedco/listconews/sehk/2020/0724/2020072400215.pdf', '/listedco/listconews/sehk/2020/0723/2020072301280.pdf', '/listedco/listconews/sehk/2020/0723/2020072301101.pdf', '/listedco/listconews/sehk/2020/0723/2020072301061.pdf', '/listedco/listconews/sehk/2020/0723/2020072301013.pdf', '/listedco/listconews/sehk/2020/0723/2020072300897.pdf', '/listedco/listconews/sehk/2020/0723/2020072300893.pdf', '/listedco/listconews/sehk/2020/0723/2020072300753.pdf', '/listedco/listconews/sehk/2020/0723/2020072300731.pdf', '/listedco/listconews/sehk/2020/0723/2020072300680.pdf', '/listedco/listconews/sehk/2020/0723/2020072300678.pdf', '/listedco/listconews/sehk/2020/0723/2020072300600.pdf', '/listedco/listconews/sehk/2020/0723/2020072300590.pdf', '/listedco/listconews/sehk/2020/0723/2020072300584.pdf', '/listedco/listconews/sehk/2020/0723/2020072300556.pdf', '/listedco/listconews/sehk/2020/0723/2020072300554.pdf', '/listedco/listconews/sehk/2020/0723/2020072300498.pdf', '/listedco/listconews/sehk/2020/0723/2020072300476.pdf', '/listedco/listconews/gem/2020/0723/2020072300452.pdf', '/listedco/listconews/sehk/2020/0723/2020072300448.pdf', '/listedco/listconews/sehk/2020/0723/2020072300444.pdf', '/listedco/listconews/sehk/2020/0723/2020072300438.pdf', '/listedco/listconews/sehk/2020/0723/2020072300426.pdf', '/listedco/listconews/sehk/2020/0723/2020072300410.pdf', '/listedco/listconews/sehk/2020/0723/2020072300399.pdf', '/listedco/listconews/sehk/2020/0723/2020072300395.pdf', '/listedco/listconews/sehk/2020/0723/2020072300391.pdf', '/listedco/listconews/sehk/2020/0723/2020072300301.pdf', '/listedco/listconews/sehk/2020/0723/2020072300219.pdf', '/listedco/listconews/sehk/2020/0722/2020072201173.pdf', '/listedco/listconews/sehk/2020/0722/2020072200865.pdf', '/listedco/listconews/sehk/2020/0722/2020072200804.pdf', '/listedco/listconews/sehk/2020/0722/2020072200757.pdf', '/listedco/listconews/sehk/2020/0722/2020072200734.pdf', '/listedco/listconews/sehk/2020/0722/2020072200653.pdf', '/listedco/listconews/sehk/2020/0722/2020072200600.pdf', '/listedco/listconews/sehk/2020/0722/2020072200596.pdf', '/listedco/listconews/sehk/2020/0722/2020072200572.pdf', '/listedco/listconews/sehk/2020/0722/2020072200554.pdf', '/listedco/listconews/sehk/2020/0722/2020072200488.pdf', '/listedco/listconews/sehk/2020/0722/2020072200478.pdf', '/listedco/listconews/sehk/2020/0722/2020072200462.pdf', '/listedco/listconews/sehk/2020/0722/2020072200440.pdf', '/listedco/listconews/sehk/2020/0722/2020072200438.pdf', '/listedco/listconews/sehk/2020/0722/2020072200434.pdf', '/listedco/listconews/sehk/2020/0722/2020072200342.pdf', '/listedco/listconews/sehk/2020/0722/2020072200312.pdf', '/listedco/listconews/sehk/2020/0722/2020072200165.pdf', '/listedco/listconews/sehk/2020/0722/2020072200027.pdf', '/listedco/listconews/sehk/2020/0721/2020072101475.pdf', '/listedco/listconews/sehk/2020/0721/2020072101273.pdf', '/listedco/listconews/sehk/2020/0721/2020072101136.pdf', '/listedco/listconews/sehk/2020/0721/2020072101044.pdf', '/listedco/listconews/sehk/2020/0721/2020072100787.pdf', '/listedco/listconews/sehk/2020/0721/2020072100713.pdf', '/listedco/listconews/sehk/2020/0721/2020072100655.pdf', '/listedco/listconews/sehk/2020/0721/2020072100653.pdf', '/listedco/listconews/sehk/2020/0721/2020072100637.pdf', '/listedco/listconews/sehk/2020/0721/2020072100609.pdf', '/listedco/listconews/sehk/2020/0721/2020072100607.pdf', '/listedco/listconews/sehk/2020/0721/2020072100601.pdf', '/listedco/listconews/sehk/2020/0721/2020072100549.pdf', '/listedco/listconews/sehk/2020/0721/2020072100487.pdf', '/listedco/listconews/sehk/2020/0721/2020072100485.pdf', '/listedco/listconews/sehk/2020/0721/2020072100333.pdf', '/listedco/listconews/sehk/2020/0721/2020072100213.pdf', '/listedco/listconews/sehk/2020/0720/2020072000988.pdf', '/listedco/listconews/sehk/2020/0720/2020072000717.pdf', '/listedco/listconews/sehk/2020/0720/2020072000601.pdf', '/listedco/listconews/sehk/2020/0720/2020072000561.pdf', '/listedco/listconews/sehk/2020/0720/2020072000518.pdf', '/listedco/listconews/sehk/2020/0720/2020072000498.pdf', '/listedco/listconews/sehk/2020/0720/2020072000494.pdf', '/listedco/listconews/sehk/2020/0720/2020072000113.pdf', '/listedco/listconews/sehk/2020/0719/2020071900019.pdf', '/listedco/listconews/sehk/2020/0719/2020071900015.pdf', '/listedco/listconews/sehk/2020/0717/2020071701202.pdf', '/listedco/listconews/sehk/2020/0717/2020071701061.pdf', '/listedco/listconews/sehk/2020/0717/2020071700849.pdf', '/listedco/listconews/sehk/2020/0717/2020071700747.pdf', '/listedco/listconews/sehk/2020/0717/2020071700726.pdf', '/listedco/listconews/sehk/2020/0717/2020071700724.pdf', '/listedco/listconews/sehk/2020/0717/2020071700637.pdf', '/listedco/listconews/sehk/2020/0717/2020071700621.pdf', '/listedco/listconews/sehk/2020/0717/2020071700552.htm', '/listedco/listconews/sehk/2020/0717/2020071700529.pdf', '/listedco/listconews/sehk/2020/0717/2020071700499.pdf', '/listedco/listconews/sehk/2020/0717/2020071700480.pdf', '/listedco/listconews/sehk/2020/0717/2020071700428.pdf', '/listedco/listconews/sehk/2020/0717/2020071700400.pdf', '/listedco/listconews/sehk/2020/0717/2020071700388.pdf', '/listedco/listconews/sehk/2020/0717/2020071700127.pdf', '/listedco/listconews/sehk/2020/0717/2020071700051.pdf', '/listedco/listconews/sehk/2020/0717/2020071700031.pdf', '/listedco/listconews/sehk/2020/0717/2020071700007.pdf', '/listedco/listconews/sehk/2020/0716/2020071601188.pdf', '/listedco/listconews/sehk/2020/0716/2020071601178.pdf', '/listedco/listconews/sehk/2020/0716/2020071601089.pdf', '/listedco/listconews/sehk/2020/0716/2020071600963.pdf', '/listedco/listconews/sehk/2020/0716/2020071600949.pdf', '/listedco/listconews/sehk/2020/0716/2020071600886.pdf', '/listedco/listconews/sehk/2020/0716/2020071600863.pdf', '/listedco/listconews/sehk/2020/0716/2020071600702.pdf', '/listedco/listconews/sehk/2020/0716/2020071600648.pdf', '/listedco/listconews/sehk/2020/0716/2020071600636.pdf', '/listedco/listconews/sehk/2020/0716/2020071600628.pdf', '/listedco/listconews/sehk/2020/0716/2020071600576.pdf', '/listedco/listconews/sehk/2020/0716/2020071600560.pdf', '/listedco/listconews/sehk/2020/0716/2020071600556.pdf', '/listedco/listconews/sehk/2020/0716/2020071600552.pdf', '/listedco/listconews/sehk/2020/0716/2020071600536.pdf', '/listedco/listconews/sehk/2020/0716/2020071600518.pdf', '/listedco/listconews/sehk/2020/0716/2020071600510.pdf',
             '/listedco/listconews/sehk/2020/0716/2020071600480.pdf', '/listedco/listconews/sehk/2020/0716/2020071600474.pdf', '/listedco/listconews/sehk/2020/0715/2020071501240.pdf', '/listedco/listconews/gem/2020/0715/2020071500889.pdf', '/listedco/listconews/sehk/2020/0715/2020071500720.pdf', '/listedco/listconews/sehk/2020/0715/2020071500470.pdf', '/listedco/listconews/sehk/2020/0715/2020071500451.pdf', '/listedco/listconews/sehk/2020/0715/2020071500419.pdf', '/listedco/listconews/sehk/2020/0715/2020071500377.pdf', '/listedco/listconews/sehk/2020/0715/2020071500329.pdf', '/listedco/listconews/sehk/2020/0715/2020071500213.pdf', '/listedco/listconews/sehk/2020/0715/2020071500005.pdf', '/listedco/listconews/sehk/2020/0714/2020071401074.pdf', '/listedco/listconews/sehk/2020/0714/2020071401058.pdf', '/listedco/listconews/sehk/2020/0714/2020071400977.pdf', '/listedco/listconews/sehk/2020/0714/2020071400871.pdf', '/listedco/listconews/sehk/2020/0714/2020071400735.pdf', '/listedco/listconews/sehk/2020/0714/2020071400721.pdf', '/listedco/listconews/sehk/2020/0714/2020071400717.pdf', '/listedco/listconews/sehk/2020/0714/2020071400612.pdf', '/listedco/listconews/sehk/2020/0714/2020071400598.pdf', '/listedco/listconews/sehk/2020/0714/2020071400590.pdf', '/listedco/listconews/sehk/2020/0714/2020071400576.pdf', '/listedco/listconews/sehk/2020/0714/2020071400570.pdf', '/listedco/listconews/sehk/2020/0714/2020071400564.pdf', '/listedco/listconews/sehk/2020/0714/2020071400550.pdf', '/listedco/listconews/sehk/2020/0713/2020071300894.pdf', '/listedco/listconews/sehk/2020/0713/2020071300746.pdf', '/listedco/listconews/sehk/2020/0713/2020071300376.pdf', '/listedco/listconews/sehk/2020/0713/2020071300157.pdf', '/listedco/listconews/sehk/2020/0710/2020071000907.pdf', '/listedco/listconews/sehk/2020/0710/2020071000511.pdf', '/listedco/listconews/sehk/2020/0710/2020071000505.pdf', '/listedco/listconews/sehk/2020/0710/2020071000416.pdf', '/listedco/listconews/sehk/2020/0710/2020071000402.pdf', '/listedco/listconews/sehk/2020/0710/2020071000013.pdf', '/listedco/listconews/sehk/2020/0709/2020070901013.pdf', '/listedco/listconews/sehk/2020/0709/2020070900659.pdf', '/listedco/listconews/sehk/2020/0709/2020070900612.pdf', '/listedco/listconews/sehk/2020/0708/2020070800866.pdf', '/listedco/listconews/sehk/2020/0708/2020070800440.pdf', '/listedco/listconews/sehk/2020/0708/2020070800363.pdf', '/listedco/listconews/sehk/2020/0707/2020070701693.pdf', '/listedco/listconews/sehk/2020/0707/2020070701577.pdf', '/listedco/listconews/sehk/2020/0707/2020070701188.pdf', '/listedco/listconews/sehk/2020/0707/2020070701022.pdf', '/listedco/listconews/sehk/2020/0707/2020070700890.pdf', '/listedco/listconews/sehk/2020/0707/2020070700792.pdf', '/listedco/listconews/sehk/2020/0707/2020070700123.pdf', '/listedco/listconews/gem/2020/0707/2020070700013.pdf', '/listedco/listconews/sehk/2020/0706/2020070601968.pdf', '/listedco/listconews/sehk/2020/0706/2020070601946.pdf', '/listedco/listconews/gem/2020/0706/2020070601906.pdf', '/listedco/listconews/sehk/2020/0706/2020070600997.pdf', '/listedco/listconews/sehk/2020/0706/2020070600947.pdf', '/listedco/listconews/sehk/2020/0706/2020070600895.pdf', '/listedco/listconews/gem/2020/0703/2020070302803.pdf', '/listedco/listconews/sehk/2020/0703/2020070301717.pdf', '/listedco/listconews/sehk/2020/0703/2020070301658.pdf', '/listedco/listconews/sehk/2020/0703/2020070301488.pdf', '/listedco/listconews/sehk/2020/0702/2020070203743.pdf', '/listedco/listconews/sehk/2020/0702/2020070203407.pdf', '/listedco/listconews/gem/2020/0702/2020070202599.pdf', '/listedco/listconews/gem/2020/0702/2020070202255.pdf', '/listedco/listconews/sehk/2020/0702/2020070202029.pdf', '/listedco/listconews/sehk/2020/0702/2020070201571.pdf', '/listedco/listconews/gem/2020/0702/2020070200867.pdf', '/listedco/listconews/gem/2020/0702/2020070200801.pdf', '/listedco/listconews/gem/2020/0702/2020070200074.pdf', '/listedco/listconews/gem/2020/0701/2020070100181.pdf', '/listedco/listconews/gem/2020/0701/2020070100101.pdf', '/listedco/listconews/gem/2020/0701/2020070100061.pdf', '/listedco/listconews/gem/2020/0701/2020070100029.pdf', '/listedco/listconews/gem/2020/0701/2020070100011.pdf', '/listedco/listconews/sehk/2020/0630/2020063002720.pdf', '/listedco/listconews/gem/2020/0630/2020063002702.pdf', '/listedco/listconews/gem/2020/0630/2020063002684.pdf', '/listedco/listconews/sehk/2020/0630/2020063002676.pdf', '/listedco/listconews/gem/2020/0630/2020063002674.pdf', '/listedco/listconews/gem/2020/0630/2020063002664.pdf', '/listedco/listconews/gem/2020/0630/2020063002616.pdf', '/listedco/listconews/gem/2020/0630/2020063002460.pdf', '/listedco/listconews/gem/2020/0630/2020063002420.pdf', '/listedco/listconews/sehk/2020/0630/2020063002326.pdf', '/listedco/listconews/gem/2020/0630/2020063002298.pdf', '/listedco/listconews/gem/2020/0630/2020063002260.pdf', '/listedco/listconews/gem/2020/0630/2020063001688.pdf', '/listedco/listconews/gem/2020/0630/2020063001678.pdf', '/listedco/listconews/sehk/2020/0630/2020063001518.pdf', '/listedco/listconews/gem/2020/0630/2020063001256.pdf', '/listedco/listconews/gem/2020/0630/2020063000956.pdf', '/listedco/listconews/gem/2020/0630/2020063000934.pdf', '/listedco/listconews/sehk/2020/0630/2020063000926.pdf', '/listedco/listconews/sehk/2020/0630/2020063000788.pdf', '/listedco/listconews/gem/2020/0630/2020063000786.pdf', '/listedco/listconews/gem/2020/0630/2020063000751.pdf', '/listedco/listconews/gem/2020/0630/2020063000709.pdf', '/listedco/listconews/gem/2020/0630/2020063000705.pdf', '/listedco/listconews/gem/2020/0630/2020063000687.pdf', '/listedco/listconews/gem/2020/0630/2020063000683.pdf', '/listedco/listconews/gem/2020/0630/2020063000681.pdf', '/listedco/listconews/gem/2020/0630/2020063000514.pdf', '/listedco/listconews/gem/2020/0630/2020063000359.pdf', '/listedco/listconews/gem/2020/0630/2020063000335.pdf', '/listedco/listconews/gem/2020/0630/2020063000333.pdf', '/listedco/listconews/sehk/2020/0630/2020063000327.pdf', '/listedco/listconews/gem/2020/0630/2020063000295.pdf', '/listedco/listconews/sehk/2020/0630/2020063000185.pdf', '/listedco/listconews/gem/2020/0630/2020063000133.pdf', '/listedco/listconews/gem/2020/0630/2020063000069.pdf', '/listedco/listconews/sehk/2020/0630/2020063000053.pdf', '/listedco/listconews/sehk/2020/0630/2020063000025.pdf', '/listedco/listconews/gem/2020/0629/2020062902713.pdf', '/listedco/listconews/gem/2020/0629/2020062902347.pdf', '/listedco/listconews/gem/2020/0629/2020062902181.pdf', '/listedco/listconews/gem/2020/0629/2020062902163.pdf', '/listedco/listconews/sehk/2020/0629/2020062901915.pdf', '/listedco/listconews/gem/2020/0629/2020062901894.pdf', '/listedco/listconews/gem/2020/0629/2020062901867.pdf', '/listedco/listconews/gem/2020/0629/2020062901859.pdf', '/listedco/listconews/sehk/2020/0629/2020062901847.pdf', '/listedco/listconews/gem/2020/0629/2020062901841.pdf', '/listedco/listconews/gem/2020/0629/2020062901819.pdf', '/listedco/listconews/gem/2020/0629/2020062901807.pdf', '/listedco/listconews/gem/2020/0629/2020062901781.pdf', '/listedco/listconews/gem/2020/0629/2020062901733.pdf', '/listedco/listconews/gem/2020/0629/2020062901645.pdf', '/listedco/listconews/gem/2020/0629/2020062901552.pdf', '/listedco/listconews/gem/2020/0629/2020062901536.pdf', '/listedco/listconews/gem/2020/0629/2020062901484.pdf', '/listedco/listconews/gem/2020/0629/2020062901462.pdf', '/listedco/listconews/gem/2020/0629/2020062901423.pdf', '/listedco/listconews/gem/2020/0629/2020062901393.pdf', '/listedco/listconews/gem/2020/0629/2020062901274.pdf', '/listedco/listconews/gem/2020/0629/2020062901252.pdf', '/listedco/listconews/gem/2020/0629/2020062901250.pdf', '/listedco/listconews/gem/2020/0629/2020062901174.pdf', '/listedco/listconews/gem/2020/0629/2020062901148.pdf', '/listedco/listconews/sehk/2020/0629/2020062901064.pdf', '/listedco/listconews/gem/2020/0629/2020062901014.pdf', '/listedco/listconews/gem/2020/0629/2020062900988.pdf', '/listedco/listconews/gem/2020/0629/2020062900980.pdf', '/listedco/listconews/gem/2020/0629/2020062900950.pdf', '/listedco/listconews/gem/2020/0629/2020062900914.pdf', '/listedco/listconews/gem/2020/0629/2020062900908.pdf', '/listedco/listconews/gem/2020/0629/2020062900844.pdf', '/listedco/listconews/gem/2020/0629/2020062900822.pdf', '/listedco/listconews/gem/2020/0629/2020062900820.pdf', '/listedco/listconews/gem/2020/0629/2020062900814.pdf', '/listedco/listconews/gem/2020/0629/2020062900806.pdf', '/listedco/listconews/gem/2020/0629/2020062900780.pdf', '/listedco/listconews/gem/2020/0629/2020062900746.pdf', '/listedco/listconews/gem/2020/0629/2020062900710.pdf', '/listedco/listconews/gem/2020/0629/2020062900688.pdf', '/listedco/listconews/sehk/2020/0629/2020062900684.pdf', '/listedco/listconews/gem/2020/0629/2020062900678.pdf', '/listedco/listconews/gem/2020/0629/2020062900664.pdf', '/listedco/listconews/gem/2020/0629/2020062900653.pdf', '/listedco/listconews/gem/2020/0629/2020062900609.pdf', '/listedco/listconews/gem/2020/0629/2020062900599.pdf', '/listedco/listconews/gem/2020/0629/2020062900565.pdf', '/listedco/listconews/gem/2020/0629/2020062900549.pdf', '/listedco/listconews/gem/2020/0629/2020062900543.pdf', '/listedco/listconews/gem/2020/0629/2020062900535.pdf', '/listedco/listconews/gem/2020/0629/2020062900523.pdf', '/listedco/listconews/gem/2020/0629/2020062900519.pdf', '/listedco/listconews/gem/2020/0629/2020062900517.pdf', '/listedco/listconews/gem/2020/0629/2020062900509.pdf', '/listedco/listconews/sehk/2020/0629/2020062900483.pdf', '/listedco/listconews/sehk/2020/0629/2020062900451.pdf', '/listedco/listconews/gem/2020/0629/2020062900313.pdf', '/listedco/listconews/gem/2020/0629/2020062900017.pdf']
    d = {link: 1 for link in links}
    problem = 0
    for url, p in d.items():
        url = 'https://www1.hkexnews.hk' + url
        print(url)
        try:
            main(url, p)
        except:
            print('No good')
            problem += 1
            with open('problem_pdf.txt', 'a+') as f:
                # for problem in problems:
                f.write(url)
                f.write('\n')
    print(f'error case: {problem}; error rate: {problem/len(d):.2%}')


def search_audit_report_by_page(url):
    '''
    search independent audit report section by page; secondary option when pdf outline is not available.
    '''
    pdf = get_pdf(url)
    pages = pdf.getNumPages()
    iar, il = r"independent auditor['s]?( report)?", []
    kam, kl = "KEY AUDIT MATTERS", []
    for p in range(pages):
        page = pdf.getPage(p)
        page_txt = re.sub('\n+', '', page.extractText())

        if re.search(iar, page_txt, flags=re.IGNORECASE):
            il.append(p)
            # print(page_txt)

        if re.search(kam, page_txt, flags=re.IGNORECASE):
            kl.append(p)
    print(f'found {iar}: {len(il)} times, in page {il}')
    print(f'found {kam}: {len(kl)} times, in page {kl}')
    print(url)


def get_outline_pages(toc: dict, title_pattern: str) -> list:
    '''
    Return an outline page range in list by searching the outline title pattern.
    '''
    pageRange = [page_range.split(' - ') for outline, page_range in toc.items(
    ) if re.search(title_pattern, outline, flags=re.IGNORECASE)][0]
    return pageRange
# url = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0728/2020072800460.pdf' # outline unavaiable


url = 'https://www1.hkexnews.hk/'
url = url + '/listedco/listconews/sehk/2020/0731/2020073100689.pdf'
pdf = get_pdf(url)

for i in range(10):
    page = pdf.getPage(i)
    page_txt = re.sub('\n+', '', page.extractText())
    print(page_txt)

# search_audit_report_by_page(url)

# toc = get_toc(pdf)
# title_pattern = r"independent auditor['s]?( report)?"
# from_page, to_page = get_outline_pages(toc, title_pattern)
# print(from_page, to_page)

# S = ["KEY AUDIT MATTERS", "KEY AUDIT MATTER"]
# pattern = r'KEY AUDIT MATTER[S]?'
# S = ["independent auditors aa', independent auditor's report, independent auditor report"]
# pattern = r"independent auditor['s]?( report)?"
# print([i for i in S if re.search(pattern, i, flags=re.I)])
