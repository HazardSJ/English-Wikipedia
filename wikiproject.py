# -*- coding: utf-8 -*-
## EarwigBot
## WikiProject tagging
## v2.0
##
## Written by The Earwig, (c) 2009 - 2010 <http://en.wikipedia.org/wiki/User:The_Earwig>
##
### Permission is hereby granted, free of charge, to any person obtaining a copy
### of this software and associated documentation files (the "Software"), to deal
### in the Software without restriction, including without limitation the rights to
### use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
### of the Software, and to permit persons to whom the Software is furnished to do
### so, subject to the following conditions:
##
### The above copyright notice and this permission notice shall be included in all
### copies or substantial portions of the Software.
## 
### THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
### IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
### FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
### AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
### LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
### OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
### SOFTWARE.
##
### Edited by Hazard-SJ, (c) 2011 - 2012 <https://en.wikipedia.org/wiki/User:Hazard-SJ>

import traceback, codecs, string, urllib, re
import wikipedia, catlib

topTemps = ["\{\{(s|S)kip[ _]?to[ _]?toc[ _]?(talk)?\}\}", "\{\{(c|C)ommunity[ _]article[ _]probation\}\}", "\{\{(c|C)ensor\}\}", "\{\{[bB][lL][pP][oO]\}\}",
"\{\{[bB][lL][pP]\}\}", "\{\{(t|T)alk[ _]?(header|page)\}\}", "\{\{(n|N)ot[ _]?a[ _]?forum\}\}", "\{\{(r|R)ecurring[ _]?(t|T)hemes\}\}", "\{\{[fF][aA][qQ]\}\}",
"\{\{(r|R)ound[ _]?(i|I)n[ _]?(c|C)ircles\}\}", "\{\{(a|A)rticle[ _]?(h|H)istory(.*?)\}\}", "\{\{(f|F)ailed[ _]?(g|G)(a|A)}}", "\{\{(o|O)ld[ _]?[pP][rR][oO][dD](.*?)\}\}"
"\{\{(o|O)ld[ _]?[aA][fF][dD](.*?)\}\}", "\{\{(w|W)((iki(p|P)roject)|(p|P))[ _]?(B|b)(i|I)(o|O)(.*?)\}\}"] # All templates that should go above the banner.

def main():
	print "EarwigBot\nWikiProject tagging\nv2.0\n"
	shutoffcheck()
	site = wikipedia.getSite()
	print "Allowed methods of page input:\n   1: through a category\n   2: through a file containing categories\n   3: through a file containing pages\n"
	method = raw_input("Choose: ")
	namespaces = [input("Namespaces to work in (as list; subject spaces only; use '*' to denote all): ")]
	pages = getPages(method, namespaces, site)
	if not pages:
		print "Could not get a list of pages."
		exit()
	banner = raw_input("Banner template to add: ")
	bannerRe = bannerRegex(site, banner)
	autoassess = input("Autoassess for this banner? (True/False): ")
	noexist = input("Process nonexistant pages? (True/False): ")
	append = raw_input("Text to append to end of banner (e.g., importance, living): ")
	summary = "[[WP:BOT|Bot]]: Adding WikiProject banner (WikiProject " + raw_input("WikiProject: ") + "); [[User:Hazard-Bot/Requests|you can request too]]"
	counter = 1
	for page in pages:
		edited = process(site, page, banner, bannerRe, autoassess, noexist, append, summary)
		if edited: counter += 1
		if not counter % 11: # Check shutoff every ten edits.
			counter = 1
			shutoffcheck()

def process(site, page, banner, bannerRe, autoassess, noexist, append, summary):
	print u"\nProcessing page [[%s]]:" % page.title()
	exists = True
	try:
		text = page.get()
	except wikipedia.NoPage:
		exists = False
		print "Page does not exist."
		if not noexist:
			return False
		text = ""
	except wikipedia.IsRedirectPage:
		exists = False
		print "Page is a redirect."
		if not noexist:
			return False
		text = ""
	if re.search(bannerRe + ")(.*?)\}\}", text, re.DOTALL):
		print "Banner is already on page; skipping."
		return False
	if autoassess:
		assessment = getAssessment(site, page)
		print "Assessment for article is %s." % assessment
	else: assessment = False
	theStuff = formulate(banner, assessment, append)
	if re.search("\{\{((w|W)((ikiProject ?Banner ?(s|S)(hell)?)|((p|P)(b|B)(s|S)?)))\s*\|", text, re.DOTALL):
		print "Page uses a banner shell; adding banner inside shell."
		newtext = addBanner(text, theStuff, shell=True)
	else:
		print "Page does not use a banner shell; adding banner."
		newtext = addBanner(text, theStuff, shell=False)
	print "New text generated."
	if exists:
		splits = string.split(newtext, "\n")
		for line in splits:
			if line.startswith(banner[:-2]):
				print "Added on line %s." % splits.index(line)
				if splits.index(line):
					print "prev: " + splits[splits.index(line) - 1]
				try:
					print "next: " + splits[splits.index(line) + 1]
				except IndexError: pass
	wikipedia.showDiff(text, newtext)
	page.put(newtext, comment=summary)
	return True

