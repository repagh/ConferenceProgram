#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 09:11:47 2023

@author: repa
"""

import argparse
import xlrd


parser = argparse.ArgumentParser(
    '--verbose', action='store_true',
    description="""Compose a conference program""")
parser.add_argument(
    '--program', type=argparse.FileType('r'), required=True, 
    help='''Excel sheet with program. Needs the following tabs
    
    - items    Paper presentation, panel participation, etc. The first row
               identifies the contents, and needs the following:
               * key      Identifying key
               * title    Title of the item/contribution
               * authors  List of authors, separated by , or &, if needed
                 compound first name in quotes (")
               * abstract Abstract, or statement/description
               
    - sessions Schedule of the conference. First row identifies the contents
               * date     Date
               * time     Start time of the slot
               * duration Duration
               * title    Title of the session
               * items    Comma-separated list of items in the session
               * venue    Location where the session is held
               
    - authors  List of author names, with additional details, e.g., 
               biography, picture, email, title, affiliation
    ''')
    
subparsers = parser.add_subparsers(help='commands', title='Commands')



class ProgramPdf:
    
    command = 'pdf'
    
    @classmethod
    def args(cls, subparsers):
        parser = subparsers.add_parser(
            ProgramPdf.command,
            help="Create a PDF file output")
        parser.add_argument(
            "outfile", type=argparse.FileType('w'), required=True,
            help='Output file')

    def __call__(self, ns):
        
        program = Program(ns.program)

                