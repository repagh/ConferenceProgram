import pyparsing as pp
import html

_mailaddress = pp.Regex(r"[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}")
_mailname = pp.OneOrMore(pp.Word(pp.printables,excludeChars='<'))
_nameandmail = _mailname + \
    pp.Literal('<') + _mailaddress + pp.Literal('>')


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
        
        else:
            try:
                res = _nameandmail.parse_string(args[0], True)
                self.name = html.unescape(' '.join(res[:-3]))
                self.email = res[-2]
            except:
                pass

            try:
                self.name = ''
                self.email = _mailaddress.parse_string(args[0], True)[0]
            except:
                raise ValueError(f"Cannot get email address from {args[0]}")

    def __str__(self):

        if self.name:
            return f"{html.escape(self.name)} <{self.email}>"
        return self.email

    def getEmail(self):
        return self.email
