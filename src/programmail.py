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
        """Produce an email iterator

        This 

        Arguments:
            wm -- _description_
        """
        self.wm = wm

    def __iter__(self, sendlist):
        self.ix = iter(sendlist)
        return self

    def __next__(self):
        it = next(self.ix)
        data = it.getFieldDetails()

        recipientlist = self.wm.testmail or data['recipient']
        recipients = (self.wm.testmail,) or data['recipients']
        msg = MIMEMultipart('alternative')
        msg['From'] = self.wm.sender
        msg['To'] = recipientlist
        msg['Cc'] = self.wm.sender
        msg['Subject'] = self.wm.subject
        msg.attach(MIMEText(self.wm.gentxt.render(**data), 'plain'))
        msg.attach(MIMEText(self.wm.genhtml.render(**data), 'html'))
        message = msg.as_string()

        return message, recipients

class WriteEmail:

    def __init__(self, program, sender, subject,
                 tmplhtml='templates/mailtemplate.html',
                 tmpltxt='templates/mailtemplate.txt',
                 testmail=None):
        """Email writer class

        Args:
            program (Program): Program data
            sender (str): e-mail address of sender
            subject (str): Topic line
            tmplhtml (str|file, optional): template for the html-formatted message. 
                                           Defaults to 'templates/mailtemplate.html'.
            tmpltxt (str|file, optional): template for the txt-formatted part of the message. Defaults to 'templates/mailtemplate.txt'.
            testmail (None|str, optional): destination e-mail address for test mails. Defaults to None.
        """

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

    def mails(self, target: str):
        """Generate an interator for all mails to send

        Arguments:
            target -- Type of recipients, corresponding authors, session chairs 
            or a combination, with groups of session chair and authors as
            recipients

        Returns:
            MailIter iterator
        """
        if target == 'corresponding':
            sendlist = [
                (item, item.correspondingEmail())
                 for item in self.program.items
            ]
        elif target == 'chairs':
            sendlist = [
                (session, session.chairEmail())
                 for session in self.program.sessions.values()
                 if session.chairEmail()
            ]
        elif target == 'chairgroup':
            print(self.program)
            print(self.program.sessions)
            sendlist = [
                (session, session.authorEmails()+[session.chairEmail()])
                 for session in self.program.sessions.values()
            ]
        else:
            raise ValueError(f'Cannot send mails to group {target}')

        return MailIter(self, sendlist)


