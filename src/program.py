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
            
        # an item may be presented in multiple sessions, for example the
        # best student paper candidates
        self.session = self.session.split(',')
            
        # link to the session if available
        coord = row[index['session']].coordinate
        self._session = []
        try:
            self._session = [ program.sessions[s] for s in self.session]
        except:
            raise ValueError(f"Item: check items.{coord}, cannot find session {self.session}")
        for s in self._session:
            s._items.append(self)

        # find, if needed create the authors.
        try:
            self.authors = list(AuthorList(row[index['author_list']].value, 
                                           program))
        except:
            print(f"Cannot get authors from {row[index['author_list']].value}")
            self.authors = [Author(dict(firstname='', lastname='Anonymous'), 
                                   program)]

        # session link is ok, now add the authors
        for a in self.authors:
            a._items.append(self)
            
    def __str__(self):
        return str(self.__dict__)

    def key(self):
        return self.item
    
    def getEvents(self):
        """ Return the associated events ID's, if present
        """
        return [ s._event.event for s in self._session ]
        
    def printAuthors(self):
        res = []
        for a in self.authors:
            res.append(f"{a.firstname} {a.lastname}")
        return ', '.join(res)
        
def daysort(e):
    _dayvalue = dict(wed=300,thu=400,fri=500,sat=600)
    try:
        ses = e.event
        return _dayvalue[ses[:3]] + 10*int(ses[4]) + \
            ((len(ses) == 6) and (ord(ses[5])-ord('a')) or 0)
    except:
        return 0

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
    
    def getEvents(self):
        return sorted([ e for k, e in self.events.items() ], key=daysort)


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
        self._slot = TimeSlot(self, program)
        
    def __str__(self):
        return str(self.__dict__)

    def key(self):
        return self.event
    
    def getEventClass(self):
        try:
            return self._session.format
        except AttributeError:
            return ''

    def printDay(self):
        return self.day.strftime("%a")
    
    def printStart(self):
        return self.start.strftime("%H:%M")
    
    def printEnd(self):
        return self.end.strftime("%H:%M")
    
    def hasSession(self):
        return hasattr(self, '_session')
    
    def printShortName(self):
        try:
            return self._session.shorttitle
        except AttributeError:
            return ''
    
    def printEventCode(self):
        return self.event or ''

    def precedingSiblings(self):
        res = []
        for i, ev in enumerate(self._slot.getEvents()):
            if ev == self:
                print(f"for {self.event}, list of pre {res}")
                return res
            res.append(dict(shortname=ev.printShortName(), 
                            sibling_class=f"sibling{i}"))
    
    def succeedingSiblings(self):
        for i, ev in enumerate(self._slot.getEvents()):
            if ev == self:
                res = []
            elif 'res' in locals():
                res.append(dict(shortname=ev.printShortName(), 
                                sibling_class=f"sibling{i}"))
        return res
    
    def printSiblingClass(self):
        return f"sibling{self._slot.getEvents().index(self)}"
    
    def printChair(self):
        try:
            return f"Chair: {self._session.chair}"
        except AttributeError:
            return ''
        
    def printTitle(self):
        try:
            return self._session.title
        except AttributeError:
            return self.title

class Session:
    
    _members = ('session', 'title', 'shorttitle', 'items', 'event', 
                'format', 'chair')
    
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

        self.author_list = [
            au[1] for au in sorted(self.authors.items(), 
                                   key=lambda s: s[0][0].casefold()) ]

    def getEvents(self):
        res = []
        for k, slot in sorted(self.slots.items()):
            res.extend(slot.getEvents())
        return res
            
    
    
if __name__ == '__main__':
    
    pr = Program('../../../TUDelft/community/ISAP2023/collated_abstracts.xlsx')
    kl = sorted(pr.authors.keys(), key=lambda s: s[0].casefold())
    for ak in kl:
        print(ak, pr.authors[ak]._items)
    for ak in pr.author_list:
        print (ak.nameLastFirst())
        
    print(pr.getEvents())