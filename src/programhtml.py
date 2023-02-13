#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb 11 08:49:33 2023

@author: repa
"""
from jinja2 import Environment, FileSystemLoader, PackageLoader

environment = Environment(
#    loader=FileSystemLoader("templates/")
    loader=PackageLoader("programhtml", 'templates')
    )

class WriteHTML:
    
    def __init__(self, project):
        
        self.project = project
        
    def authorList(self, template='authorlist.html'):
        
        gen = environment.get_template(template)
        return gen.render(authors=self.project.author_list)
        
    def eventList(self, template='eventlist.html'):
        
        gen = environment.get_template(template)
        return gen.render(events=self.project.getEvents())