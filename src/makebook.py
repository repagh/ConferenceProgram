#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Feb  9 09:11:47 2023

@author: repa
"""

from program import Program
from programhtml import WriteHTML
from programpdf import WritePDF
from programdocx import WriteDocx
import argparse
import os
from jinja2 import PackageLoader

parser = argparse.ArgumentParser(
    description="""Compose a conference program""")
parser.add_argument(
    '--verbose', action='store_true',
    help="Verbose run with information output")

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

if __name__ == '__main__':

    HOME = os.getenv('HOME')
    print("running from", os.getcwd())
    pr = Program(f'{HOME}/TUDelft/community/ISAP2023/collated_abstracts.xlsx')
    #writer = WriteHTML(pr)
    #print(writer.authorList('authorlist.html'))
    
    writer = WritePDF(pr, tdir=f'templates')
    writer.authorList('../results/authorlist.pdf')
    writer.eventList('../results/eventlist.pdf')


    hwriter = WriteHTML(pr)
    with open('../results/eventlist.html', 'w') as f:
        f.write(hwriter.eventList('eventlist.html'))
    with open('../results/authorlist.html', 'w') as f:
        f.write(hwriter.authorList('authorlist.html'))
   
    dwriter = WriteDocx(pr)
    dwriter.authorList('../results/authorlist.docx')
    dwriter.eventList('../results/eventlist.docx')
      
     