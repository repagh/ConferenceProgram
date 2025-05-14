#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gspread
import pandas as pd
import numpy as np
import os
import sys

"""
Created on Thu Feb 23 09:10:46 2023

@author: repa
"""

"""
For opening a spreadsheet with gspread google API:
https://codesolid.com/google-sheets-in-python-and-pandas/
"""


class BookOfSheets:

    def __init__(self, url, accountfile=''):

        if accountfile:

            # assume google sheets; not tested yet
            gc = gspread.service_account(filename=accountfile)
            try:
                self.book = gc.open(url)
            except gspread.SpreadsheetNotFound:
                print(f"Could not open as sheet: {url}")
                self.book = gc.open_by_url(url)

            for s in ('items', 'sessions', 'events', 'authors'):
                ws = self.book.worksheet(s)
                setattr(self, s, pd.DataFrame(ws.get_all_records()))
            self.events['day'] = pd.to_datetime(self.events['day'],
                                                dayfirst=True)

        elif not os.path.exists(url):

            # try read access without credentials
            if not url.startswith('https://'):
                url = f'https://docs.google.com/spreadsheets/d/{url}'
            elif '/edit?' in url:
                url = ''.join(url.split('/edit?')[:-1])

            for s in ('items', 'sessions', 'authors', 'events'):
                setattr(self, s, pd.read_csv(
                    f'{url}/gviz/tq?tqx=out:csv&sheet={s}').
                    replace(np.nan, None))
            self.events['day'] = pd.to_datetime(self.events['day'],
                                                dayfirst=True)

        else:

            # assume local excel spreadsheet
            for s in ('items', 'sessions', 'events', 'authors'):
                setattr(self, s, pd.read_excel(
                    url, sheet_name=s).
                    replace(np.nan, None))

    def addSheet(self, name: str, data):

        if getattr(self, 'book', None) is None:
            print("Works for now only with gspread account", file=sys.stderr)
            return
        rows = len(data)
        cols = len(data[0])
        if name in [sh.title for sh in self.book.worksheets()]:
            print(f"A sheet named {name} already exists, not overwriting",
                  file=sys.stderr)
        ws = self.book.add_worksheet(title=name, rows=rows, cols=cols)
        c2 = chr(ord('A') + cols - 1)
        r2 = rows
        ws.update(f"A1:{c2}{r2}", data)


if __name__ == '__main__':

    base = os.path.dirname(__file__)
    b1 = BookOfSheets(f'{base}/../example/exampledata.xlsx')
