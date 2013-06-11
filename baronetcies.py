#!/usr/bin/env python
#
"""
Copyright (C) 2012 Legoktm

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""
#
# See https://en.wikipedia.org/w/index.php?title=Wikipedia:Bot_requests&oldid=504648019#Baronetcy_articles
#
# Will mass move all non-redirect articles to their lower-case variants

import os
import pywikibot
import robot

def log(old_title, new_title):
    LOGFILE = 'movepages.log'
    if os.path.isfile(LOGFILE):
        f = open(LOGFILE, 'r')
        old = f.read()
        f.close()
    else:
        old = ''
    msg = '*[[:%s]] --> [[:%s]]\n' % (old_title, new_title)
    f = open(LOGFILE, 'w')
    f.write(old+msg)
    f.close()
    


class RMBot(robot.Robot):
    
    def __init__(self):
        robot.Robot.__init__(self, task=16)
        self.reason = 'BOT: Moving %s to %s per [[Talk:Abdy_Baronets#Requested_move|RM]]'

    def run(self):
        cat = pywikibot.Category(pywikibot.Page(self.site, 'Category:Baronetcies'))
        gen = pywikibot.pagegenerators.CategorizedPageGenerator(cat)
        for page in gen:
            self.do_page(page)

    def do_page(self, page):
        old_title = page.title()
        if page.isRedirectPage():
            self.output('Skipping %s, it\'s a redirect' % page.title())
            return
        if not 'Baronets' in old_title:
            self.output('Skipping %s, doesnt contain \'Baronets\' in it.' % page.title())
            return
        new_title = old_title.replace('Baronets', 'baronets')
        if old_title == new_title:
            self.output('New title is same as old title? logging.')
            log(old_title, new_title)
        edit_summary = self.reason % (old_title, new_title)
        self.output('Moving: %s --> %s' % (old_title, new_title))
        try:
            if not self.isEnabled():
                self.output('Disabled, quitting.')
                self.quit()
            page.move(new_title, reason=edit_summary, movetalkpage=True)
        except pywikibot.exceptions.Error, e:
            self.output(e)
            log(old_title, new_title)
            return
            

if __name__ == "__main__":
    bot = RMBot()
    bot.run()