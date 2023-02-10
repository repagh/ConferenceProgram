#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 10:40:39 2023

@author: repa
"""

import openpyxl
import re
import sys


def getTitle(raw):
    for t in ('Dr', 'Dr.', 'Mr', 'Mr.', 'Prof', 'Prof.', 'Lt Col'):
        if raw.startswith(t+' '):
            return t, raw[len(t):]
    return '', raw

class Author:
    
    _decode = re.compile(
        r'(?:(?:"([^"]+)")|(\S+))\s+([^(]+?)\s*(?:\((\d{4}-\d{4}-\d{4}-\d{4})\))?')
    _authors = dict()
    
    def __new__(cls, raw_name: str):
        
        title, raw_name = getTitle(raw_name)
                
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
            return cls._authors[(lastname, firstname, orcid)]
        except KeyError:
            pass
        obj = super().__new__(cls)
        obj.lastname = lastname
        obj.fistname = firstname
        obj.title = title
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
        
    def complete(self, sheet):
        pass

class Item:
    
    _members = ('key', 'title', 'abstract', 'session')

    def __init__(self, index, row):
            
        # these are directly coupled
        for m in Item._members:
            setattr(self, m, row[index[m]].value)
            
        # this becomes a list, note authors are unique!
        print(row[index['author_list']].value)
        try:
            self.authors = [
                Author(a) for a in row[index['author_list']].value.split(',')]
        except:
            print(f"Cannot get authors from {row[index['author_list']].value}")
            self.authors = [Author('Anonymous')]

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
            slot.events = { event.eventid : event }
            slot.start = event.start
            slot.end = event.end
            cls._slots[(event.day, event.start)] = slot
        return slot

class Event:
    
    _members = ('day', 'start', 'end', 'title', 'venue', 'eventid')
    
    def __init__(self, index, row):
        
        # directly coupled/read
        for m in Event._members:
            setattr(self, m, row[index[m]].value)
            
        # claim/insert the time slot
        TimeSlot(self)
    def __str__(self):
        return str(self.__dict__)

class Session:
    
    _members = ('topic', 'title', 'items', 'session', 'format')
    
    def __init__(self, index, row):
        for m in Session._members:
            setattr(self, m, row[index[m]].value)
            
    def __str__(self):
        return str(self.__dict__)


def makeIndex(sheet):
    return dict([(c[0].value, c[0].column-1) for 
                 c in sheet.iter_cols(max_row=1)])

class Program:
    
    def __init__(self, file):
        book = openpyxl.load_workbook(file)
        
        # read the sessions
        sessions = book['sessions']
        index = makeIndex(sessions)
        self.sessions = []
        for row in sessions.iter_rows(min_row=2):
            self.sessions.append(Session(index, row))
            print(self.sessions[-1])
            
        # read the events
        events = book['events']
        index = makeIndex(events)
        for row in events.iter_rows(min_row=2):
            ev = Event(index, row)
            print(ev)
        
        # read the items
        items = book['items']
        self.items = []
        index = makeIndex(items)
        for row in items.iter_rows(min_row=2):
          self.items.append(Item(index, row))
          print(self.items[-1])
      
    
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