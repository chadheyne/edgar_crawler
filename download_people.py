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

BASE_URL = "http://www.sec.gov/cgi-bin/own-disp?action=getissuer&CIK="
OWNER_URL = "http://www.sec.gov/cgi-bin/own-disp?action=getowner&CIK="
COMP_URL = "http://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK="
COLUMNS = ["Owner", "Filings", "Transaction Date", "Type of Owner", 'owner_link', 'filings_link', 'Company', 'Company_CIK']


def download_meta(cik, company):
    owners = []

    edgar_site = BASE_URL + company['CIK']
    site_request = requests.get(edgar_site)
    soup = BeautifulSoup(site_request.text)

    tables = soup.find_all('table')
    table_wanted = tables[6]

    headers = table_wanted.find('tr')
    cols = [c.text for c in headers.find_all('td')]

    if cols != COLUMNS[:4]:
        print(company['CIK'] + ' invalid table')
        return owners

    people = headers.findNextSiblings()
    for owner in people:
        row_text = [col.text for col in owner.find_all('td')]
        owner_data = dict(zip(COLUMNS, row_text))
        owner_data['owner_link'] = OWNER_URL + owner_data['Filings']
        owner_data['filings_link'] = COMP_URL + owner_data['Filings']
        owner_data['Company'] = company['company']
        owner_data['Company_CIK'] = company['CIK']
        owners.append(owner_data)

    return owners


def load_companies():
    comps = open(os.path.join(prefix, 'awards.csv'), encoding='utf-8', newline='')
    comps_csv = csv.DictReader(comps)
    companies = [dict(r) for r in comps_csv]

    if not os.path.exists(os.path.join(prefix, 'list_of_owners')):
        os.mkdir(os.path.join(prefix, 'list_of_owners'))

    return companies


def save_company(company, owners):
    f = open(os.path.join(prefix, 'list_of_owners', company["CIK"]+".csv"), "w", encoding="utf-8", newline='')
    f_csv = csv.DictWriter(f, COLUMNS)
    f_csv.writeheader()
    f_csv.writerows(owners)


def extract_ceos():
    ceo_list = open(os.path.join(prefix, 'ceos.csv'), 'w', encoding='utf-8', newline='')
    ceo_csv = csv.DictWriter(ceo_list, COLUMNS)
    ceo_csv.writeheader()

    for edgar_file in glob.glob(os.path.join(prefix, 'list_of_owners', '*.csv')):
        with open(edgar_file) as f:
            edgar_csv = csv.DictReader(f)
            for person in edgar_csv:
                if 'ceo' in person['Type of Owner'].lower() or 'chief executive officer' in person['Type of Owner'].lower():
                    ceo_csv.writerow(person)

    ceo_list.close()


def main():
    companies = load_companies()

    meta_set = set()
    meta_set = {comp['CIK']: comp for comp in companies if comp['CIK'] and comp['CIK'] not in meta_set}

    for cik, company in meta_set.items():
        print(cik)
        owners = download_meta(cik, company)

        if len(owners) > 0:
            save_company(company, owners)
    extract_ceos()

if __name__ == "__main__":
    main()
