#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Published by Hazard-SJ (https://wikitech.wikimedia.org/wiki/User:Hazard-SJ)
# under the terms of Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)
# https://creativecommons.org/licenses/by-sa/3.0/

from __future__ import unicode_literals
from datetime import datetime
import re

import mwparserfromhell

import pywikibot
from catlib import Category

class CitationStyleRobot(object):
    def __init__(self):
        self.site = pywikibot.Site("en", "wikipedia")
        self.categories = [
            Category(self.site, "Category:Pages with archiveurl citation errors"),
            Category(self.site, "Category:Pages with citations having wikilinks embedded in URL titles"),
            Category(self.site, "Category:Pages with empty citations")
        ]
        self.doTaskPage = pywikibot.Page(self.site, "User:Hazard-Bot/DoTask/21")
        self.citationTemplates = self.getAllTitles("Template:Citation")
        citationTemplatesCategory = Category(self.site, "Category:Citation Style 1 templates")
        for page in citationTemplatesCategory.articles():
            if ("/" not in page.title()) and (page.namespace() == 10):
                self.citationTemplates.extend(self.getAllTitles(page.title()))
        self.subscription = self.getAllTitles("Template:Subscription required")
        self.lang = self.getAllTitles("Template:Lang")
        self.lang.extend(self.getAllTitles("Template:Rtl-lang"))
        self.loadLanguages("User:Hazard-Bot/Languages.css")
        self.citationNeededTemplate = mwparserfromhell.nodes.template.Template(
            "citation needed",
            params = [
                mwparserfromhell.nodes.extras.parameter.Parameter(
                    "date",
                    "{{subst:CURRENTMONTHNAME}} {{subst:CURRENTYEAR}}"
                )
            ]
        )

    def checkDoTaskPage(self):
        try:
            text = self.doTaskPage.get(force = True)
        except pywikibot.IsRedirectPage:
            raise Exception(
                "The 'do-task page' (%s) is a redirect." % self.doTaskPage.title(asLink = True)
            )
        except pywikibot.NoPage:
            raise Exception(
                "The 'do-task page' (%s) does not exist." % self.doTaskPage.title(asLink = True)
            )
        else:
            if text.strip().lower() == "true":
                return True
            else:
                raise Exception(
                    "The task has been disabled from the 'do-task page' (%s)."
                    % self.doTaskPage.title(asLink = True)
                )

    def getAllTitles(self, title):
        page = pywikibot.Page(self.site, title, defaultNamespace = 10)
        if page.isRedirectPage():
            page = page.getRedirectTarget()
        redirects = page.getReferences(redirectsOnly = True)
        titles = [page.title(withNamespace = False).lower()]
        for redirect in redirects:
            if page.namespace() == redirect.namespace():
                titles.append(redirect.title(withNamespace = False).lower())
        return titles

    def loadLanguages(self, title):
        self.languages = {}
        page = pywikibot.Page(self.site, title)
        text = page.get()
        lines = text.splitlines()
        for line in lines:
            code, name = line.split(":")
            self.languages[code] = name

    def getLanguage(self, code):
        try:
            return self.languages[code]
        except KeyError:
            return "{{#language:%s|en}}" % code

    def removeWikilinks(self):
        def replaceWikilinks(URL, title):
            if not (self.template.has_param(URL) and self.template.has_param(title)):
                return
            links = self.template.get(title).value.filter_wikilinks()
            if links:
                for link in links:
                    if link.text:
                        self.template.replace(link, link.text)
                    else:
                        self.template.replace(link, link.title)
            temps = self.template.get(title).value.filter_templates()
            if temps:
                for temp in temps:
                    if (temp.name.lower().strip() in self.subscription) and temp.has_param("via"):
                        self.template.add("via", temp.get("via").value)
                        self.template.get(title).value.remove(temp)
                    elif temp.name.lower().strip() in self.lang:
                        if self.template.has_param("language"):
                            self.template.remove("language")
                        self.template.add("language", self.getLanguage(temp.get(1).value.lower().strip()))
                        self.template.get(title).value.replace(temp, temp.get(2).value)
                    elif temp.name.lower().strip().startswith("lang-"):
                        if self.template.has_param("language"):
                            self.template.remove("language")
                        self.template.add("language", self.getLanguage(temp.name.lower().strip()[5:]))
                        self.template.get(title).value.replace(temp, temp.get(1).value)
                    else:
                        self.code.insert_after(self.template, temp)
                        self.template.get(title).value.remove(temp)
        replaceWikilinks("url", "title")
        replaceWikilinks("chapterurl", "article")
        replaceWikilinks("chapterurl", "chapter")
        replaceWikilinks("chapterurl", "entry" )
        replaceWikilinks("chapterurl", "contribution")
        replaceWikilinks("conferenceurl", "conference")
        replaceWikilinks("contributionurl", "entry")
        replaceWikilinks("contributionurl", "article")
        replaceWikilinks("contributionurl", "chapter")
        replaceWikilinks("contributionurl", "contribution")
        replaceWikilinks("transcripturl", "transcript")

    def fixEmptyCitations(self):
        parameters = [param.value.strip() for param in self.template.params]
        empty = True
        for parameter in parameters:
            if parameter:
                empty = False
                break
        if not empty:
            return
        self.code.replace(self.template, self.citationNeededTemplate)

    def getURLFromArchive(self):
        if not (self.template.has_param("archiveurl") and not self.template.has_param("url")):
            return
        archiveURL = self.template.get("archiveurl").strip()
        URL = None
        if re.search(".*?web\.archive\.org/web/\d*/", archiveURL):
            URL = re.compile(".*?web\.archive\.org/web/\d*/").sub("", archiveURL)
        if not URL:
            return
        if not re.match("(https?:)?//", URL, re.I):
            URL = "http://%s" % URL
        self.template.add("url", URL)

    def getArchiveDate(self):
        if not (self.template.has_param("archiveurl") and not self.template.has_param("archivedate")):
            return
        archiveURL = self.template.get("archiveurl").strip()
        if re.search(".*?web\.archive\.org/web/\d*/", archiveURL):
            timestamp = re.compile(".*?web\.archive\.org/web/(?P<date>\d*)/.*").sub("\g<date>", archiveURL)
            date = datetime.strptime(timestamp,'%Y%m%d%H%M%S')
            self.template.add("archivedate", date.strftime("%d %B %Y"))

    def run(self):
        for category in self.categories:
            self.checkDoTaskPage()
            for self.page in category.articles():
                if self.page.namespace():
                    continue
                print
                try:
                    text = self.page.get()
                    self.code = mwparserfromhell.parse(text)
                except:
                    print "Skipping: Error loading page"                    
                for self.template in self.code.filter_templates():
                    if not self.template.name.lower().strip() in self.citationTemplates:
                        continue
                    try:
                        self.removeWikilinks()
                        self.fixEmptyCitations()
                        self.getURLFromArchive()
                        self.getArchiveDate()
                    except:
                        print "Skipping: Error encountered while processing"
                if text == self.code:
                    print "Skipping: No change was made"
                    continue
                pywikibot.showDiff(text, unicode(self.code))
                try:
                    self.page.put(unicode(self.code), "[[Wikipedia:Bots|Robot]]: Fixed [[Help:Citation Style 1|citation style]] errors")
                except:
                    print "Skipping: Could not save page"

def main():
    bot = CitationStyleRobot()
    bot.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
