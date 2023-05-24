#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Feb 10 10:35:54 2023

@author: repa
"""
from pyparsing import oneOf, Word, alphas, OneOrMore, ZeroOrMore, \
    Literal, Regex, ParserElement, LineEnd, Opt, ParseException
import sys

# newlines are significant for parsing multi-line author lists
ParserElement.setDefaultWhitespaceChars(' \t')

# ensure we parse most accented names
unicodePrintables = u''.join(chr(c) for c in range(512)
                             if chr(c).isalpha() or chr(c) == "'" or
                             chr(c) == '-' or chr(c) == '_')


def dprint(*argv, **argkw):
    # print(*argv, **argkw)
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
                  'Lt Col', 'Lt. Col.', 'Prof. Dr.-Ing.', 'Professor',
                  'Mr', 'Mr.', 'Mrs.')).set_parse_action(setTitle)
titlepost = Literal(',') + \
    oneOf(('MSc', 'MSc.', 'PHD', 'Phd.', 'Ed.D', 'Ph.D.', 'MSC',
           'MS')).set_parse_action(setTitle2)
firstname = (Word(unicodePrintables, asKeyword=True) +
             ZeroOrMore(Regex(r'[A-Z]\.'))).set_parse_action(setFirst)
nickname = (Literal('(') + Word(unicodePrintables, asKeyword=True) +
            Literal(')')).set_parse_action(lambda toks: ''.join(toks))

initial = Regex(r'([A-Z]\.)+')
initials = (
    (OneOrMore(initial) +
     Opt(nickname) +
     ZeroOrMore(initial)).set_parse_action(setFirst) |
    (ZeroOrMore(initial) +
     Opt(nickname) +
     OneOrMore(initial)).set_parse_action(setFirst))

lastname = OneOrMore(Word(unicodePrintables, asKeyword=True)
                     ).set_parse_action(setLast)
lastcaps = Word(alphas.upper(), min=2,
                asKeyword=True).set_parse_action(setLastCap)

author = (lastcaps + firstname + Opt(titlepost)) | \
    (Opt(titlepre) + (initials | firstname) + lastname + Opt(titlepost))


separator = Literal(',') | Literal('&') | Literal('\n')

author_line = (author + Opt(Literal(',') +
               Regex(r'[^\n]*').set_parse_action(setAffiliation))
               )
author_lines = author_line + OneOrMore(LineEnd() + author_line)
author_list = author + ZeroOrMore(separator + author)


def printattr(o, attrib, pre='', post=' ', default=''):
    if hasattr(o, attrib):
        return pre + str(getattr(o, attrib)) + post
    return default


def daysort(ses):
    _dayvalue = dict(wed=300, thu=400, fri=500, sat=600)
    try:
        return _dayvalue[ses[:3]] + 10*int(ses[4]) + \
            ((len(ses) == 6) and (ord(ses[5])-ord('a')) or 0)
    except Exception:
        return 0


class Author:

    _members = ('orcid', 'affiliation', 'email',
                'picture', 'biography')

    def __new__(cls, *argv, **argkw):
        if len(argv) == 2 and hasattr(argv[0], 'keys'):
            return cls._from_dict(argv[0], argv[1])
        elif len(argv) == 3:
            return cls._from_iterable(argv[0], argv[1], argv[2])
        raise ValueError(f"Cannot make author from {argv}")

    @classmethod
    def _from_parts(cls, firstname, lastname, orcid, program):

        if firstname.upper() == firstname and '.' not in firstname:
            firstname, lastname = lastname, firstname

        try:
            return program.authors[(lastname, firstname, orcid)]
        except KeyError:
            if orcid is None:

                # is there an author def with orcid in there?
                for k, a in program.authors.items():
                    if k[:2] == (lastname, firstname):
                        print(f"Matching {lastname}, {firstname} to orcid={k[2]}",
                              file=sys.stderr)
                        return a
            else:

                # is the name there, but without orcid? Appropriate
                a = program.authors.get((lastname, firstname, None), False)
                if a:
                    print(f"Matching orcid={orcid} to {lastname}, {firstname}",
                          file=sys.stderr)
                    del program.authors[(lastname, firstname, None)]
                    program.authors[(lastname, firstname, orcid)] = a
                    return a

        # apparently nothing found, create a new author
        obj = super().__new__(cls)
        obj.lastname = lastname
        obj.firstname = firstname
        obj.orcid = orcid
        obj._items = []
        program.authors[obj.key()] = obj
        return obj

    @classmethod
    def _from_dict(cls, data, program):
        obj = cls._from_parts(data.get('firstname'),
                              data.get('lastname', 'Anonymous'),
                              data.get('orcid', None),
                              program)
        for k, v in data.items():
            setattr(obj, k, v)
        return obj

    @classmethod
    def _from_iterable(cls, row, data, program):
        obj = SingleAuthor(data['author'], program)[0]

        # these are directly coupled
        for m in cls._members:
            setattr(obj, m, data[m])

        # if applicable, remove the un-orcided one, and install with orcid
        if obj.orcid:
            try:
                del program.authors[(obj.lastname, obj.firstname, None)]
                program.authors[(obj.lastname, obj.firstname, obj.orcid)] = obj
                # print(f"Adding orcid to author {str(obj)}")
            except KeyError:
                pass
        return obj

    def __str__(self):
        return f'{self.lastname}, {self.firstname}'

    def __eq__(self, o):
        return self.lastname == o.lastname and self.firstname == o.firstname

    def __lt__(self, o):
        if self.lastname < o.lastname:
            return True
        if self.firstname < o.firstname:
            return True

    def __hash__(self):
        return hash((self.lastname, self.firstname))

    @classmethod
    def find(cls, **kw):
        try:
            return cls._authors((kw['lastname'], kw['firstname'],
                                 kw.get('orcid', None)))
        except KeyError:
            pass
        try:
            for k, o in cls._authors.items():
                if k[2] == kw['orcid']:
                    return o
        except KeyError:
            raise KeyError("Wrong arguments to find author")
        raise KeyError(f"Cannot find author from {kw}")

    def key(self):
        return (self.lastname, self.firstname, self.orcid)

    def nameLastFirst(self):
        return f'{self.lastname}, {printattr(self, "titlepre")}{self.firstname}{printattr(self, "titlepost", pre=", ", post="")}'

    def getEventCodes(self):
        res = []
        for it in self._items:
            res.extend(it.getEvents())
        return sorted(res, key=daysort)


class AuthorList(list):

    def __init__(self, text, program):
        self.program = program
        text = text.strip()
        if '\n' in text:
            al = author_line.copy().set_parse_action(self.complete)
            parser = al + OneOrMore(LineEnd() + al)
        else:
            au = author.copy().set_parse_action(self.complete)
            parser = au + ZeroOrMore(separator + au)
        parser.parseString(text)

    def complete(self, toks):
        dprint(f"list addition {dict(toks.items())}")
        self.append(Author(toks, self.program))


class SingleAuthor(list):

    def __init__(self, text, program):
        self.program = program
        parser = author_line.copy().set_parse_action(self.complete)
        try:
            parser.parseString(text.strip())
        except ParseException:
            raise ParseException(f"Cannot read single author from {text}")

    def complete(self, toks):
        self.append(Author(toks, self.program))


if __name__ == '__main__':

    print(initial.parseString(' A. '))
    print(initial.parseString(' A.J. '))
    print(initial.parseString('B. '))

    print(initials.parseString('J.J. '))
    print(initials.parseString('J.J. (Rowan)'))
    print(initials.parseString('N. D. '))
    for test in (
            'Dr Amy Irwin',
            'Lt. Col. Pedro Piedade',
            'René van Paassen',
            'OKINAWA John'
    ):
        res = author.parseString(test)
        print(res)

    res = author_lines.parseString('''Lt Nicholas Armendariz, MSC, USN, Naval Aerospace Medical Institute
       J. J. Walcutt, Ph.D., Clay Strategic Designs
       Christina Parker, Ed.D, Education and Technology Branch, Army Aviation Center of Excellence
       Shelbi Kuhlmann, Ph.D., School of Education, UNC-Chapel Hill''')

    for test in (
        'Hannah Rennich, Dr. Michael Miller, Dr. John McGuirl, Dr. Timothy Fry',
        'Michael Vidulich & Pamela Tsang',
        'Nejc Sedlar, Dr Amy Irwin, Prof Amelia Hunt',
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
        print(res)
