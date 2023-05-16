from collections.abc import Iterable
import pyparsing as pp
import html

# parsing rule for email addresses
_mailaddress = pp.Regex(r"[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}")


class EmailAddress:
    """Name and email address type
    """

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
            except pp.ParseException:
                raise ValueError(f"Cannot get email address from {args[1]}")

        # no person, no email email address, return None
        elif not args[0]:
            self.name = ''
            self.email = None

        # try to parse email address and name from args[0]
        elif '<' in args[0] and args[0].strip()[-1] == '>':
            try:
                self.name = html.unescape(args[0].split('<')[0].strip())
                self.email = _mailaddress.parse_string(
                    args[0].split('<')[1][:-1].strip())
            except pp.ParseException:
                raise ValueError(f"Cannot get email address from {args[0]}")
        else:
            raise ValueError(f"Cannot get email address from {args[0]}")

    def __str__(self):

        if self.name:
            return f"{html.escape(self.name)} <{self.email}>"
        return self.email or ''

    def getEmail(self):
        return self.email


def parseEmails(*args, single=False):
    res = []
    print(f"parsing emails from {args}")

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

    for i, r in enumerate(res):
        print(f"email {i} parse results {r}")

    # return only the first name/email
    if single and res:
        if len(res) > 1:
            print(f"Warning, ignoring emails {res[1:]}")
        return res[0]
    elif single:
        return None
    return res


def addressEmails(mails: Iterable[EmailAddress]):
    """Convert email into printable string

    Parameters
    ----------
    mails : Iterable[EmailAddress]
        Mails to convert

    Returns
    -------
    str
        Comma-separated list of name+email address
    """
    return ', '.join(map(str, mails))
