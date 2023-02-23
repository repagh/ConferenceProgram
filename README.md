# ConferenceProgram

## Introduction

Create a conference program from a spreadsheet specification. There is
an example spreadsheet available, with a conference invented together
with ChatGPT. The example sheet also contains instructions on how to
format your data. It is also possible to directly load the program
from a Google spreadsheet.

The conference program and the author list can be converted to html
pages, pdf files or Microsoft Word compatible docx files.

## Installation

This is a really simple Python program. Just clone the source and run
it.  I recommend a miniconda or anaconda environment, with the
following packages added:

- weasyprint
- pandas
- gspread
- jinja2
- python-docx
- argparse

## Running

Check the instructions with:
    
    python src/makebook.py --help

Check the instructions in the first sheet of the
`example/exampledata.xlsx` file for the formatting requirements of the
input data. Note that most common formats for author names are parsed,
and best results are obtained when authors are listed on individual
lines in the author_list cell.
