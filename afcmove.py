#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
(C) 2012, Legoktm, under the MIT License
Checks the recently moved pages list to see
if they were messed up AFC moves. If so, log them at [[Wikipedia:Articles for creation/Wrongly moved submissions]]
"""

import pywikibot
import pywikibot.data.api
import datetime
import os
site = pywikibot.getSite()

def MovedPagesGenerator(timestamp):
  request = pywikibot.data.api.ListGenerator(site=site, listaction='logevents',letype='move', lestart=timestamp, ledir='newer')
  for item in request:
    yield {'old':item['title'], 'new':item['move']['new_title'], 'user':item['user']}




def create_timestamp():
  now = datetime.datetime.now()
  return '%s-%s-%sT%s:00:00Z' % (now.year, abs_zero(now.month), abs_zero(now.day), abs_zero(now.hour))

def abs_zero(input):
  if len(str(input)) == 1:
    return '0' + str(input)
  return str(input)

def main():
  #get page list
  timestamp = create_timestamp()
  gen = MovedPagesGenerator(timestamp=timestamp)
  logtext = ''
  for item in gen:
    log = False
    old = item['old']
    new = item['new']
    user = item['user']
    if new.startswith('Articles for creation/'):
      print 'Will log %s --> %s' % (old, new)
      log = True
    if old.startswith('Wikipedia talk:Articles for creation/') and new.startswith('Wikipedia talk:'):
      print 'Will log %s --> %s' % (old, new)
      log = True
    if old.startswith('Wikipedia:Articles for creation/') and new.startswith('Wikipedia:'):
      print 'Will log %s --> %s' % (old, new)
      log = True
    if not log:
      print 'Skipping %s --> %s' % (old, new)
      continue
    logtext += '* [[%s]] --> [[%s]] by [[User:%s|]]\n' % (old, new, user)
  if logtext == '':
    print 'Nothing was detected, won\'t update the log.'
    return
  p = pywikibot.Page(site, 'Wikipedia:Articles for creation/Wrongly moved submissions')
  current_text = p.get()
  newtext = current_text + logtext
  p.put(newtext, 'BOT: Updating log')
    
    
if __name__ == "__main__":
  main()