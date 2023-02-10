#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 10:40:39 2023

@author: repa
"""

import openpyxl
import re
import sys
from authorparse import Author, AuthorList, SingleAuthor

class Item:
    
    _members = ('item', 'title', 'abstract', 'session')
    _required = ('author_list', 'item', 'title')
    
    def __init__(self, index, row):
            
        # check the minimum is there
        for m in Item._required:
            if row[index[m]].value is None or not str(row[index[m]].value).strip():
                raise ValueError(
                    f"No data in cell {row[index[m]].coordinate}, skipping row")
        
        # these are directly coupled
        for m in Item._members:
            setattr(self, m, row[index[m]].value)
            
        # this becomes a list, note authors are unique!
        print(row[index['author_list']].value)
        try:
            self.authors = list(AuthorList(row[index['author_list']].value))
        except:
            print(f"Cannot get authors from {row[index['author_list']].value}")
            self.authors = [Author(dict(firstname='', lastname='Anonymous'))]

    def __str__(self):
        return str(self.__dict__)

class TimeSlot:
    
    _slots = dict()

    def __new__(cls, event):
        try:
            slot = cls._slots[event.start]
            slot.start = event.start
            slot.end = max(slot.end, event.end)
            slot.events[event.eventid] = event
        except KeyError:
            slot = super().__new__(cls)
            slot.events = { event.event : event }
            slot.start = event.start
            slot.end = event.end
            cls._slots[(event.day, event.start)] = slot
        return slot

class Event:
    
    _members = ('day', 'start', 'end', 'title', 'venue', 'event')
    
    def __init__(self, index, row):
        
        # directly coupled/read
        for m in Event._members:
            setattr(self, m, row[index[m]].value)
            
        # claim/insert the time slot
        TimeSlot(self)
    def __str__(self):
        return str(self.__dict__)

class Session:
    
    _members = ('session', 'title', 'items', 'event', 'format')
    
    def __init__(self, index, row):
        for m in Session._members:
            setattr(self, m, row[index[m]].value)
            
    def __str__(self):
        return str(self.__dict__)

def processSheet(sheet, Object):
    
    # result
    collect = []
    
    # read the index from the first row
    index = dict([(c[0].value, c[0].column-1) for 
                 c in sheet.iter_cols(max_row=1)])

    # process the remaining rows
    for row in sheet.iter_rows(min_row=2):
        try:
            collect.append(Object(index, row))
        except ValueError as e:
            print(f"Creating {Object.__name__}, cannot run row, {e}")
            
    return collect

class Program:
    """ Representation of a conference program.
    
        A conference program can be read from an excel spreadsheet with
        four tabs:
            
            - items: All "items" in the program, a poster presentation, 
              presentation in a parallel or plenary session, panel session 
              participation or the like. The column "item" is the identifying
              key here. Each item links to a session.
            - sessions: A definition of all sessions, each having an 
              identifying key in the column session, each session links to
              an event.
            - events: Events have a time and venue. The column "event" is the 
              identifying key
            - authors: authors are normally assembled from the author_list 
              in the items tab, but additional information can be given here.
              
        The excel spreadsheet is read, processed and linked, so that the
        program can be generated. This can be used to produce:
            
            - A time-ordered program, with all sessions with their contents,
              printed to html, pdf or the like
              
            - A list of events per venue, with a check on overlap
            
            - A list of authors, with id's of the events in which they appear
              and a check on overlap for appearing in parallel sessions
    """
    def __init__(self, file):
        book = openpyxl.load_workbook(file)
        
        # read the sessions
        self.authors = processSheet(book['authors'], Author)
        for a in self.authors:
            print(a)
        
        self.sessions = processSheet(book['sessions'], Session)
        self.events = processSheet(book['events'], Event)
        self.items = processSheet(book['items'], Item)     
    
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
    """
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
    """
    """
    book = openpyxl.load_workbook('../../../TUDelft/community/ISAP2023/collated_abstracts.xlsx')
    
    sessions = book['sessions']
    index = dict( [ (c[0].value, c[0].column) for 
                           c in sessions.iter_cols(min_row=1, max_row=1)] )
    print(index)
    for row in sessions.iter_rows(min_row=2):
        print(row)
    """
    pr = Program('../../../TUDelft/community/ISAP2023/collated_abstracts.xlsx')    