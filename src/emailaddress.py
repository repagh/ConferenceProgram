import pyparsing as pp
import html
import sys
from collections.abc import Iterable

#unicodePrintables = u''.join(chr(c) for c in range(sys.maxunicode) 
#                                        if not chr(c).isspace())
_mailaddress = pp.Regex(r"[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}")
#_mailname = pp.OneOrMore(pp.Word(unicodePrintables,excludeChars='<'))
#_nameandmail = _mailname + \
#    pp.Literal('<') + _mailaddress + pp.Literal('>')


class EmailAddress:

    def __init__(self, *args):
        """Create/parse name + email address combination

        Arguments:
        -- name, email
            First argument is name, second email

        -- emailstring
            Parsed for "name <email@org.x>", 
            otherwise parsed as email address
        """
        if len(args) == 2 and args[1]:

            try:
                self.name = args[0]
                self.email = _mailaddress.parse_string(args[1], True)[0]
            except:
                raise ValueError(f"Cannot get email address from {args[1]}")

        # no person, no email email address, return None
        elif not args[0]:
            return None

        # try to parse email address and name from args[0]
        elif '<' in args[0] and args[0].strip()[-1] == '>':
            try:
                self.name = html.unescape(args[0].split('<')[0].strip())
                self.email = _mailaddress.parse_string(
                    args[0].split('<')[1][:-1].strip())
            except:
                raise ValueError(f"Cannot get email address from {args[0]}")
        else:
            raise ValueError(f"Cannot get email address from {args[0]}")

    def __str__(self):

        if self.name:
            return f"{html.escape(self.name)} <{self.email}>"
        return self.email

    def getEmail(self):
        return self.email


def parseEmails(*args, single=False):
    res = []

    if args[0] is None:
        args = ('', *args[1:])

    # here, assume the e-mail is in the args[1]
    if len(args) == 2 and args[1]:
        
        # Equal number of names and email addresses
        if args[0].count(',') == args[1].count(','):
            for name, email in zip(args[0].split(','), args[1].split(',')):
                res.append(EmailAddress(name, email))

        # One name, possibly multiple email addresses
        elif ',' not in args[0]:
            for email in args[1].split(','):
                res.append(EmailAddress(args[0], email))

        # Only one email address
        else:
            res.append(EmailAddress(*args))

    # assume all in the first string
    else:
        for name_email in args[0].split(','):
            res.append(EmailAddress(name_email))
    
    # return only the first name/email
    if single and res:
        if len(res) > 1:
            print(f"Warning, ignoring emails {res[1:]}")
        return res[0]
    elif single:
        return None
    return res

def addressEmails(mails: Iterable[EmailAddress]):
    return ', '.join(map(str, mails))