def getAssessment(site, page): # Get assessment for a page.
	try:
		text = page.get()
	except (wikipedia.NoPage, wikipedia.IsRedirectPage):
		return False
	classes = {"FA":0, "FL":0, "GA":0, "A":0, "B":0, "C":0, "start":0, "stub":0, "list":0, "dab":0}
	for assess in classes.iterkeys():
		if re.search("\{\{(.*?)class\s*=\s*%s(.*?)\}\}" % assess, text, re.S|re.I):
			classes[assess] += 1
	maximum = max(classes.itervalues())
	if not maximum:
		return False
	for c in classes.iterkeys():
		if classes[c] == maximum:
			return c
	return False

def addBanner(text, banner, shell=False): # Add BANNER to TEXT inside of SHELL iff SHELL is specified.
	if shell: # Really trivial, just add at the beginning of the shell
		match = re.findall("(\{\{((w|W)((ikiProject ?Banner ?(s|S)(hell)?)|((p|P)(b|B)(s|S)?)))(.*?)\|1=)", text, re.DOTALL)
		if not match: # Something is seriously wrong.
			print "Something is seriously wrong."
			return text
		testMe = re.search(topTemps[-1], text, re.DOTALL)
		if testMe:
			newtext = text.replace(testMe.group(), testMe.group() + "\n" + banner)
		else:
			newtext = text.replace(match[0][0], match[0][0] + "\n" + banner)
	else:
		temptext = "BHOLDER" + text
		for temp in topTemps: 
			if re.search(temp, text, re.DOTALL):
				print "Found match for: %s" % temp
				temptext = temptext.replace("BHOLDER", "")
				t = re.findall("(%s)" % temp, temptext, re.DOTALL)[0][0]
				temptext = temptext.replace(t, t + "BHOLDER")
		if temptext.startswith("BHOLDER"):
			newtext = temptext.replace("BHOLDER", banner + "\n")
		else:
			newtext = temptext.replace("BHOLDER", "\n" + banner)
	newtext = genfixes(newtext)
	return newtext

def genfixes(newtext):
	newtext = re.sub("\{\{(t|T)alk[ _](header|page)\}\}", "{{\\1alk header}}", newtext)
	newtext = re.sub("\{\{(s|S)kiptotoc(talk)?\}\}", "{{\\1kip to talk}}", newtext)
	newtext = re.sub("(?i)\{\{(unsign?(ed3?)?|signed|uns|nosign|Tidle|Forgot to sign)(.*?)\}\}", "{{subst:Unsigned\\3}}", newtext)
	return newtext

def formulate(banner, assessment, append): # Input is some elements of the banner, output is the banner itself with any assessments or appends factored in.
	banner = banner[:-2] # Trim ending }}s.
	if assessment: # If we're adding an assessment...
		banner += "|class=%s" % assessment # Add, with assessment inside of class.
	if append: # If we're appending something to the end of the banner, such as an inportance ranking...
		banner += append # Need I explain?
	banner += "}}" # Close banner.
	return banner

def bannerRegex(site, banner): # Get regex for template based on template redirects.
	template = wikipedia.Page(site, "Template:" + banner[2:-2])
	redirects = template.getReferences(redirectsOnly=True)
	regex = "\{\{(" + escape(template.titleWithoutNamespace(), exclude=[" "]).replace(" ", "( |_)")
	for page in redirects:
		regex += "|" + escape(page.titleWithoutNamespace(), exclude=[" "]).replace(" ", "( |_)")
	return regex

def escape(pattern, exclude=[]): # Stolen from re.escape(), includes "exclude" var now.
	alphanum = {}
	for c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789':
		alphanum[c] = 1
	s = list(pattern)
	for i in range(len(pattern)):
		c = pattern[i]
		if c not in alphanum and c not in exclude:
			if c == "\000": s[i] = "\\000"
			else: s[i] = "\\" + c
	return pattern[:0].join(s)

