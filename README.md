# Chong Sing project

This project is requested by [Chong Sing Holding FinTech Group Limited](http://www.csfgroup.com/).

## Aims

The final product is to record the annual report data and store the fetched data to a database, ideally automate the task. 
Data in interested: 
- audit firm, KAMs, representation currency, currency unit, and others...

## Introduction
The project is built with the OOP paradiam.
- the BaseClass is `pdf.py` which handles:
  - searching outline
  - spliting columns
    - assumption there are only left and right columns
  - croping section
    - more work need to do to complete this function, (should also make use of `df_bold_text`)
- with the BaseClass development, the `audit_report` is able to produce the following data
  - the auditor name
    - direct searched auditor
  - the KAM
    - kam sentence is not nesscarily cleaned.
    - kam keywords
- the `annual_report` is using the composition of the lower level classes such as `IndependentAuditReport`, and `CorporateGovReport`.

## Structure
the workflow is the following:
1. obtain data from HKEX website by using HKEX endpoint.
   1. HKEX endpoint will also provide other revelent data e.g.`upload date` , `stock code`, `news id`
2. read data by `PDF` class
3. produce report or page in interest with other composition class using as `IndependentAuditReport`, and `CorporateGovReport`.
4. all composition classes will be included in the final `AnnualReport` class.
   1. e.g.: `AnnualReport.audit_reports`, `AnnualReport.corp_gov_reports` 
5. load it to `DataBase`
   1. DataBase should have the following tables and variables:
      1. AnnualReport (main_table)
         1. `news_id`
         2. `stock_code`
         3. `company_name`
         4. `upload_date`
         5. `file_link`
      2. Auditor: fk: `news_id` m:1 relation
         1. auditors m:1 relation
      3. KAM, fk: `news_id`,  m:1 relation 
         1. kam_sentences m:1 relation
         2. kam_tags m:1 relation
      4. AuditFee, fk: `new_id`, 1:1 relation 
         1. currency_code (3digit) 1:1 relation
         2. unit 1:1 relation
         3. total_fee 1:1 relation

### PDF, Page, Sections, Bilingual Page
They are the baseclass for the annual report
- `Page` is the BaseClass for `Sections`, `BilingualPage`
- `Page` will automatically 'remove noise' when it is generated i.e. trim of the non-main-text area e.g. decarative edge text or non-textual-area
- 

#### Caveat

- `Page.remove_noise()` is a bit buggy, due to the nature of various `.pdf`, some file have the `df_char.x1 > page.width` problem, i.e. when `Page.remove_noise()` is called and the page has a abnormal `x1`, error occurs. I suppress this error in the `remove_noise` method, see below, it is the best I have got so far, it avoids the page.width problem, see below.

```python
def remove_noise(self) -> None:
    bbox_main_text = self.bbox_main_text
    if bbox_main_text is None: return None
    try:
        page = self.page.crop(bbox_main_text, relative=False)
    except Exception as e:
        print(e)
        x0, top, x1, bottom = bbox_main_text
        bbox_main_text = x0, top, self.page.width, bottom
        page = self.page.crop(bbox_main_text, relative=False)
    self.page = page
```
- I have made diffferent attempts in a bid to suppress this error, including `df_charx1 < page.width`; or suppressing it in the `bbox_main_text` property. But all theseattempts fall short, and have a notable side effect:
  - It reduces the `Page.page.width` when the `remove_noise` method is called.
  - It is frequently seens in handling bilingual and bi-columns page.


#### Development
- `Page.get_section` method currently only consider `Page.df_section_text`
  - should also consider `Page.df_bold_text` when result is not found
  - [ ] add `next_top` to `Page.df_bold_text` as if `Page.df_section_text`

### HKEX_API
The class is for obtaining data from HKEX endpoint.

#### Caveat 
- maximum obtain one year data for all stock code
- over one year query must include stock code

#### Development
- Completed

### IndependentAuditReport
- The class is composited by `Auditor` and `KeyAuditMatter`.
- It is for the auditor and key audit matter in the auditor report

#### Caveat
- `KeyAuditMatter` is using a list of keywords to extract the key audit matter sentences.
- KeyAuditMatter is not `Discliamer of Opinion`, which is another frequent title in Independent auditor report.

#### Development
- [ ] load `kam_keywords` to DataBase for future ease of update.
- [ ] load `validate_auditor` to DataBase for unifying the frequent auditor.
- [ ] `KeyAuditMatter` currently only search for the featureed text.

### CorporateGovReport
- This class is composited by `AuditFee` and `AuditFeeTable`
- It is for the `audit_fee`, and `currency`, and `currency_unit` 

#### Caveat
- This class is under development.
- Not every Audit remuneration is in the form of table, some maybe in text.
  - Having said that, using `pandas` is a good strategy, since there is `Series.str.extract`
- Sometime parsed table's number are separated, sticked with the items description text and no with the currency columns.
  - **Critical**. the number must not be wrong!
  - see the following for example:
    - https://www1.hkexnews.hk/listedco/listconews/gem/2020/0929/2020092901098.pdf
    - https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0929/2020092900604.pdf

#### Development
This class development is challenging and could not be done in a short time. However, the `currency` and there `unit` is relatively easy.
- [ ] get the `currency` and `unit` first
- [ ] find a way to reassemble the number which may potentially fall into the text columns.

### DataBase
The class is built for storing the data

#### Caveat
- The choice of DataBase is not yet confirmed, but likely be Heroku i.e. postgradSQL
- The local option maybe SQLite

#### Development
- [ ] locally gen a SQLite DataBase for Testing

### Worker
The class will be built for automating the work.

#### Caveat
- it is not confirmed that use be on heroku or locally done
- heroku option may need more time for documentation reading

#### Development
- [ ] try to do it locally first
