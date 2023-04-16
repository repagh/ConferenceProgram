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
from programmail import WriteEmail
import argparse
import os
import sys
import getpass, smtplib, ssl, mailbox, imaplib
import time

# find the current file's folder, for finding templates and the like
base = os.path.dirname(__file__)

parser = argparse.ArgumentParser(
    description="""Compose a conference program""")
parser.add_argument(
    '--verbose', action='store_true',
    help="Verbose run with information output")
parser.add_argument(
    '--title', type=str, default='',
    help="Title to print on html/pdf program")

parser.add_argument(
    '--program', type=str, required=True,
    help=r'''Excel sheet with program. Needs the following tabs

    - items    Paper presentation, panel participation, etc. The first row
               identifies the contents, and needs the following:
               * item     Identifying key
               * session  Session to which the item is assigned
               * title    Title of the item/contribution
               * author_list List of authors, separated by "," or newline
               * abstract Abstract, or statement/description

    - sessions Parts of the conference. First row identifies the contents
               * session  ID for the session (matches items/events tables)
               * title    Title of the session
               * shorttitle Short version of the title
               * event    Event slot where the session is scheduled
                          (matches events table)
               * format   Format strings for the session. If "PAR" is in
                          the format, a specific parallel session layout will
                          be generated. The format strings can be used to
                          select css classes.

    - events   Time schedule of the conference. First row identifies the
               contents.
               * day      Date of the event (date field)
               * start    Start time of the event
               * end      End time of the event
               * title    Title of the session (to be used if not attached to
                          a session)
               * venue    Location where the event is held
               * event    Event id (used in sessions table)
               * format   Format strings for the event

    - authors  List of author names, with additional details, e.g.,
               biography, picture, email, title, affiliation, orcid
    ''')

subparsers = parser.add_subparsers(help='commands', title='Commands')

class ProgramPdf:

    command = 'pdf'

    @classmethod
    def args(cls, subparsers):
        parser = subparsers.add_parser(
            cls.command,
            help="Create a PDF file output")
        parser.add_argument(
            "--outfile", type=argparse.FileType('w'), required=True,
            help='Output file event list')
        parser.add_argument(
            "--authorout", type=argparse.FileType('w'),
            help='Output file author list')
        parser.add_argument(
            "--css", type=argparse.FileType('r'),
            help='Style file')
        parser.add_argument(
            "--author-template", type=argparse.FileType('r'),
            help='Jinja2 template to generate the author list')
        parser.add_argument(
            "--event-template", type=argparse.FileType('r'),
            help='Jinja2 template to generate the conference program')
        parser.set_defaults(handler=cls)

    def __call__(self, ns):

        # process the program spec
        program = Program(ns.program, ns.title)

        # figure out template arguments
        if ns.author_template is None:
            author_template = "authorlist.html"
        else:
            author_template = ns.author_template

        if ns.event_template is None:
            event_template = "eventlist.html"
        else:
            event_template = ns.event_template

        try:
            css = ns.css.name
        except AttributeError:
            css = f"{base}/templates/printstyles.css"

        # create a writer
        writer = WritePDF(program)

        # write the events
        outfile = ns.outfile.name
        writer.eventList(outfile, template=event_template, css=css)

        # write the author list
        try:
            outfile = ns.authorout.name
            writer.authorList(outfile, template=author_template, css=css)
        except AttributeError:
            pass
ProgramPdf.args(subparsers)


class ProgramHtml:

    command = 'html'

    @classmethod
    def args(cls, subparsers):
        parser = subparsers.add_parser(
            cls.command,
            help="Create HTML file output")
        parser.add_argument(
            "--outfile", type=argparse.FileType('w'), required=True,
            help='Output file event list')
        parser.add_argument(
            "--authorout", type=argparse.FileType('w'),
            help='Output file author list')
        parser.add_argument(
            "--author-template", type=argparse.FileType('r'),
            help='Jinja2 template to generate the author list')
        parser.add_argument(
            "--event-template", type=argparse.FileType('r'),
            help='Jinja2 template to generate the conference program')
        parser.set_defaults(handler=cls)

    def __call__(self, ns):

        # process the program spec
        program = Program(ns.program, ns.title)

        # figure out template arguments
        if ns.author_template is None:
            author_template = "authorlist.html"
        else:
            author_template = ns.author_template

        if ns.event_template is None:
            event_template = "eventlist.html"
        else:
            event_template = ns.event_template

        # create a writer
        writer = WriteHTML(program)

        # write the events
        ns.outfile.write(writer.eventList(template=event_template))
        ns.outfile.close()

        # write the author list
        try:
            ns.authorout.write(writer.authorList(template=author_template))
            ns.authorout.close()
        except AttributeError:
            pass
