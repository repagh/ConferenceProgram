#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 11 08:49:33 2023

@author: repa
"""
from emailaddress import addressEmails, EmailAddress
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, PackageLoader, \
    Template

# create an environment for jinja loading
environment = Environment(
    loader=PackageLoader("programmail", 'templates')
)


class MailIter:

    def __init__(self, wm, sendlist):
        """Produce an email iterator

        Arguments:
            wm -- _description_
        """
        self.wm = wm
        self.sendlist = sendlist

    def __iter__(self):
        self.ix = iter(self.sendlist)
        return self

    def __next__(self):
        """Produce next mail message and its recipients

        Returns
        -------
        tuple[str, Iterable[EmailAddress]]
            Formatted message and list of recipients
        """
        it = next(self.ix)
        data = it[0].getFieldDetails()

        recipient = self.wm.testmail or it[1]
        data['recipientname'] = recipient.name
        print(f"message to recipients {recipient}")
        print("recipientname", data['recipientname'],
              "chairperson", data.get('chairperson', 'not known'))
        msg = MIMEMultipart('alternative')
        msg['From'] = self.wm.sender
        msg['To'] = addressEmails((recipient,))
        msg['Cc'] = self.wm.sender
        msg['Subject'] = self.wm.subject
        msg.attach(MIMEText(self.wm.gentxt.render(**data), 'plain'))
        msg.attach(MIMEText(self.wm.genhtml.render(**data), 'html'))
        message = msg.as_string()

        return message, recipient


class WriteEmail:
    """Template encapsulation for email writing

    Can generate an iterator for all messages to be sent.
    """

    def __init__(self, program, sender, subject,
                 tmplhtml='templates/mailtemplate.html',
                 tmpltxt='templates/mailtemplate.txt',
                 testmail=None):
        """Email Writer class

        Parameters
        ----------
        program : Program
            Program object with information on sessions, items, etc.
        sender : str
            Sender e-mail address
        subject : str
            Subject line
        tmplhtml : [str,file], optional
            html template by default 'templates/mailtemplate.html'
        tmpltxt : [str,file] optional
            plaintext template, by default 'templates/mailtemplate.txt'
        testmail : str, optional
            test e-mail recipient, by default None
        """

        self.program = program
        self.sender = sender
        self.subject = subject
        self.testmail = testmail and EmailAddress(testmail)
        if isinstance(tmpltxt, str):
            self.gentxt = environment.get_template(tmpltxt)
        else:
            self.gentxt = Template(tmpltxt.read())
        if isinstance(tmplhtml, str):
            self.genhtml = environment.get_template(tmplhtml)
        else:
            self.genhtml = Template(tmplhtml.read())

        self.items = program.getAssignedItems()

    def mails(self, target: str, formatselect=None):
        """Generate an interator for all mails to send

        Arguments:
            target -- Type of recipients, corresponding authors, session
            chairs or a combination, with groups of session chair and
            authors as recipients

        Returns:
            MailIter iterator
        """
        sendlist = []
        if target == 'corresponding':
            for item in self.program.getAssignedItems():
                if formatselect is None or \
                        formatselect in item.getFormats():
                    for corresp in item.correspondingEmails():
                        sendlist.append((item, corresp))
        elif target == 'chairs':
            for session in self.program.sessions.values():
                if formatselect is None or \
                        formatselect in session.getFormats():
                    for chair in session.chairEmails():
                        sendlist.append((session, chair))
        elif target == 'chairgroup':
            for session in self.program.sessions.values():
                if formatselect is None or \
                        formatselect in session.getFormats():
                    for author in session.authorEmails():
                        sendlist.append((session, author))
                    for chair in session.chairEmails():
                        sendlist.append((session, chair))
        else:
            raise ValueError(f'Cannot send mails to group {target}')
        return MailIter(self, sendlist)
