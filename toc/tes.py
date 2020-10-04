import pdfplumber
import requests
import pandas as pd
from io import BytesIO

urls = [
    'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0827/2020082700690.pdf',
    'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0721/2020072100713.pdf',
    'https://www1.hkexnews.hk/listedco/listconews/sehk/2020/0721/2020072100653.pdf'
    ]

def job(url):
    with requests.get(url) as response:
        response.raise_for_status()
        byte_obj = BytesIO(response.content)
        pdf = pdfplumber.open(byte_obj)
        problem_pages = []

    for page in pdf.pages:
        try:
            df_char = pd.DataFrame(page.chars)
            if not df_char[df_char.x1 > page.width].empty:
                problem_pages.append(page)
        except AttributeError as e:

            continue

    print(f'{url}: {problem_pages}')

for url in urls:
    job(url)

# en_df_char = df_char[~df_char['text'].str.contains(r'[^\x00-\x7F]+')]
# cn_df_char = df_char[df_char['text'].str.contains(r'[^\x00-\x7F]+')]

# print(en_df_char)
# print(cn_df_char)
