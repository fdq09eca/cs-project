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

## Difficulties

**The most difficult part of this project is PDF mining.** The annual report is `.pdf` but it may not be written in format which pose difficulties in the programming process.

- Annual report format is not consistent. Although most are `.pdf`, there are occasionally in other format e.g. `html` (see [SaSa](https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0717/2020071700552.htm))

- Some `.pdf` is scanned document i.e. text search is impossible, see [here](https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0731/2020073100689.pdf)

- Extracted text may not be parsed correctly, which posed difficulties in text searching.

## References

### Email and Scheduling

- [How to Web Scrape in the Cloud (Easy Way)](https://www.youtube.com/watch?v=qquCAgwvL8Q)
- [how to execute a python script every Monday or every day](https://www.youtube.com/watch?v=Gs5jGDROx1M)
- [APS](https://apscheduler.readthedocs.io/en/3.0/userguide.html#code-examples)
- [Introduction to Dash Plotly - Data Visualization in Python](https://www.youtube.com/watch?v=hSPmj7mK6ng)

## Notable

- Query over 1 year is not allowed. hkex API allows single stock for over 1 year query, but not overall.

## Problem of get_auditor()

- sometime it might not extract the txt correctly, e.g. `PricewaterhouseCoopersCerti˜ed`, `KPMGCerti˜ed`, `Deloitte Touche TohmatsuCerti˜ed`
- trim the auditor output
- return just space characters e.g. `audit firm: found on page: 177`
- some company employee two auditors e.g. `audit firm: APPOINTMENT OF EXTERNAL AUDITOR AND INTERNAL CONTROL CONSULTANTOn 24 April 2019, the Board announced that, the Board resolved to appoint Ernst & Young Hua Ming as the auditor of the Company for the year 2019 and resolved to appoint BDO China Shu Lun Pan found on page: 127`
- other, see below

```
audit firm:  On 22 March 2019, the Audit Committee convened an on-site meeting, at which the Audit Committee considered and approved the following resolutions:(1) the resolution on the 2018 Annual Report of the Company and its summary and the H Shares results announcement was considered and approved;(2) the resolution on the 2018 audited financial report of the Company was considered and approved;(3) the resolution on the 2018 Audit Report on the financial report of the Company was considered and approved;(4) the resolution on the 2018 Internal Control Evaluation Report of the Company was considered and approved;(5) the resolution on the 2018 Internal Control Audit Report of the Company was considered and approved;(6) the resolution on the performance of functions by the Audit Committee of the Company for the year 2018 was considered and approved;(7) the resolution on the payment of the audit fee for 2018 financial reports to Shinewing found on page: 141
```

```
audit firm: 8 million was paid/payable to Deloitte  ed  found on page: 91
```

### Strategy

1. Capture error type
   1. create a `.csv` for capture the result. with the following variable
      1. stock number
      2. stock name
      3. auditor result
      4. from_page
      5. to_page
      6. link
      7. page_text.
2. use fuzzy string match to boost the accuracy
3. use Logistic regression or NLP to learn..
