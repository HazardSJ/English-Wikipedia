#!/usr/bin/python
# -*- coding: utf-8  -*-
import catlib, pagegenerators, wikipedia
import re

site = wikipedia.getSite()


gen_cat = catlib.Category(site, u"Category:Biography articles without listas parameter")
gen = pagegenerators.CategorizedPageGenerator(gen_cat)


def escape(pattern, exclude=[]):
    alphanum = {}
    for c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
        alphanum[c] = 1
    s = list(pattern)
    for i in range(len(pattern)):
        c = pattern[i]
        if c not in alphanum and c not in exclude:
            if c == "\000": s[i] = "\\000"
            else: s[i] = "\\" + c
    return pattern[:0].join(s)

def getBannerRegex():
    template = wikipedia.Page(site, u"Template:WikiProject Biography")
    redirects = template.getReferences(redirectsOnly=True)
    regex = u"\{\{ *(Template:)?(" + escape(template.titleWithoutNamespace(), exclude=[" "]).replace(" ", "( |_)")
    for page in redirects:
        regex += u"|" + escape(page.titleWithoutNamespace(), exclude=[" "]).replace(" ", "( |_)")
    regex += u")"
    return regex

def main():
    bannerRegex = getBannerRegex()
    for page in gen:
        # Distinguish between subject page and talk page
        if page.isTalkPage():
            talkpage = page
            page = page.toggleTalkPage()
        else:
            talkpage = page.toggleTalkPage()

        print
        print page
        
        # Skip if neither of the pages exist
        if not (page.exists() and talkpage.exists()):
            print u"Skipping: Nonexistent page"
            continue
        
        # Skip if either page is a redirect
        if page.isRedirectPage() or talkpage.isRedirectPage():
            print u"Skipping: Redirect page"
            continue

        # Get the text of the pages
        pagetext = page.get()
        talkpagetext = talkpage.get()

        # Skip if the WikiProject banner cannot be located on the talk page
        if not re.search(bannerRegex, talkpagetext, re.I):
            print u"Skipping: No WikiProject banner on talk page"
            continue

        key = None
        # Try to get a value to list as
        if re.search(u"\{\{DEFAULTSORT", pagetext, re.I|re.S):
            print u"{{DEFAULTSORT}} located"
            try:
                tmp = re.findall(u"\{\{DEFAULTSORT:.*?\}\}", pagetext, re.I|re.S)[0]
                key = re.sub(u"\{\{DEFAULTSORT:\s*(?P<key>.*?)\s*\}\}", u"\g<key>", tmp, re.I, re.S)
                del tmp
                DEFAULTSORT = True
                print u"Generated key from {{DEFAULTSORT}}:", key
            except:
                pass
        if not key:
            if re.search(u"\{\{lifetime\|.*?\|.*?\|.*?\}\}", pagetext, re.I|re.S):
                print u"{{Lifetime}} located"
                try:
                    tmp = re.findall(u"\{\{lifetime|.*?|.*?|.*?\}\}", pagetext, re.I|re.S)[0]
                    key = re.sub(u"\{\{lifetime\|.*?\|.*?\|\s*(?P<key>.*?)\s*\}\}", u"\g<key>", tmp, re.I, re.S)
                    del tmp
                    Lifetime = True
                    print u"Generated key from {{lifetime}}:", key
                except:
                    pass

        # If no key was found, skip to the next page
        if not key:
            print u"Skipping: Failed to attain a key"
            continue

        # Try to add key to the listas parameter of {{WikiProject Biography}} on the talk page
        oldtalkpagetext = talkpagetext
        talkpagetext = re.compile(u"(?P<before>.*%s.*?)(?P<after>\}\}.*)" % bannerRegex, re.I|re.S).sub(u"\g<before>|listas=%s\n\g<after>" % key, talkpagetext)
        if oldtalkpagetext != talkpagetext:
            try:
                summary = u"[[Wikipedia:Bots|Bot]]: Adding listas parameter"
                if DEFAULTSORT:
                    summary += u" (attained \"%s\" from {{DEFAULTSORT}})" % key
                elif Lifetime:
                    summary += u" (attained \"%s\" from {{lifetime}})" % key
                #talkpage.put(talkpagetext, comment=summary)
                print summary
            except:
                print u"Could not save page"
        else:
            print u"Key was not added"

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
