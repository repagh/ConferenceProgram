#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 10:40:39 2023

@author: repa
"""

from authorparse import Author, AuthorList
from datetime import time, datetime
from spreadbook import BookOfSheets
import itertools
import sys
from emailaddress import EmailAddress, parseEmails
import re


class Item:
    """Read from the sheet an item; presentation, poster, contribution
       or similar

    Raises:
        ValueError: Data lacking from the sheet, will skil a row
    """

    _members = ('item', 'title', 'abstract', 'email', 'corresponding',
                'session', 'presenter', 'requested_format')
    _required = ('author_list', 'item', 'title', 'email', 'corresponding',
                 'session')

    def __init__(self, row, data, program):

        # check the minimum is there
        for m in Item._required:
            if data[m] is None or not str(data[m]).strip():
                raise ValueError(
                    f"No data for {m} in row {row}, skipping row")

        # these are directly coupled, make empty string cells void
        for m in Item._members:
            if isinstance(data[m], str) and data[m].strip() == '':
                v = None
            elif data[m] is not None:
                v = str(data[m])
            else:
                v = None
            setattr(self, m, v)

        # an item may be presented in multiple sessions, for example the
        # best student paper candidates
        self.session = self.session.split(',')

        # link to the session if available
        self._session = []
        try:
            self._session = [program.sessions[s] for s in self.session]

        except Exception:
            raise ValueError(
                f"Item: check items row {row}, cannot find session"
                f" {self.session}")

        for s in self._session:
            s._items.append(self)

        # find, if needed create the authors.
        try:
            self.authors = list(AuthorList(data['author_list'], program))
        except Exception:
            print(f"Cannot get authors from author_list in row {row}")
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
        return [s._event.event for s in self._session]

    def printAuthors(self):
        res = []
        for a in self.authors:
            res.append(f"{a.firstname} {a.lastname}")
        return ', '.join(res)

    def getFieldDetails(self):
        return dict(
            recipient=self.email,
            recipientname=self.corresponding,
            title=self.title,
            daysandtimes=' and on '.join(
                [f"{s._event.printDay()} at {s._event.printStart()}"
                 for s in self._session]),
            day=', '.join([s._event.printDayFull() for s in self._session]),
            time=' and on '.join(
                [
                    f"{s._event.printDay()} at {s._event.printStart()}"
                    for s in self._session
                ]),
            session=' and in session'.join([
                f"{s._event.title}: {s._event._session.title}"
                for s in self._session]),
            sessiontitle=', '.join([s._event._session.title
                                    for s in self._session]),
            authors=self.printAuthors(),
            poster=('POSTER' in [s.session for s in self._session]),
            chair=[dict(name=s.chair,
                        email=s.chair_email,
                        session=s._event._session.title)
                   for s in self._session
                   if s.chair and s.chair_email and s._event._session.title],
        )

    def correspondingAuthors(self):
        if self.presenter:
            return [EmailAddress(self.corresponding, self.email),
                    EmailAddress(self.presenter)]
        else:
            return [EmailAddress(self.corresponding, self.email), ]

    def getFormats(self):
        res = set()
        for f in self._session.getFormats():
            res = res or f
        return res


def daysort(e):
    _dayvalue = dict(wed=300, thu=400, fri=500, sat=600)
    try:
        ses = e.event
        return _dayvalue[ses[:3]] + 10*int(ses[4]) + \
            ((len(ses) == 6) and (ord(ses[5])-ord('a')) or 0)
    except Exception:
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
            slot.events = {event.event: event}
            slot.start = event.start
            slot.end = event.end
            program.slots[event.start] = slot
        return slot

    def key(self):
        return self.start

    def getEvents(self):
        return sorted([e for k, e in self.events.items()], key=daysort)


_timeparse = re.compile(r'([0-9]{1,2}):([0-9]{2})\s?(AM|PM)?')


def makeTime(day, t):
    if isinstance(t, time):
        return datetime.combine(day, t)

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

    _members = ('day', 'start', 'end', 'title', 'venue', 'event', 'format')

    def __init__(self, row, data, program):

        # directly coupled/read
        for m in Event._members:
            setattr(self, m, data[m])

        # fix the start if needed
        try:
            self.start = makeTime(self.day, self.start)
            self.end = makeTime(self.day, self.end)
        except Exception as e:
            raise ValueError(f"Cannot convert event times in row {row}: {e}")

        # claim/insert the time slot
        self._slot = TimeSlot(self, program)

    def __str__(self):
        return str(self.__dict__)

    def key(self):
        return self.event

    def getEventClass(self):
        try:
            return f'{self._session.format} {self.format}'
        except AttributeError:
            return f'{self.format}'

    def printDay(self):
        return self.day.strftime("%a")

    def printDayFull(self):
        return self.day.strftime("%A, %B %e")

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
                # print(f"for {self.event}, list of pre {res}")
                return res
            res.append(dict(shortname=ev.printShortName(),
                            sibling_class=f"pre_sibling{i}"))

    def succeedingSiblings(self):
        for i, ev in enumerate(self._slot.getEvents()):
            if ev == self:
                res = []
            elif 'res' in locals():
                res.append(dict(shortname=ev.printShortName(),
                                sibling_class=f"post_sibling{i}"))
        return res

    def printSiblingClass(self):
        return f"sibling{self._slot.getEvents().index(self)}"

    def printChair(self):
        try:
            if self._session.chair:
                return f"Chair: {self._session.chair}"
            return ''
        except AttributeError:
            return ''

    def printTitle(self):
        try:
            return self._session.title
        except AttributeError:
            return self.title


class Session:

    _members = ('session', 'title', 'shorttitle', 'items', 'event',
                'format', 'chair', 'chair_email')

    def __init__(self, row, data, program):
        for m in Session._members:
            try:
                setattr(self, m, data[m])
            except KeyError as e:
                print(f"Cannot find key {m} in {data}")
                raise e

        # find the corresponding event
        try:
            event = program.events[self.event]
            self._event = event
            event._session = self
        except KeyError:
            raise KeyError(
                f"Cannot find event {self.event} for session {self.session}"
                f", check event in row {row}")
        self._items = []

    def __str__(self):
        return str(self.__dict__)

    def key(self):
        return self.session

    def allAuthors(self):
        res = set()
        for i in self._items:
            res |= set(i.authors)
        return res

    def chairEmails(self):
        return parseEmails(self.chair, self.chair_email)

    def authorEmails(self):
        res = []
        for it in self._items:
            res.append(EmailAddress(it.corresponding, it.email))
            if it.presenter:
                res.append(EmailAddress(it.presenter))
        return res

    def getFieldDetails(self):
        return dict(
            sessiontitle=self.title,
            chairperson=self.chair,
            chair_email=self.chair_email,
            dayandtime=f"{self._event.printDay()} at"
                       f" {self._event.printStart()}",
            items=[dict(authors=it.printAuthors(),
                        title=it.title,
                        corresponding=it.correspondingAuthors())
                   for it in self._items],
            poster=('POSTER' in self.format),
        )

    def getFormats(self):
        return set(self.format.split())


class Day:

    def __init__(self, day, starter):
        self.date = day
        self.events = [starter]

    def printDate(self, fmt='%A %B %d'):
        return self.date.strftime(fmt)


def processSheet(sheet, Object, program=None):

    # result
    collect = dict()

    # process the remaining rows
    for row, data in sheet.iterrows():
        try:
            o = Object(row, data, program)
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

    def __init__(self, file, title='', accountfile='', check_overlap=True):
        self.title = title

        self.book = BookOfSheets(file, accountfile)

        # prepare for filling
        self.authors = dict()
        self.slots = dict()

        # events dict is returned by the call, sorted by event id
        # this also fills the slots, keyed by slot start time
        self.events = processSheet(self.book.events, Event, self)

        # the sessions dict is returned by the processSheet call
        # a session is linked to an event, and thereby to a time slot
        self.sessions = processSheet(self.book.sessions, Session, self)

        # the items are linked to a session; they will be added to
        # the list of items there
        self.items = processSheet(self.book.items, Item, self)

        # read the full definitions from the authors tab for authors with
        # further details
        #
        # this may also further fill the authors dict
        processSheet(self.book.authors, Author, self)

        # make an organization per day
        self.days = dict()
        for k, sl in self.slots.items():
            day = sl.start.date()
            for ke, ev in sorted(sl.events.items()):
                if day in self.days:
                    self.days[day].events.append(ev)
                else:
                    self.days[day] = Day(day, ev)

        self.author_list = [
            au[1] for au in sorted(self.authors.items(),
                                   key=lambda s: s[0][0].casefold())]

        if check_overlap:
            self.checkAuthorEventOverlap()

    def getEvents(self):
        res = []
        for k, slot in sorted(self.slots.items()):
            res.extend(slot.getEvents())
        return res

    def getDays(self):
        return [d for k, d in sorted(self.days.items())]

    def getAssignedItems(self):
        return [it for k, it in self.items.items() if len(it._session)]

    def checkAuthorEventOverlap(self):
        for k, slot in sorted(self.slots.items()):
            if len(slot.getEvents()) > 1:
                # create sets of authors
                authorsets = [
                    (e.event, e._session.allAuthors())
                    for e in slot.getEvents()]

                for s1, s2 in itertools.combinations(authorsets, 2):
                    common_authors = s1[1].intersection(s2[1])
                    if common_authors:
                        ca = ' and '.join([str(a) for a in common_authors])
                        print(f"Authors for events {s1[0]} and {s2[0]}",
                              f" overlap\n common authors: {ca}",
                              file=sys.stderr)


if __name__ == '__main__':

    pr = Program(
        '../../../TUDelft/community/ISAP2023/'
        'ISAP 2023 shedule data230417b.xlsx')
    kl = sorted(pr.authors.keys(), key=lambda s: s[0].casefold())
    for ak in kl:
        print(ak, pr.authors[ak]._items)
    for ak in pr.author_list:
        print(ak.nameLastFirst())

    print(pr.getEvents())
