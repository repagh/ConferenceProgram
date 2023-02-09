#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 10:40:39 2023

@author: repa
"""

import xlrd
import re
import sys

class Author:
    
    _decode = re.compile(
        r'(?:(?:"([^"]+)")|(\S+))\s+([^(]+?)\s*(?:\((\d{4}-\d{4}-\d{4}-\d{4})\))?')
    _authors = dict()
    
    def __new__(cls, raw_name: str):
        
        res = cls._decode.fullmatch(raw_name.strip())
        if res:
            lastname = res.group(3)
            firstname = res.group(1) or res.group(2)
            orcid = res.group(4)
            
        else:
            print(f"Cannot decode author first/last: {raw_name}")
            firstname = ''
            lastname = raw_name.strip()
            orcid = None
        try:
            return cls._authors((lastname, firstname, orcid))
        except KeyError:
            pass
        obj = super().__new__()
        obj.lastname = lastname
        obj.fistname = firstname
        cls._authors[(lastname, firstname, orcid)] = obj
        return obj
        
    def __str__(self):
        return f'{self.lastname}, {self.firstname}'

    @classmethod
    def find(cls, **kw):
        try:
            return cls._authors((kw['lastname'], kw['firstname'], 
                                 kw.get('orcid', None)))
        except KeyError:
            pass
        try:
            for k, o in cls._authors.items():
                if k[2] == kw['orcid']:
                    return o
        except KeyError:
            raise KeyError("Wrong arguments to find author")
        raise KeyError(f"Cannot find author from {kw}")

class Item:
    
    _members = ('key', 'title', 'abstract')

    def __init__(self, index, row):
            
        # these are directly coupled
        for m in Item._members:
            setattr(self, m, row[index[m]].value)
            
        # this becomes a list, note authors are unique!
        self.authors = [
            Author(a) for a in row[index['authors']].value.split('&')]

class Program:
    
    def __init__(self, file):
        book = xlrd.open_workbook(file)
        
        # find the appropriate sheets
        items = book.sheet_by_name('items')
        sessions = book.sheet_by_name('sessions')
        authors = book.sheet_by_name('authors')
        
        
    
if __name__ == '__main__':
    
    def testem(dec):
        print(f"testing {dec}")
        txt = """John Doe
John Doe (0000-1234-0000-0000)
"John" Doe
"John A." Doe
Jane Burke Cohen
Jane-Jet Cohen
"John A." Doe (0000-1234-0000-0000)"""
        for t in txt.split('\n'):
            try:
                res = dec.fullmatch(t)
                print(res.groups())
            except:
                print(f"Cannot decode {t}")
    
    # captures simple, first name + rest
    dec0 = re.compile(r'(\S+)\s+(.+)')
    testem(dec0)
    
    # captures quoted first name in #2, simple first name in #3, last name #4
    dec1 = re.compile(r'(("([^"]+)")|(\S+))\s+(.+)')
    testem(dec1)
    
    # do not capture orcid opening brackets
    dec2 = re.compile(r'(("([^"]+)")|(\S+))\s+([^(]+)')
    testem(dec2)
    
    # do the optional orcid decode
    dec3 = re.compile(r'(?:(?:"([^"]+)")|(\S+))\s+([^(]+?)\s*(?:\((\d{4}-\d{4}-\d{4}-\d{4})\))?')
    testem(dec3)
    
    pr = Program(open('../../../TUDelft/community/ISAP2023/collated_abstracts.xlsx'))
    
    