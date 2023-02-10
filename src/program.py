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
    _members = ('orcid', 'affiliation', 'email',
                'picture', 'biography')
    
    def __new__(cls, *argv, **argkw):
        if len(argv) == 1 and hasattr(argv[0], 'keys'):
            return cls._from_dict(argv[0])
        elif len(argv) == 2:
            return cls._from_iterable(argv[0], argv[1])
    
    @classmethod
    def _from_parts(cls, firstname, lastname, orcid=None):
        try:
            return cls._authors[(lastname, firstname, orcid)]
        except KeyError:
            if orcid is None:

                # is there an author def with orcid in there?
                for k, a in cls._authors.items():
                    if k[:2] == (lastname, firstname):
                        print(f"Matching {lastname}, {firstname} to orcid={k[2]}",
                              file=sys.stderr)
                        return a
            else:

                # is the name there, but without orcid? Appropriate
                a = cls._authors.get((lastname, firstname, None), False)
                if a:
                    print(f"Matching orcid={orcid} to {lastname}, {firstname}",
                          file=sys.stderr)
                    del cls._authors[(lastname, firstname, None)]
                    cls._authors[(lastname, firstname, orcid)] = a
                    return a

        # apparently nothing found, create a new author
        obj = super().__new__(cls)
        obj.lastname = lastname
        obj.firstname = firstname
        return obj

    @classmethod    
    def _from_dict(cls, data):
        obj = cls._from_parts(data.get('firstname'), 
                              data.get('lastname', 'Anonymous'),
                              data.get('orcid', None))
        for k, v in data.items():
            if k != '_authors':
                setattr(obj, k, v)
        return obj
        
    @classmethod
    def _from_iterable(cls, index, row):
        obj = cls._from_string(row[index['author']].value)
        
        # these are directly coupled
        for m in cls._members:
            setattr(obj, m, row[index[m]].value)
        
        # remove the un-orcided one, and install with orcid
        del cls._authors[(obj.lastname, obj.firstname, None)]
        cls._authors[(obj.lastname, obj.firstname, obj.orcid)] = obj
        
        
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
    
    _members = ('item', 'title', 'abstract', 'session')

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
        collect.append(Object(index, row))
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