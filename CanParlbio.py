#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Published by Hazard-SJ (https://www.wikidata.org/wiki/User:Hazard-SJ)
# under the terms of Creative Commons Attribution-ShareAlike 3.0 Unported (CC BY-SA 3.0)
# https://creativecommons.org/licenses/by-sa/3.0/

import pywikibot
import mwparserfromhell
import re

templatenames = [
    "Canadian Parliament links", "canadian Parliament links",
    "Parliament of Canada biography", "parliament of Canada biography",
    "Canparlbio", "canparlbio",
    "CanParlbio", "canParlbio",
    ]
templatenamesRE = "("
templatenamesRE += "|".join(templatenames)
templatenamesRE += ")"

site = pywikibot.getSite()
source = pywikibot.Page(site, "User:Bility/cleanup")
sourcetext = source.get()
lines = [line for line in sourcetext.splitlines()]
for line in lines:
    print
    page = pywikibot.Page(site, line[4:-2])
    print page.title()
    oldtext = page.get()
    newtext = oldtext
    #tags = re.findall("<ref.*?\{\{\s*%s.*?</ref>" % templatenamesRE, newtext, re.DOTALL|re.IGNORECASE)
    tags = re.findall("<ref.*?\{\{.*?</ref>", newtext, re.DOTALL|re.IGNORECASE)
    #print tags
    if not tags:
        print "No tags found"
        continue
    for tag in tags:
        code = mwparserfromhell.parse(tag)
        #print code
        templates = code.filter_templates()
        #print templates
        for template in templates:
            if template.name.strip().lower() in templatenames:
                if not template.has_param("nolist"):
                    print "Adding parameter"
                    template2 = template
                    template.add("nolist", "yes")
                    code.replace(template2,unicode(template))
                    newtext = re.sub(r.escape(tag),unicode(code),newtext)
                else:
                    print "Already has parameter"

        else:
            print "No change to text"
    if oldtext != newtext:
        pywikibot.showDiff(oldtext, newtext)
        save = raw_input("Save? [y/n]")
        if save.lower() == "y":
            page.put(newtext, comment="Added 'nolist' parameter per merge ([[Template_talk:CanParlbio#Merge_Template:MPLinksCA|discussion]])")
        else:
            print "Skipping"
    else:
        print "No diff"

pywikibot.stopme()