ProgramHtml.args(subparsers)

class ProgramDocx:

    command = 'docx'

    @classmethod
    def args(cls, subparsers):
        parser = subparsers.add_parser(
            cls.command,
            help="Create docx file output")
        parser.add_argument(
            "--outfile", type=argparse.FileType('w'), required=True,
            help='Output file event list')
        parser.add_argument(
            "--authorout", type=argparse.FileType('w'),
            help='Output file author list')
        parser.set_defaults(handler=cls)

    def __call__(self, ns):

        # process the program spec
        program = Program(ns.program)

        # create a writer
        writer = WriteDocx(program)

        # write the events
        outfile = ns.outfile.name
        writer.eventList(outfile)

        # write the author list
        try:
            outfile = ns.authorout.name
            writer.authorList(outfile)
        except AttributeError:
            pass
ProgramDocx.args(subparsers)

class ProgramEmail:

    command = 'email'

    @classmethod
    def args(cls, subparsers):
        parser = subparsers.add_parser(
            cls.command,
            help="Send or create e-mails to corresponding authors")
        parser.add_argument(
            "--smtp-server", type=str,
            help="SMTP Email server, for sending the emails")
        parser.add_argument(
            "--imap-server", type=str,
            help="IMAP mail host, for sent-items copies")
        parser.add_argument(
            "--user", type=str,
            help="Username for email server, name for email sender")
        parser.add_argument(
            "--email", type=str, default='no-reply@nowhere.org',
            help="From email for email sender")
        parser.add_argument(
            "--html-template", type=argparse.FileType('r'),
            default="templates/mailtemplate.html",
            help="Template for sending email")
        parser.add_argument(
            "--txt-template", type=argparse.FileType('r'),
            default="templates/mailtemplate.txt",
            help="Template for sending email")
        parser.add_argument(
            "--outfile", type=argparse.FileType('w'),
            help='Mail file for saving all concepts')
        parser.add_argument(
            "--testmail", type=str,
            help="test recipient email")
        parser.set_defaults(handler=cls)

    def __call__(self, ns):

        # process the program spec
        program = Program(ns.program)
        sendemail = ns.email or 'no-reply@isap.org'

        # create a writer
        writer = WriteEmail(program, sendemail, ns.title,
                            ns.html_template, ns.txt_template,
                            ns.testmail)

        # and email connection
        server = None
        imap = None
        pw = None

        if (ns.smtp_server or ns.imap_server) and ns.user:
            pw = getpass.getpass("Password for email servers : ")
            context = ssl.create_default_context()

        if ns.smtp_server and ns.user:
            server = smtplib.SMTP_SSL(ns.smtp_server, 465, context=context)
            server.login(ns.user, pw)

        if ns.imap_server and ns.user:
            imap = imaplib.IMAP4_SSL(ns.imap_server, 993, ssl_context=context)
            imap.login(ns.user, pw)

        # if we have an outfile
        mbox = None
        if ns.outfile:
            mbname = ns.outfile.name
            ns.outfile.close()
            mbox = mailbox.mbox(mbname)

        # if we have an outfile
        for message, recipient in writer.mails():
            print("to", recipient)
            if ns.outfile:
                mkey = mbox.add(message)
                print("added message", mkey)
            if server:
                server.sendmail(ns.email, recipient, message)
            if imap:
                res = imap.append('Sent', r'(\Seen)',
                                  imaplib.Time2Internaldate(time.time()),
                                  message.encode('utf8'))
                if res[0] != 'OK':
                    print("Could not append message to Sent folder", res)

        server and server.quit()
        imap and imap.logout()
        ns.outfile and mbox.close()

ProgramEmail.args(subparsers)

# default arguments
argvdef = (
    '--title="The Nonsense Conference"',
    f'--program={base}/../example/exampledata.xlsx',
    'email',
    '--outfile=Nonsense.mbox',
    '--email=M.M.vanPaassen@TUDelft.nl',
    '--testmail=rene_vanpaassen@yahoo.com'
    )



if __name__ == '__main__':

    if len(sys.argv) > 1:
        pres = parser.parse_args(sys.argv[1:])
    else:
        print("Default example conference")
        pres = parser.parse_args(argvdef)
    try:
        hclass = pres.handler
    except AttributeError:
        parser.print_usage()
        sys.exit(-1)

    # run the handler
    handler = hclass()
    handler(pres)
