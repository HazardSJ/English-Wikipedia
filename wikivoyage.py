#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Published by Hazard-SJ (https://wikitech.wikimedia.org/wiki/User:Hazard-SJ)
# under the terms of Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)
# https://creativecommons.org/licenses/by-sa/3.0/

from __future__ import unicode_literals

import mwparserfromhell

import config
from cosmetic_changes import CosmeticChangesToolkit
import pywikibot
import xmlreader

config.usernames["wikipedia"]["en"] = "Hazard-Bot"

class WikivoyageBot(object):
    def __init__(self):
        self.wikipedia = pywikibot.Site("en", "wikipedia")
        self.wikivoyage = pywikibot.Site("en", "wikivoyage")
        self.doTaskPage = pywikibot.Page(self.wikipedia, "User:Hazard-Bot/DoTask/Wikivoyage")
        self.dumpFile = "/public/datasets/public/enwikivoyage/20130528/enwikivoyage-20130528-pages-articles.xml.bz2"
        self.templates = {
            "sister": self.getAllTitles("Template:Sister project links"),
            "wikivoyage": self.getAllTitles("Template:Wikivoyage")
        }
        self.templates["wikivoyage"].extend(self.getAllTitles("Template:Wikivoyage-inline"))
        self.cosmeticChanges = CosmeticChangesToolkit(self.wikipedia)

    def checkDoTaskPage(self):
        try:
           text = self.doTaskPage.get(force = True)
        except pywikibot.IsRedirectPage:
            raise Warning(
                "The 'do-task page' (%s) is a redirect."
                % self.doTaskPage.title(asLink = True)
            )
        except pywikibot.NoPage:
            raise Warning(
                "The 'do-task page' (%s) does not exist."
                % self.doTaskPage.title(asLink = True)
            )
        else:
            if text.strip().lower() == "true":
                return True
            else:
                raise Exception(
                    "The task has been disabled from the 'do-task page' (%s)."
                    % self.doTaskPage.title(asLink = True)
                )

    def getAllTitles(self, template):
        page = pywikibot.Page(self.wikipedia, template)
        if page.isRedirectPage():
            page = page.getRedirectTarget()
        titles = [page.title(withNamespace = False).lower()]
        redirects = page.getReferences(redirectsOnly = True)
        for redirect in redirects:
            titles.append(redirect.title(withNamespace = False).lower())
        return titles

    def parseDump(self):
        dump = xmlreader.XmlDump(self.dumpFile)
        gen = dump.parse()
        for page in gen:
            if page.ns != "0":
                continue
            voyTitle = page.title
            code = mwparserfromhell.parse(page.text)
            links = code.filter_wikilinks()
            for link in links:
                if not link.title.lower().strip().startswith("wikipedia"):
                    continue
                wpTitle = pywikibot.Page(
                    self.wikipedia,
                    unicode(link.title)
                ).title(withNamespace = False)
                yield wpTitle, voyTitle

    def run(self):
        gen = self.parseDump()
        for wpTitle, voyTitle in gen:
            print
            wpPage = pywikibot.Page(self.wikipedia, wpTitle)
            voyPage = pywikibot.Page(self.wikivoyage, voyTitle)
            if not (wpPage.exists() and voyPage.exists()):
                continue
            if wpPage.isRedirectPage():
                wpPage = wpPage.getRedirectTarget()
            print wpPage.title(), voyPage.title()
            text = wpPage.get()
            code = mwparserfromhell.parse(text)
            skip = False
            hasvoy = False
            hassister = False
            voyinsister = False
            for template in code.filter_templates():
                if template.name.lower().strip() in self.templates["wikivoyage"]:
                    hasvoy = True
                    break
                if template.name.lower().strip() in self.templates["sister"]:
                    hassister = True
                    if template.has_param("voy"):
                        voyinsister = True
                        break
            if hasvoy:
                print "Skipping: Already has Wikivoyage template"
            elif voyinsister:
                print "Skipping: Already has a Wikivoyage link in sister project template"
            if hasvoy or voyinsister:
                continue
            if hassister:
                for template in code.filter_templates():
                    if template.name.lower().strip() in self.templates["sister"]:
                        template.add("voy", voyPage.title())
                        break
            else:
                voyTemplate = "\n{{Wikivoyage|%s}}" % voyPage.title()
                externalLinksHeading = None
                lastSectionText = None
                for node in code.nodes:
                    if isinstance(node, mwparserfromhell.nodes.heading.Heading):
                        if ("external" in node.lower()) or ("links" in node.lower()):
                            externalLinksHeading = node
                            break
                    if isinstance(node, mwparserfromhell.nodes.text.Text):
                        lastSectionText = node
                if externalLinksHeading:
                    code.insert_after(externalLinksHeading, voyTemplate)
                elif lastSectionText:
                    code.insert_after(
                        lastSectionText,
                        "\n== External links ==%s\n" % voyTemplate
                    )
                    code = mwparserfromhell.parse(
                        self.cosmeticChanges.standardizePageFooter(
                            unicode(code)
                        )
                    )
                else:
                    print "Skipping: Could not insert template"
            wpPageCats = [category.title() for category in wpPage.categories(api = True)]
            if "Category:All article disambiguation pages" in wpPageCats:
                print "Skipping: Disambiguation page"
                continue
            if text != code:
                pywikibot.showDiff(text, unicode(code))
                try:
                    wpPage.put(
                        unicode(code),
                        comment = "[[Wikipedia:Bots|Robot]]: Added link to Wikivoyage"
                    )
                except:
                    print "Skipping: Could not save changes"
            else:
                print "Skipping: No changes made"


def main():
    bot = WikivoyageBot()
    bot.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
