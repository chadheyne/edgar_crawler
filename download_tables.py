#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
import csv
import os
import platform
import glob

__author__ = "Chad Heyne"
__email__ = "chadheyne@smeal.psu.edu"

if "Linux" in platform.system():
    prefix = "/home/chad/Code/Repos/Python/edgar_crawler/"
else:
    prefix = r"C:/Users/czh156/Repos/Python/edgar_crawler/"

BASE_URL = "http://www.sec.gov/cgi-bin/own-disp?action=getowner&CIK={}&type=&dateb=&owner=include&start={}"
DL_COLUMNS = ['A/D', 'Date', 'Issuer', 'Form', 'Trans.', 'Modes', 'Shares', 'Price', 'Owned', 'No.', 'Issuer CIK', 'Security Name', 'Deemed']
EX_COLUMNS = ['Owner', 'CIK', 'Transaction Date', 'Type of Owner', 'owner_link', 'filings_link', 'Company']

WR_COLUMNS = ['A/D', 'Date', 'Owner', 'CIK', 'Company', 'Issuer', 'Form', 'Trans.', 'Modes', 'Shares', 'Price', 'Owned', 'No.', 'Issuer CIK', 'Security Name', 'Deemed']


def download_person(person):
    filings = []
    keep_going = True
    start = 0

    while keep_going:
        page_data = load_page(person['CIK'], start)

        if 'Invalid parameter' in page_data.text:
            keep_going = False
            return filings

        soup = BeautifulSoup(page_data.text)

        tables = soup.find_all('table')
        table_wanted = [t for t in tables if t.find('th')][0]
        rows = table_wanted.find_all('tr')
        if len(rows) < 5:
            keep_going = False
            return filings

        for row in rows:
            col_text = [col.text for col in row.find_all('td')]

            if row.find('th') or 'bgcolor' not in row.attrs:  # Skip header rows and the first dummy row
                continue
            if 'bgcolor' in row.attrs and row.attrs['bgcolor'] != '#FFFFFF':  # Skip rows that have non-white bg (Non awards)
                continue

            filing_data = dict(zip(DL_COLUMNS, col_text))

            if filing_data['Issuer CIK'] != person['Company_CIK']:
                continue

            filing_data['Owner'] = person['Owner']
            filing_data['CIK'] = person['CIK']
            filing_data['Company'] = person['Company']

            filings.append(filing_data)
        start += 80

    return filings


def load_page(cik, start):
    return requests.get(BASE_URL.format(cik, start))


def load_people():
    people = open(os.path.join(prefix, 'ceos.csv'), encoding='utf-8', newline='')
    ceos_csv = csv.DictReader(people)
    ceos = [dict(r) for r in ceos_csv]

    if not os.path.exists(os.path.join(prefix, 'list_of_purchases')):
        os.mkdir(os.path.join(prefix, 'list_of_purchases'))

    return ceos


def save_person(person, filings):
    f = open(os.path.join(prefix, 'list_of_purchases', person['CIK']+'_'+person['Company_CIK']+".csv"), "w", encoding="utf-8", newline='')
    f_csv = csv.DictWriter(f, WR_COLUMNS, quoting=csv.QUOTE_ALL)
    f_csv.writeheader()
    f_csv.writerows(filings)

    f.close()


def main():

    ceos = load_people()

    for ceo in ceos:
        print(ceo['Owner'])
        filings = download_person(ceo)

        save_person(ceo, filings)

if __name__ == '__main__':
    main()
