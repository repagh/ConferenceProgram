#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 11 08:49:33 2023

@author: repa
"""


class WriteSheet:

    def __init__(self, project):

        self.pr = project

    def eventList(self, fname):

        book = self.pr.book
        res = [
            ["day", "start", "end", "code", "room", "title",
             "authors/chair"]]
        for day in self.pr.getDays():
            for event in day.events:
                res.append([
                    event.printDay(), event.printStart(), event.printEnd(),
                    event.printEventCode(), event.venue,
                    event.printTitle(), event.printChair()])
                if event.hasSession():
                    for item in event._session._items:
                        res.append([
                            None, None, None, None, None,
                            item.title, item.printAuthors()])
        book.addSheet(fname, res)