# Chong Sing Web scraping project

This project is requested by [Chong Sing Holding FinTech Group Limited](http://www.csfgroup.com/).

## Aims

> The final product should be a database or a `.csv` which reflect the overall KAMs occurrence and update daily.

1. Get the listed companies' annual report from [hkexnews](https://www.hkexnews.hk/) daily
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

## Pseudocode

- [ ] Connect to Heroku database
- [ ] schedule the script (optional? heroku has this simple scheduler)

### get_data()

- [ ] get data from hkex
- [ ] get the annual report `pdf`

### get_audit_firm()

- [ ] if outline available
  - [ ] get the outline title and page range (from page, to page)
- [ ] else:
  - [ ] for each page
    - [ ] append page number to a list if searched `independent auditor report` on that page
- [ ] get the page range (from-to) of `independent auditor report`
- [ ] get the last page of the auditor report
- [ ] get audit firm_name
- [ ] save the `pdf` to respective audit firm folder

### get_kam_occurrence()

get selected kam

- [ ] create dictionary: `{kam : 0 for kam in KAMs}`
- [ ] for page in auditor_report:
  - [ ] for kam in KAMs:
    - [ ] if fuzzy string match selected kam:
      - [ ] dictionary['kam'] += 1

### add_to_db()

- [ ] data to db

- data should have
  - date
  - stock number
  - stock name
  - auditor firm name
  - **each** KAM occurrences

- [ ] insert data to heroku database

### email_notify()

- [ ] write the web-scraping result to a `.csv`
- [ ] write the caution data to another `.csv`
  - [ ] include link for further investigation
- [ ] attach `.csv` and email to the related ppl

## Some Thoughts

- Using [Heroku](https://dashboard.heroku.com/) for the scheduling and database (PostgradSQL)
- Use [Pypdf2](https://pythonhosted.org/PyPDF2/) for the pdf mining and string extraction.
- There are another choices e.g. [pdfminer](https://github.com/euske/pdfminer/) but that would be too complicated and hard for maintenance since the authors has stop the support of the module.

## Problems

The most difficult part of this project is PDF mining. The annual report is  `.pdf` but it may not be written in format which pose difficulties in the programming process.

- Annual report format is not consistent. Although most are `.pdf`, there are occasionally in other format e.g. `html` (see [SaSa](https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0717/2020071700552.htm))

- Some `.pdf` is scanned document, which posed difficulties in text searching. see [here](https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0731/2020073100689.pdf)

- Some `.pdf` outlines is not functional i.e. no reaction after clicking, thus, use the brute force keywords page search..

## References

### Email and Scheduling

- [How to Web Scrape in the Cloud (Easy Way)](https://www.youtube.com/watch?v=qquCAgwvL8Q)
- [how to execute a python script every Monday or every day](https://www.youtube.com/watch?v=Gs5jGDROx1M)
- [APS](https://apscheduler.readthedocs.io/en/3.0/userguide.html#code-examples)

## Notable

- Query over 1 year is not allowed. hkex API allows single stock for over 1 year query not overall.