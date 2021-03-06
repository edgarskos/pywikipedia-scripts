#!/usr/bin/env python
from __future__ import unicode_literals

import datetime
import mwparserfromhell
import pywikibot
import re

site = pywikibot.Site('en', 'wikipedia')

GA_SUBPAGES = ['Agriculture, food and drink', 'Art and architecture', 'Engineering and technology',
               'Geography and places', 'History', 'Language and literature', 'Mathematics', 'Music', 'Natural sciences',
               'Philosophy and religion', 'Social sciences and society', 'Sports and recreation',
               'Media and drama', 'Warfare', 'Video games']

ARTICLE_HISTORY = ['Article history', 'Article History', 'Article milestones', 'ArticleHistory', 'Articlehistory', 'Article milestones']

GA_TEMPLATE = ['GA', 'Ga']

STUFF_TO_PROCESS = [
    ('Wikipedia:Featured article candidates/Featured log', True, 'FA'),
    ('Wikipedia:Featured article candidates/Archived nominations', False, 'FA'),
    ('Wikipedia:Featured list candidates/Featured log', True, 'FL'),
    ('Wikipedia:Featured list candidates/Failed log', False, 'FL'),
]


def get_facs_to_handle(prefix):
    monthyear = datetime.datetime.utcnow().strftime('%B %Y')
    monthpage = pywikibot.Page(site, prefix + '/' + monthyear)
    data = {}
    # FIXME: HAAAAAAAAAAAACK
    # Assumes that log will have <100 edits
    print 'Fetching log page history'
    site.loadrevisions(monthpage, getText=True, rvdir=False,
                       step=100, total=100, startid=None)
    hist = monthpage.fullVersionHistory(total=100)  # This should fetch nothing...
    for revision in hist:
        for temp in mwparserfromhell.parse(revision[3]).filter_templates():
            data[unicode(temp.name)] = (revision[0], revision[1], revision[2])
    return data


