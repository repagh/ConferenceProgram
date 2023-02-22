#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 11 08:49:33 2023

@author: repa
"""
from jinja2 import Environment, PackageLoader, \
    Template

environment = Environment(
    loader=PackageLoader("programhtml", 'templates')
    )

class WriteHTML:
    
    def __init__(self, project):
        
        self.project = project
        
    def authorList(self, template='authorlist.html'):
        
        if isinstance(template, str):
            gen = environment.get_template(template)
        else:
            gen = Template(template.read())
        return gen.render(authors=self.project.author_list)
        
    def eventList(self, template='eventlist.html'):

        if isinstance(template, str):
           gen = environment.get_template(template)
        else:
           gen = Template(template.read())
        return gen.render(days=self.project.getDays(), 
                          title=self.project.title)