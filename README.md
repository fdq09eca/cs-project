# Chong Sing Web scraping project

This project is requested by [Chong Sing Holding FinTech Group Limited](http://www.csfgroup.com/).

## Aims

>The final product should be a database or a `.csv` which reflect the overall KAMs occurrence and update daily.

1. Get the listed companies' annual report uploaded to [hkexnews](https://www.hkexnews.hk/) daily
2. Save the annual report into folders with respect to the firm of independent auditor report, the following firms are in particular interested:
   1. Big4
      1. Deloitte
      2. Ernst & Young
      3. KPMG
      4. PwC
   2. Selected secondary accounting firms
      1. TBC
   3. Others

3. Search in the independent auditor report for the Key Audit Matters (KAMs).
   1. TBC
4. Build a database for recording the listed company and the its mentioned KAMs.
5. Schedule the program to run and update the database daily.
6. Email related people after the completion.

## Some thoughts

1. Using [Heroku](https://dashboard.heroku.com/) for the scheduling and database (PostgradSQL)
2. Use [Pypdf2](https://pythonhosted.org/PyPDF2/) for the pdf mining and string extraction.
   1. There are another choices e.g. [pdfminer](https://github.com/euske/pdfminer/) but that would be too complicated and hard for maintenance since the authors has stop the support of the module.

## Problems

The most difficult part of this project is PDF mining. the annual report is in `pdf` format but it may not be written in format which pose a lot of difficulties in the programming process.

1. Annual report format is not consistent. Although most are `.pdf`, there are occasionally in other format e.g. html (see [SaSa](https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0717/2020071700552.htm))

2. Some `.pdf` is scanned document, which posed difficulties in text searching. see [here](https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0731/2020073100689.pdf)

3. Some `.pdf` outlines (table of content) is not functional: no reaction after clicking.

## Reference video

### Email and Scheduling

- [How to Web Scrape in the Cloud (Easy Way)](https://www.youtube.com/watch?v=qquCAgwvL8Q)
- [how to execute a python script every Monday or every day](https://www.youtube.com/watch?v=Gs5jGDROx1M)
- [APS](https://apscheduler.readthedocs.io/en/3.0/userguide.html#code-examples)