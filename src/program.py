#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 10:40:39 2023

@author: repa
"""

import openpyxl
from authorparse import Author, AuthorList
from datetime import date, time, timedelta, datetime
import re

class Item:
    
    _members = ('item', 'title', 'abstract', 'session')
    _required = ('author_list', 'item', 'title', 'session')
    
    def __init__(self, index, row, program):
            
        # check the minimum is there
        for m in Item._required:
            if row[index[m]].value is None or not str(row[index[m]].value).strip():
                raise ValueError(
                    f"No data in cell {row[index[m]].coordinate}, skipping row")
        
        # these are directly coupled, make empty string cells void
        for m in Item._members:
            v = str(row[index[m]].value)
            if v is not None and v.strip() == '': v = None
            setattr(self, m, v)
            
        # this becomes a list, note authors are unique!
        # print(row[index['author_list']].value)
        try:
            self.authors = list(AuthorList(row[index['author_list']].value, 
                                           program))
        except:
            print(f"Cannot get authors from {row[index['author_list']].value}")
            self.authors = [Author(dict(firstname='', lastname='Anonymous'), 
                                   program)]

        # link to the session if available
        try:
            self._session = program.sessions[self.session]
            self._session._items.append(self)
        
        except:
            raise ValueError(f"Item: cannot find session {self.session}")

    def __str__(self):
        return str(self.__dict__)

    def key(self):
        return self.item

class TimeSlot:

    def __new__(cls, event, program):
        try:
            slot = program.slots[event.start]
            slot.start = event.start
            slot.end = max(slot.end, event.end)
            slot.events[event.event] = event
        except KeyError:
            slot = super().__new__(cls)
            slot.events = { event.event : event }
            slot.start = event.start
            slot.end = event.end
            program.slots[event.start] = slot
        return slot
    
    def key(self):
        return self.start


_timeparse = re.compile('([0-9]{1,2}):([0-9]{2})\s?(AM|PM)?')

def makeTime(day, t):
    if isinstance(t, datetime):
        return t
    
    res = _timeparse.match(t)
    h, m = int(res.group(1)), int(res.group(2))
               
    if res.group(3) == 'PM' and h != 12:
        h = h + 12
    elif res.group(3) == 'AM' and h == 12:
        h = 0
    elif res.group(3) not in ('AM', 'PM', 'am', 'pm', None):
        raise ValueError("Indicate AM, PM or nothing")
    
    return datetime.combine(day, time(h, m))

        
class Event:
    
    _members = ('day', 'start', 'end', 'title', 'venue', 'event')
    
    def __init__(self, index, row, program):
        
        # directly coupled/read
        for m in Event._members:
            setattr(self, m, row[index[m]].value)
        
        # fix the start if needed
        try:
            self.start = makeTime(self.day, self.start)
            self.end = makeTime(self.day, self.start)
        except Exception as e:
            rs, re = row[index['start']].coordinate, row[index['end']].coordinate
            raise ValueError(f"Cannot convert event times in {rs} and/or {re}: {e}")
        
        # claim/insert the time slot
        TimeSlot(self, program)
        
    def __str__(self):
        return str(self.__dict__)

    def key(self):
        return self.event

class Session:
    
    _members = ('session', 'title', 'items', 'event', 'format')
    
    def __init__(self, index, row, program):
        for m in Session._members:
            setattr(self, m, row[index[m]].value)
            
        # find the corresponding event
        try:
            event = program.events[self.event]
            self._event = event
            event._session = self
        except KeyError:
            raise KeyError(f"Cannot find event {self.event} for session {self.session}"
                           f", check {row[index['event']].coordinate}")
        self._items = []
            
    def __str__(self):
        return str(self.__dict__)

    def key(self):
        return self.session

def processSheet(sheet, Object, program=None):
    
    # result
    collect = dict()
    
    # read the index from the first row
    index = dict([(c[0].value, c[0].column-1) for 
                 c in sheet.iter_cols(max_row=1)])

    # process the remaining rows
    for row in sheet.iter_rows(min_row=2):
        try:
            o = Object(index, row, program)
            collect[o.key()] = o
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
        self.book = book
        
        # prepare for filling        
        self.authors = dict()
        self.slots = dict()
      
        # events dict is returned by the call, sorted by event id
        # this also fills the slots, keyed by slot start time
        self.events = processSheet(book['events'], Event, self)

        # the sessions dict is returned by the processSheet call
        # a session is linked to an event, and thereby to a time slot
        self.sessions = processSheet(book['sessions'], Session, self)
        
        # the items are linked to a session; they will be added to 
        # the list of items there
        self.items = processSheet(book['items'], Item, self)     

        # read the full definitions from the authors tab for authors with
        # further details
        #
        # this may also further fill the authors dict
        processSheet(book['authors'], Author, self)

    
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
    kl = sorted(pr.authors.keys(), key=lambda s: s[0].casefold())
    for ak in kl:
        print(ak)
    