def getPages(method, namespaces, site): # Get the list of pages to work with, based on user input.
	if method == '1': # through a category
		categoryname = raw_input("Category: ")
		if "[[" in categoryname:
				categoryname = categoryname[2:-2] # Exclude [[s and ]]s.
		if not categoryname.startswith("Category:"):
			categoryname = "Category:" + categoryname
		recurse = input("Recurse? Can be True, False, or an integral level: ")
		pages = []
		tempPages = pagesInCat(site, categoryname, recurse=recurse)
		for tempPage in tempPages:
			if tempPage.isTalkPage(): # If it's a talk page, KEEP the variable, but get the namespace for the subject page.
				namespace = tempPage.toggleTalkPage().namespace()
			else: # If it's a subject page, CHANGE the variable TO A TALK PAGE but get the namespace for the current page.
				namespace = tempPage.namespace()
				tempPage = tempPage.toggleTalkPage()
                        if namespace != 3:
				if namespaces != ['*']:
                                	if (namespace in namespaces) and (tempPage not in pages):
                                		pages.append(tempPage)
                		else:
                        		if tempPage not in pages:
                                		pages.append(tempPage)
	elif method == '2': # through a file containing categories
		filename = raw_input("File listing categories: ")
		recurse = input("Recurse for each individual category? Can be True, False, or an integral level: ")
		try:
			f = codecs.open(filename, 'r', 'utf-8')
			list = f.read()
			f.close()
		except Exception:
			traceback.print_exc()
			print "Error, stopping."
			exit()
		cats = string.split(list, "\n")
		pages = []
		print "List of cats loaded; getting list of pages.\n"
		for cat in cats:
			if not cat: continue # Whitespace
			if "[[" in cat:
				cat = cat[2:-2] # Exclude [[s and ]]s.
			if not cat.startswith("Category:"):
				cat = "Category:" + cat
			tempPages = pagesInCat(site, cat, recurse=recurse)
			for tempPage in tempPages:
				if tempPage.isTalkPage(): # If it's a talk page, KEEP the variable, but get the namespace for the subject page.
					namespace = tempPage.toggleTalkPage().namespace()
				else: # If it's a subject page, CHANGE the variable TO A TALK PAGE but get the namespace for the current page.
					namespace = tempPage.namespace()
					tempPage = tempPage.toggleTalkPage()
				if namespace != 3:
                                	if namespaces != ['*']:
                                        	if (namespace in namespaces) and (tempPage not in pages):
                                                	pages.append(tempPage)
                                        else:
                                        	if tempPage not in pages:
                                                	pages.append(tempPage)
	elif method == '3': # through a file containing pages
		filename = raw_input("File name: ")
		try:
			f = codecs.open(filename, 'r', 'utf-8')
			list = f.read()
			f.close()
		except Exception:
			traceback.print_exc()
			print "Error, stopping."
			exit()
		print "File data loaded."
		pages = []
		pgs = string.split(list, "\n")
		for pg in pgs:
			if not pg: continue # Whitespace
			if "[[" in pg:
				pg = pg[2:-2] # Exclude [[s and ]]s.
			page = wikipedia.Page(site, pg)
			if page.isTalkPage(): # If it's a talk page, KEEP the variable, but get the namespace for the subject page.
				namespace = page.toggleTalkPage().namespace()
			else: # If it's a subject page, CHANGE the variable TO A TALK PAGE but get the namespace for the current page.
				namespace = page.namespace()
				page = page.toggleTalkPage()
			if namespace != 3:
                                if namespaces != ['*']:
                                	if (namespace in namespaces) and (page not in pages):
                                		pages.append(page)
                                else:
                                        if page not in pages:
                                                pages.append(page)
	else:
		print "Page input method is not supported. Aborting."
		exit()
	pages.sort()
	print "List of pages loaded. %s pages found.\n" % len(pages)
	return pages

def pagesInCat(site, categoryname, recurse): # Return pages in this category as a list, or die.
	try:
		category = catlib.Category(site, categoryname)
		pages = category.articlesList(recurse=recurse)
	except Exception:
		traceback.print_exc()
		print "Error, stopping."
		exit()
	return pages

def shutoffcheck():
	site = wikipedia.getSite()
	pagename = "User:Hazard-Bot/Check/Wikiproject"
	page = wikipedia.Page(site, pagename)
	print "Checking [[" + pagename + "]]for emergency shutoff."
	text = page.get()
	if text.lower() != 'enable':
		print "Emergency shutoff enabled; stopping."
		wikipedia.stopme()
		exit()
	print "Emergency shutoff disabled; continuing."

if __name__ == "__main__":
	try:
		main()
	finally:
		wikipedia.stopme()
