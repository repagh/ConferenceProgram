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
        it = next(self.ix)
        data = it.getFieldDetails()

        recipient = self.wm.testmail or data['recipient']
        msg = MIMEMultipart('alternative')
        msg['From'] = self.wm.sender
        msg['To'] = recipient
        msg['Cc'] = self.wm.sender
        msg['Subject'] = self.wm.subject
        msg.attach(MIMEText(self.wm.gentxt.render(**data), 'plain'))
        msg.attach(MIMEText(self.wm.genhtml.render(**data), 'html'))
        message = msg.as_string()

        return message, (recipient, )

class WriteEmail:

    def __init__(self, program, sender, subject,
                 tmplhtml='templates/mailtemplate.html',
                 tmpltxt='templates/mailtemplate.txt',
                 testmail=None):

        self.program = program
        self.sender = sender
        self.subject = subject
        self.testmail = testmail
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


