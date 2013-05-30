#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Published by Hazard-SJ (https://meta.wikimedia.org/wiki/User:Hazard-SJ)
# under the terms of Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)
# https://creativecommons.org/licenses/by-sa/3.0/

import pywikibot
import mwparserfromhell
from catlib import Category

class CitationStyleRobot(object):
    def __init__(self):
        self.site = pywikibot.Site("en", "wikipedia")
        self.categories = [
            Category(self.site, "Category:Pages with citations having wikilinks embedded in URL titles"),
            ]
        self.doTaskPage = pywikibot.Page(self.site, 'User:Hazard-Bot/DoTask/21')

    def checkDoTaskPage(self):
        try:
            text = self.doTaskPage.get(force = True)
        except pywikibot.IsRedirectPage:
            raise Exception(u"The 'do-task page' (%s) is a redirect." % self.doTaskPage.title(asLink = True))
        except pywikibot.NoPage:
            raise Exception(u"The 'do-task page' (%s) does not exist." % self.doTaskPage.title(asLink = True))
        else:
            if text.strip().lower() == u"true":
                return True
            else:
                raise Exception(u"The task has been disabled from the 'do-task page' (%s)." % self.doTaskPage.title(asLink = True))

    def removeWikilinks(self):
        def replaceWikilinks(template, URL, title):
            if template.has_param(URL):
                if template.has_param(title):
                    links = template.get(title).value.filter_links()
                    if links:
                        for link in links:
                            if link.text:
                                self.code.replace(link, link.text)
                            else:
                                self.code.replace(link, link.title)
                    temps = template.get(title).value.filter_templates()
                    if temps:
                        for temp in temps:
                            self.code.remove(temp)
        ## @fixme: Use a function, and use {{Cite doi}} as well, just in case...
        ## ...or generate from [[Category:Citation Style 1 templates]]? (doesn't include {{citation}} though)
        #template = pywikibot.Page(self.site, "Template:Cite web")
        #templates = list()
        #templates.append(template.title(withNamespace = False).lower())
        #references = template.getReferences(redirectsOnly = True)
        #for reference in references:
        #    templates.append(reference.title(withNamespace = False).lower())
        for template in self.code.filter_templates():
            if template.name.lower().strip().startswith("cite") \
            or template.name.lower().strip().startswith("web") \
            or (template.name.lower().strip() == "citation"):
                replaceWikilinks(template,             "url", "title"        )
                replaceWikilinks(template,      "chapterurl", "chapter"      )
                replaceWikilinks(template,      "chapterurl", "contribution" )
                replaceWikilinks(template,      "chapterurl", "entry"        )
                replaceWikilinks(template,      "chapterurl", "article"      )
                replaceWikilinks(template,   "conferenceurl", "conference"   )
                replaceWikilinks(template, "contributionurl", "chapter"      )
                replaceWikilinks(template, "contributionurl", "contribution" )
                replaceWikilinks(template, "contributionurl", "entry"        )
                replaceWikilinks(template, "contributionurl", "article"      )
                replaceWikilinks(template,   "transcripturl", "transcript"   )

    def run(self):
        for category in self.categories:
            self.checkDoTaskPage()
            for self.page in category.articles():
                print
                try:
                    text = self.page.get()
                    self.code = mwparserfromhell.parse(text)
                    self.removeWikilinks()
                    # and all the others, once they're coded, if they're coded
                    if text != self.code:
                        pywikibot.showDiff(text, unicode(self.code))
                        self.page.put(unicode(self.code), u"[[Wikipedia:Bots|Robot]]: Fixed [[Help:Citation Style 1|citation style]] errors")
                    else:
                        print u"Skipping: No change was made"
                except:
                    print u"Skipping: Error encountered"

def main():
    bot = CitationStyleRobot()
    bot.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
