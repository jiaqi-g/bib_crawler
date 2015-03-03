
from bs4 import BeautifulSoup
import re
import urllib
import urllib2
from urllib2 import Request
import httplib
import json
import datetime, time

class Crawler:
	def __init__(self, host, logFile=None):
		# global settings
		self.host = host
		if logFile != None:
			self.logFile = open(logFile, 'w')
		else:
			self.logFile = None

	def close(self):
		if self.logFile != '':
			self.logFile.close()

	def makeRequest(self, url, query, retries=10):
		if retries < 0:
			raise Exception('Cannot connect to server!')
		params = urllib.urlencode({'q':query})
		# create and send HTTP request
		req_url = url + '?' + params
		req = httplib.HTTPConnection(self.host)
		req.putrequest("GET", req_url)
		req.putheader("Host", self.host)
		req.endheaders()
		req.send('')
		# get response and print out status
		self.resp = req.getresponse()
		self.log(str(self.resp.status) + str(self.resp.reason))
		if self.resp.status != 200:
			self.log('redo!')
			self.makeRequest(query, retries-1)
		return self.resp

	def log(self, s):
		if self.logFile != None:
			self.logFile.write(s + '\n')
		else:
			print(s)

class BibPage:
	pass

class ResultPage:
	def __init__(self, html):
		self.html = html

	def getLink(self, tag):
		soup = BeautifulSoup(self.html)
		lst = map(lambda x: x.get('href', '/'), soup.find_all('a'))
		lst = filter(lambda x: tag in x, lst)
		s = list(set(lst))

		if len(s) == 1:
			return Link(s[0])
		else:
			raise Exception()

class Link:
	def __init__(self, url):
		self.url = url

	def requestContent(self, tag='pre'):
		soup = BeautifulSoup(urllib2.urlopen(Request(self.url)).read())
		return soup.find_all(tag)[0].contents[0]

class DblpCrawler:
	def __init__(self):
		self.crawler = Crawler('dblp.uni-trier.de')

	def search(self, query):
		return ResultPage(self.crawler.makeRequest('/search', query))

########################

def main():
	USAGE = """

	USAGE: main.py [-s <query-source>] SOURCE DEST
		--help
			Displays input options
		-s, --source <query-source>
			(Optional)Provide source to crawl bib data, dblp or google
		SOURCE
			Input file of a paper keywords list
		DEST
			Output bib file
	"""

	source = 'in.txt'
	dest = 'output.bib'
	crawler = DblpCrawler()

	comments = ['\n% \\bibliography{mybib}{}', '\\bibliographystyle{plain}\n']
	contents = []

	with open(source) as f:
		lines = f.readlines()
		for line in lines:
			keywords = line.strip()
			try:
				if len(keywords) > 0:
					content = crawler.search(keywords).getLink('bibtex').requestContent()
					keywords = '_'.join(keywords.split(' '))
					comments.append('\cite{' + keywords + '}')
					contents.append(re.sub('(?<={).+', keywords +',', content, count=1))
			except Exception, e:
				print 'More than one entry found for keywords: ' + keywords

	with open(dest, 'w') as o:
		o.write("\n% ".join(comments))
		o.write("\n")
		o.write("\n".join(contents))

main()
