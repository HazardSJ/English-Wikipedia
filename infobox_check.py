#!/usr/bin/python
# -*- coding: utf-8  -*-

import wikipedia as pywikibot
import catlib, re


site = pywikibot.getSite()

category = catlib.Category(site, "Category:Amusement parks")

#storage = "Wikipedia:WikiProject Amusement Parks/Need infoboxes"
storage = "User:Hazard-SJ/Sandbox"
storage = pywikibot.Page(site, storage)

limit = 500

def main():
    pages = []
    for page in category.articles(recurse=True):
        if (page.namespace() != 0) or page.isRedirectPage() or (page in pages):
            continue
        if page.title().startswith("List of"):
            continue
        wikicode = page.get()
        instances = re.findall("\{\{ *infobox", wikicode, re.I)
        if len(instances) == 0:
            pages.append(page)
        if len(pages) >= limit:
            break
        else:
            print len(pages), "pages currently;", limit - len(pages), "pages to go."
    print "Limit (%i) reached; preparing to update list." % limit
    pages.sort()
    text = "Update as of ~~~~~:\n"
    for page in pages:
        text += "# [[%s]]\n" % page.title()
    storage.put(text, minorEdit=False, comment="Bot: Updating list of pages without infoboxes")
    print "Update complete."
    return

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
