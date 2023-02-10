#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 10 10:35:54 2023

@author: repa
"""
from pyparsing import oneOf, Word, alphas, OneOrMore, ZeroOrMore, \
    Literal, Regex, ParserElement, LineEnd, Opt
from program import Author

# newlines are significant for parsing multi-line author lists
ParserElement.setDefaultWhitespaceChars(' \t')

# ensure we parse most accented names
unicodePrintables = u''.join(chr(c) for c in range(512) 
                             if chr(c).isalpha() or chr(c) == "'" or chr(c) =='-')

def dprint(*argv, **argkw):
    #print(*argv, **argkw)
    pass

# functions to assemble different parts
def setFirst(toks):
    toks['firstname'] = ' '.join(toks)
    dprint(f"firstname {toks}")
def setLast(toks):
    toks['lastname'] = ' '.join(toks)
    dprint(f"lastname {toks}")
def setLastCap(toks):
    toks['lastname'] = toks[0].capitalize()
    dprint(f"lastname {toks[0].capitalize()}")
def setTitle(toks):
    toks['titlepre'] = toks[0]
    dprint(f"titlepre {toks}")
def setTitle2(toks):
    toks['titlepost'] = toks[0]
    dprint(f"titlepost {toks}")
def setAffiliation(toks):
    toks['affiliation'] = ' '.join(toks)
    dprint(f"rest {toks}")
def completeAuthor(toks):
    toks['author'] = Author(toks)
    dprint(f"complete {toks} {list(toks.keys())}")

# parsing tokens and language
titlepre = oneOf(('Dr', 'Dr.', 'Prof', 'Prof.', 'dr.', 'dr.ir.', 'Lt',
                  'Lt Col', 'Lt. Col.')).set_parse_action(setTitle)
titlepost = Literal(',') + \
    oneOf(('MSc', 'MSc.', 'PHD', 'Phd.', 'Ed.D', 'Ph.D.', 'MSC')).set_parse_action(setTitle2)
firstname = (Word(unicodePrintables, asKeyword=True) + 
             ZeroOrMore(Regex(r'[A-Z]\.'))).set_parse_action(setFirst)
nickname = (Literal('(') + Word(unicodePrintables, asKeyword=True) + 
            Literal(')')).set_parse_action(lambda toks: ''.join(toks))

initials = (
    (OneOrMore(Regex(r'([A-Z]\.)+')) + 
     Opt(nickname) +
     ZeroOrMore(Regex(r'([A-Z]\.)+'))).set_parse_action(setFirst) | \
    (ZeroOrMore(Regex(r'([A-Z]\.)+')) + 
     Opt(nickname) +
     OneOrMore(Regex(r'([A-Z]\.)+'))).set_parse_action(setFirst))

lastname = OneOrMore(Word(unicodePrintables, asKeyword=True)).set_parse_action(setLast)
lastcaps = Word(alphas.upper(), asKeyword=True).set_parse_action(setLastCap)

author = (Opt(titlepre) + (initials | firstname) + lastname + Opt(titlepost)) | \
         (lastcaps + firstname + Opt(titlepost))

separator = Literal(',') | Literal('&') | Literal('\n')

author_line = (author + Opt(Literal(',') + 
               Regex(r'[^\n]*').set_parse_action(setAffiliation))
               )
author_lines = author_line + OneOrMore(LineEnd() + author_line)
author_list = author + ZeroOrMore(separator + author) 

class AuthorList(list):
    
    def __init__(self, text):
        if '\n' in test:
            al = author_line.copy().set_parse_action(self.complete)
            parser = al + OneOrMore(LineEnd() + al)
        else:
            au = author.copy().set_parse_action(self.complete)
            parser = au + ZeroOrMore(separator + au) 
        parser.parseString(text)
        
    def complete(self, toks):
        print(f"list addition {dict(toks.items())}")
        self.append(Author(toks))
        
class SingleAuthor(list):
    
    def __init__(self, text):
        parser = author_line.copy().set_parse_action(self.complete)
        parser.parseString(text)
        
    def complete(self, toks):
        self.append(Author(toks))
        
if __name__ == '__main__':
    
    print(initials.parseString('J.J.'))
    print(initials.parseString('J.J. (Rowan)'))
    print(initials.parseString('N. D.'))
    for test in (
            'Dr Amy Irwin',
            'Lt. Col. Pedro Piedade',
            'René van Paassen',
            'OKINAWA John'
            ):
        res = author.parseString(test)
        print (res)
        a = SingleAuthor(test)
        print(a)
        
    
    res = author_lines.parseString('''Lt Nicholas Armendariz, MSC, USN, Naval Aerospace Medical Institute
       J. J. Walcutt, Ph.D., Clay Strategic Designs
       Christina Parker, Ed.D, Education and Technology Branch, Army Aviation Center of Excellence
       Shelbi Kuhlmann, Ph.D., School of Education, UNC-Chapel Hill''')
    
    for test in (
        'Hannah Rennich, Dr. Michael Miller, Dr. John McGuirl, Dr. Timothy Fry',
        'Michael Vidulich & Pamela Tsang',
        'Samantha N. Emerson, Maria Chaparro Osman, Cait Rizzardo, Kent C. Halverson, Steve Ellis, Don Haley',
        'Lynne Martin, Lauren Roberts, Joey Mercer, Yasmin Arbab, Charles Walter, William McCarty, Charles Sheehe III',
        'Ivo Stuldreher, Erik Van der Burg, Wietse Ledegang, Mark Houben, Yvonne Fonken & Eric Groen',
        '''Lt Nicholas Armendariz, MSC, USN, Naval Aerospace Medical Institute
        J.J. Walcutt, Ph.D., Clay Strategic Designs
        Christina Parker, Ed.D, Education and Technology Branch, Army Aviation Center of Excellence
        Shelbi Kuhlmann, Ph.D., School of Education, UNC-Chapel Hill'''):
        if '\n' in test:
            res = author_lines.parseString(test)
        else:
            res = author_list.parseString(test)
        print (res)
        a = AuthorList(test)
        print(a)