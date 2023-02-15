#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 11 08:49:33 2023

@author: repa
"""

# pypdf2 : reading/combining /pypdf /pypdf3 
# weasyprint : rendering with CSS
from weasyprint import HTML, CSS
from programhtml import WriteHTML
from weasyprint.text.fonts import FontConfiguration
from jinja2 import PackageLoader

class WritePDF:
    
    def __init__(self, project, tdir='templates'):
        
        self.html = WriteHTML(project)
        self.tdir = tdir
        
    def authorList(self, fname, template='authorlist.html'):
        
        hm = HTML(string=self.html.authorList(template=template))
        css = CSS(filename=f"{self.tdir}/printstyles.css")
        fontconfig = FontConfiguration()    
        hm.write_pdf(fname, stylesheets=[css], font_config=fontconfig)
        
    def eventList(self, fname, template='eventlist.html'):
    
        hm = HTML(string=self.html.eventList(template=template))
        css = CSS(filename=f"{self.tdir}/printstyles.css")
        fontconfig = FontConfiguration()
        hm.write_pdf(fname, stylesheets=[css], font_config=fontconfig)