def promote_fac(fac_name, rev_info, was_promoted, featured_type='FA'):
    pg = pywikibot.Page(site, fac_name)
    article_title = fac_name.split('/')[1]
    oldid = rev_info[0]
    c_abbr = featured_type + 'C'  # Either 'FLC' or 'FAC'
    is_fa = featured_type == 'FA'
    timestamp = rev_info[1].strftime('%H:%M, %d %B %Y (UTC)')
    username = rev_info[2]
    text = pg.get()
    if was_promoted:
        prom_text = 'promoted'
    else:
        prom_text = 'not promoted'
    if '<!--FAtop-->' in text or '<!--FLtop-->' in text:
        # Already handled
        print '%s has already been handled, skipping.' % fac_name
        return
    print unicode(fac_name), oldid
    if is_fa:
        top_text = "{{{{subst:Fa top|result='''{prom}''' by [[User:{user}|{user}]] {ts} " \
                   "[//en.wikipedia.org/?diff={oldid}]}}}}"\
            .format(user=username, ts=timestamp, oldid=oldid, prom=prom_text)
        bottom_text = '{{subst:Fa bottom}}'
    else:
        top_text = '{{{{subst:User:Hahc21/FLTop|result={prom}|closer={user}|time={ts}|link=diff={oldid}]}}}}'\
            .format(prom=prom_text, user=username, ts=timestamp, oldid=oldid)
        bottom_text = '{{subst:User:Hahc21/FCloseBottom}}'
    newtext = top_text + '\n' + text + '\n' + bottom_text
    pg.put(newtext, 'Bot: Archiving ' + c_abbr)
    article = pywikibot.Page(site, article_title)
    article_text = article.get()
    if was_promoted:
        # add the FA icon, possibly removing the GA icon
        needs_fa_icon = True
        if is_fa:
            icon = '{{featured article}}'
        else:
            icon = '{{featured list}}'
        if re.search('\{\{featured\s?(small|article|list)\}\}', article_text, re.IGNORECASE):
            needs_fa_icon = False
            new_article_text = None  # Shut up PyCharm
        elif re.search('\{\{(good|ga) article\}\}', article_text, re.IGNORECASE):
            new_article_text = re.sub('\{\{(good|ga) article\}\}', icon, article_text, flags=re.IGNORECASE)
        else:
            new_article_text = icon + '\n' + article_text
        if needs_fa_icon:
            article.put(new_article_text, 'Bot: Adding '+icon)
    latest_rev = pywikibot.Page(site, article_title).latestRevision()
    article_talk = article.toggleTalkPage()
    article_talk_text = article_talk.get()

    if was_promoted:
        current_status = featured_type  # 'FA' or 'FL'
    else:
        current_status = 'F' + c_abbr  # 'FFAC' or 'FFLC'

    has_article_history = False
    parsed = mwparserfromhell.parse(article_talk_text)
    # First we're going to do a preliminary check for {{GA}} and stuffs.
    pre_stuff_params = {}
    for temp in parsed.filter_templates():
        for ga_name in GA_TEMPLATE:
            if temp.name.matches(ga_name):
                pre_stuff_params[''] = 'GAN'
                pre_stuff_params['date'] = temp.get(1).value
                pre_stuff_params['result'] = 'promoted'  # Safe to assume?
                pre_stuff_params['link'] = article_talk.title() + '/GA' + unicode(temp.get('page').value)
                for param in ['topic', 'oldid']:
                    pre_stuff_params[param] = temp.get(param).value

    for temp in parsed.filter_templates():
        # This might have some false positives, may need adjusting later.
        if was_promoted and temp.has_param('class'):
            temp.get('class').value = featured_type
        for ah_name in ARTICLE_HISTORY:
            if temp.name.matches(ah_name):
                has_article_history = True
                num = 1
                while temp.has_param('action' + str(num)):
                    num += 1
                for param in pre_stuff_params:
                    if param == 'topic':
                        temp.add('topic', pre_stuff_params['topic'])
                    else:
                        temp.add('action'+str(num)+param, pre_stuff_params[param])
                num += 1
                action_prefix = 'action' + str(num)
                temp.add(action_prefix, c_abbr)
                temp.add(action_prefix+'date', timestamp.replace(' (UTC)', ''))
                temp.add(action_prefix+'link', fac_name)
                temp.add(action_prefix+'result', prom_text)
                temp.add(action_prefix+'oldid', latest_rev)
                if temp.has('currentstatus', ignore_empty=False):
                    if was_promoted or temp.get('currentstatus').value != 'GA':
                        temp.get('currentstatus').value = current_status
                else:
                    temp.add('currentstatus', current_status)
                break

    article_talk_text = unicode(parsed)
    if not has_article_history:
        article_history_text = mwparserfromhell.parse('{{Article history}}')
        temp = article_history_text.filter_templates()[0]
        for param in pre_stuff_params:
            if param == 'topic':
                temp.add('topic', pre_stuff_params[param])
            else:
                temp.add('action1'+param, pre_stuff_params[param])
        new_params = {
            'action2': c_abbr,
            'action2date': timestamp,
            'action2link': fac_name,
            'action2result': prom_text,
            'action2oldid': latest_rev,
            'currentstatus': current_status,
        }
        for param in new_params:
            temp.add(param, new_params[param])
        article_talk_text = unicode(article_history_text) + article_talk_text
    article_talk_text = re.sub('\{\{(featured (list|article) candidates|ga)\s*\|.*?\}\}', '', article_talk_text,
                               flags=re.IGNORECASE)
    article_talk.put(unicode(article_talk_text).strip(), 'Bot: Updating {{Article history}} after ' + c_abbr)
    if was_promoted and is_fa:
        print 'Checking GA listings...'
        # Only FA's can be GA's, not FL's.
        update_ga_listings(article_title)
    quit()


def update_ga_listings(article):
    """
    This whole function is pretty bad.
    We can optimize checking all the subpages by doing a db query
    on the pagelinks table and only look for subpages of "WP:GA"
    """
    for subj in GA_SUBPAGES:
        pg = pywikibot.Page(site, 'Wikipedia:Good articles/' + subj)
        if pg.isRedirectPage():
            pg = pg.getRedirectTarget()
        text = pg.get()
        if not article in text:
            continue
        # This part is weird, but meh
        lines = text.splitlines()
        for line in lines[:]:
            if article in line:
                lines.remove(line)
                break
        pg.put('\n'.join(lines), 'Bot: Removing [[%s]] since it was promoted to FA' % article)
        break


if __name__ == '__main__':
    for prefix, was_promoted, featured_type in STUFF_TO_PROCESS:
        facs = get_facs_to_handle(prefix)
        for fac, rev_info in facs.iteritems():
            if fac == 'TOClimit':
                continue
            promote_fac(fac, rev_info, was_promoted=was_promoted, featured_type=featured_type)

