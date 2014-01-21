# Import the future
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# Import standard library modules
import difflib
import os
import re
from datetime import datetime

from Motome.config import END_OF_TEXT
from Motome.Modules.NoteModel import NoteModel

# RegEx to find urls
# https://mail.python.org/pipermail/tutor/2002-September/017228.html
urls = '(?: %s)' % '|'.join("""http telnet gopher file wais ftp""".split())
ltrs = r'\w'
gunk = r'/#~:.?+=&%@!\-'
punc = r'.:?\-'
any = "%(ltrs)s%(gunk)s%(punc)s" % { 'ltrs' : ltrs,
                                     'gunk' : gunk,
                                     'punc' : punc }

URL_RE = r"""
    \b                            # start at word boundary
        %(urls)s    :             # need resource and a colon
        [%(any)s]  +?             # followed by one or more
                                  #  of any valid character, but
                                  #  be conservative and take only
                                  #  what you need to....
    (?=                           # look-ahead non-consumptive assertion
            [%(punc)s]*           # either 0 or more punctuation
            (?:   [^%(any)s]      #  followed by a non-url char
                |                 #   or end of the string
                  $
            )
    )
    """ % {'urls': urls,
           'any': any,
           'punc': punc}


def parse_note_content(data):
        meta = {}
        try:
            idx = data.index(END_OF_TEXT)
            content = data[:idx]
            lines = data[idx:].splitlines()
        except ValueError:
            content = data
            lines = []

        for line in lines:
            try:
                key,value = line.strip().split(':',1)
                if key == 'tags':
                    tags = re.findall(r'\w+',value)  # find all words
                    meta['tags'] = u' '.join(tags)
                else:
                    meta[key] = unicode(value)
            except ValueError:
                pass
        return content,meta


def open_and_parse_note(filepath):
    data = NoteModel.enc_read(filepath)
    return parse_note_content(data)


def safe_filename(filename):
    try:
        pattern = re.compile('[\W_]+')
        root, ext = os.path.splitext(os.path.basename(filename))
        return pattern.sub('_', root) if ext is '' else ''.join([pattern.sub('_', root), ext])
    except:
        return None


def human_date(dt):
    """
    Given a datetime object, return a more human readable date.

    For example, if timestamp is:
    * within a week: Monday 15:11
    * within a year: Aug 6 15:11
    * not this week or this year, so we return locale's appropriate date and time representation.
    """

    # this returns localtime
    now = datetime.now()

    # get a timedelta
    td = now - dt

    if td.days < 7:
        # within a week: Monday 15:11
        return dt.strftime('%A %H:%M')

    elif td.days < 365:
        # within a year: Aug 6 15:11
        return dt.strftime('%b %d %H:%M')

    else:
        # not this week or this year, so we return locale's appropriate date and time representation."
        return dt.strftime('%c')


def diff_to_html(text1, text2, fromdesc='', todesc='Current'):
    """
    Returns an HTML sequence of the difference between two strings
    """
    # hdiff = dmp()
    # diffs = hdiff.diff_main(text1,text2)
    # hdiff.diff_cleanupSemantic(diffs)
    # return hdiff.diff_prettyHtml(diffs)
    hdiff = difflib.HtmlDiff(wrapcolumn=80)
    return hdiff.make_file(text1.splitlines(True), text2.splitlines(True),
                           fromdesc=fromdesc, todesc=todesc, context=True)


def grab_urls(text):
    """ Given a text string, returns all the urls we can find in it.
    from: https://mail.python.org/pipermail/tutor/2002-September/017228.html
    """
    url_re_compile = re.compile(URL_RE, re.VERBOSE | re.MULTILINE)
    return url_re_compile.findall(text)


def build_preview_header_html(title):
    return """
<?xml version="1.0" encoding="UTF-8"?>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<title>{0}</title>
<link rel="stylesheet" href="stylesheets/preview.css">
</head>
<body>
    """.format(title)


def build_preview_footer_html():
    return u'</body>\n</html>'