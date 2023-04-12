#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 11 08:49:33 2023

@author: repa
"""
from jinja2 import Environment, PackageLoader, \
    Template

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

environment = Environment(
    loader=PackageLoader("programmail", 'templates')
    )

class MailIter:

    def __init__(self, wm):
        self.wm = wm

    def __iter__(self):
        self.ix = iter(self.wm.items)
        return self

    def __next__(self):
        self.ix = next(self.ix)
        data = self.ix.getFieldDetails()

        msg = MIMEMultiPart('alternative')
        msg['From'] = self.wm.sender
        msg['To'] = self.ix.email
        msg['Subject'] = self.wm.subject
        msg.attach(MIMEText(self.wm.gentxt.render(**data), 'plain'))
        msg.attach(MIMEText(self.wm.genhtml.render(**data), 'html'))
        return msg.as_string(), data.recipient

class WriteEmail:

    def __init__(self, program, sender,
                 tmplhtml='templates/mailtemplate.html', tmpltxt='templates/mailtemplate.txt',
                 subject="A message about your conference participation"):

        self.program = program
        self.sender = sender
        if isinstance(tmpltxt, str):
            self.gentxt = environment.get_template(tmppltxt)
        else:
            self.gentxt = Template(tmpltxt.read())
        if isinstance(tmplhtml, str):
            self.genhtml = environment.get_template(tmplhtml)
        else:
            self.genhtml = Template(tmplhtml.read())

        self.items = program.getAssignedItems()

    def mails(self):
        return MailIter(self)


