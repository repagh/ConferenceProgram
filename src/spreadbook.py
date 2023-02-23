#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb 23 09:10:46 2023

@author: repa
"""

import gspread
import pandas as pd
import numpy as np
import os

class BookOfSheets:

    def __init__(self, url, accountfile=''):

        if accountfile:

            # assume google sheets; not tested yet
            gc = gspread.service_account(filename=accountfile)
            book = gc.open_by_url(url)

            for s in ('items', 'sessions', 'event', 'authors'):
                ws = book.worksheet(s)
                setattr(self, s, pd.DataFrame(ws.get_all_records()))

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


if __name__ == '__main__':

    base = os.path.dirname(__file__)
    b1 = BookOfSheets(f'{base}/../example/exampledata.xlsx')
    sheet_id = '1bfvtA3tBdtqd_M8TpKA1pY_vuov1SiMdtywJ8G20lw0'
    b2 = BookOfSheets(f'https://docs.google.com/spreadsheets/d/{sheet_id}/edit?usp=sharing')