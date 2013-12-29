import urllib
import urllib2
import string
import sys
import re
import sqlite3
import codecs
import datetime
from math import sqrt
conn = sqlite3.connect('blogs.db')
conn.text_factory = str
from BeautifulSoup import BeautifulSoup

#remote path
path = "."
#debug path
#path= ""

current_blogs = []

c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS blogs (id INTEGER primary key autoincrement,hot TEXT,title TEXT,link TEXT,author TEXT,comments TEXT,views TEXT,last TEXT,last_poster TEXT,date_added DATETIME DEFAULT CURRENT_TIMESTAMP)''')
c.execute('''CREATE TABLE IF NOT EXISTS featured (id INTEGER primary key autoincrement,link TEXT,date_added DATETIME DEFAULT CURRENT_TIMESTAMP)''')
c.execute('''CREATE TABLE IF NOT EXISTS latest (id INTEGER primary key autoincrement,link TEXT,date_added DATETIME DEFAULT CURRENT_TIMESTAMP)''')
c.execute('''CREATE TABLE IF NOT EXISTS rssPos (title TEXT,link TEXT primary key,desc TEXT,date_added DATETIME DEFAULT CURRENT_TIMESTAMP)''')
c.execute('''CREATE TABLE IF NOT EXISTS rssUpDown (title TEXT,link TEXT primary key,desc TEXT,date_added DATETIME DEFAULT CURRENT_TIMESTAMP)''')


#############
###
###		COLLECTION PART
###
###
#############
def scrapeTL():
	#print 'first page of blogs...'
	#user_agent = 'Mozilla/5 (Solaris 10) Gecko'
	user_agent = 'Mozilla/5 (Solaris 10) Gecko'
	headers = { 'User-Agent' : user_agent }
	values = {}
	data = urllib.urlencode(values)
	request = urllib2.Request("http://www.teamliquid.net/forum/index.php?show_part=18",data,headers)
	response = urllib2.urlopen(request)
	the_page = response.read()
	pool = BeautifulSoup(the_page)
	results = pool.findAll('td', attrs={'class' :re.compile('^forumindex')})
	# <td class="forumindex lichtb" height="25"><img width="14" height="11" src="/images/regular.png" alt="[_]" /></td>
	# <td class="forumindex lichtb"><a href="/blogs/viewblog.php?topic_id=330224" title="">Best way to change race?</a> <a class="lastPage nounderline" href="/blogs/viewblog.php?topic_id=330224&amp;currentpage=2" style="font-size:9pt; color:#797979" title="Jump to the last page">&gt;</a></td>
	# <td class="forumindex lichtb">MannerMan</td>
	# <td class="forumindex lichtb">22</td>
	# <td class="forumindex lichtb">568</td>
	# <td class="forumindex lichtb">10:56 Apr 21 2012<br />airtown</td>
	item = 0
	hot = "<ERROR>"
	title = "<ERROR>"
	link = "<ERROR>"
	author = "<ERROR>"
	comments = 0
	views = 0
	last = "<ERROR>"
	last_poster = "<ERROR>"
	for result in results:
		if(item == 0): #hot or not
			if str(result).find('hot.png') != -1:
				hot = "hot"
			else:
				hot = "regular"
		elif(item == 1): #link + title
			tlink = result.find('a')
			title = tlink.text
			link  = 'http://teamliquid.net' + str(tlink['href'])
		elif(item == 2): #author
			author = result.text
		elif(item == 3): #comments
			comments = int(result.text)
		elif(item == 4): #views
			views = int(result.text)
		elif(item == 5): #last comment
			last = str(result)[str(result).find('>')+1:str(result).find('<br />')]
			last_poster = str(result)[str(result).find('<br />')+6:str(result).rfind('<')]
		item += 1
		if(item == 6): #reset counter, add blog to database and current blogs for relevance ranking
			c.execute("INSERT INTO blogs (hot,title,link,author,comments,views,last,last_poster) VALUES (?,?,?,?,?,?,?,?)",(hot,title,link,author,comments,views,last,last_poster))
			current_blogs.append([0.000,{"hot":hot,"title":title,"link":link,"author":author,"comments":comments,"views":views,"last":last,"last_poster":last_poster}])
			conn.commit()
			item = 0


	#print 'featured blogs...'
	results = pool.find('tbody', attrs={'id':'sidebar91'})  #featured blogs
	results = results.findAll('a')
	for r in results:
		try:
			t = r['title']
			link = 'http://teamliquid.net' + str(r['href'])
			c.execute("INSERT INTO featured (link) VALUES (?)",(link,))
			conn.commit()
		except KeyError:
			pass

	#print 'latest blogs...'
	results = pool.find('tbody', attrs={'id':'sidebar91'})  #latest blogs
	results = results.findAll('a')
	for r in results:
		try:
			t = r['title']
			link = r['href']
			c.execute("INSERT INTO latest (link) VALUES (?)",(link,))
			conn.commit()
		except KeyError:
			pass


	#c.close()

#############
###
###   CALCULATION PART
###
###
#############
def _confidence(ups, downs):
    n = ups + downs
    if n == 0:return 0
    z = 1.6 #1.0 = 85%, 1.6 = 95%
    phat = float(ups) / n
    return sqrt(phat+z*z/(2*n)-z*((phat*(1-phat)+z*z/(4*n))/n))/(1+z*z/n)

def confidence(ups, downs):
    if ups + downs == 0:return 0
    else:return _confidence(ups, downs)

def calcBlogsPos():
	"""Calculate the best blogs of the moment, assumes no downvotes and comments are worth more than views"""
	for rank in current_blogs:
		blog = rank[1]
		rank[0] = confidence((blog['comments']*10)+blog['views'],0)
	current_blogs.sort()
	current_blogs.reverse()
	#RSS update
	for item in current_blogs[:10]:
		c.execute("INSERT OR IGNORE INTO rssPos (title,link,desc) VALUES (?,?,?)",(item[1]['title'],item[1]['link'],"by " + item[1]['author']))
		conn.commit()
	#debug printing:
	# print "------------------------Regular Ranking"
	# for item in current_blogs[:5]:
	# 	print str(item[0]) +'\t' + item[1]['title'] + '\t' + str(item[1]['comments'])+'|'+str(item[1]['views'])


def calcBlogsUpAndDown():
	"""Calculate the best blogs of the moment, consider a view without a comment a minor downvote"""
	for rank in current_blogs:
		blog = rank[1]
		rank[0] = confidence(blog['comments'],blog['views']/100)
	current_blogs.sort()
	current_blogs.reverse()
	#RSS update
	for item in current_blogs[:10]:
		c.execute("INSERT OR IGNORE INTO rssUpDown (title,link,desc) VALUES (?,?,?)",(item[1]['title'],item[1]['link'],"by " + item[1]['author']))
		conn.commit()
	#debug printing:
	# print "------------------------Up And Down Ranking"
	# 	for item in current_blogs[:5]:
	# 		print str(item[0]) +'\t'+ item[1]['title'] + '\t' + str(item[1]['comments'])+'|'+str(item[1]['views'])


def genHTML():
	"""Generate HTML for site"""
	webout = codecs.open(path + "index.html","w", "utf-8")
	webout.write("<!DOCTYPE html>\n")
	webout.write("<html>\n")
	webout.write("	<head>\n")
	webout.write("	<style type='text/css'>\n")
	webout.write("		h1 {background-color: #325080;color:white;text-align:center;padding-top:0px;margin-top:0px;}\n")
	webout.write("		a{color:black;}\n")
	webout.write("		table{color: #0D124B;width:800px;}\n")
	webout.write("		body {background-color: #D9DDE0;font:10pt Arial;margin:50px 0px; padding:0px;text-align:center;}\n")
	webout.write("		#content {width:800px;margin:0px auto;text-align:left;padding:15px;}\n")
	webout.write("		.light{background-color: #D9DDE0;}\n")
	webout.write("		.dark{background-color: #B3BFD1;}\n")
	webout.write("	</style>\n")
	webout.write("		<script type='text/javascript'>var _gaq = _gaq || [];_gaq.push(['_setAccount', 'UA-18046844-1']);_gaq.push(['_setDomainName', 'ultimatehurl.com']);_gaq.push(['_trackPageview']);(function() {var ga = document.createElement('script'); ga.type = 'text/javascript';ga.async = true;ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);})();</script>")
	webout.write("		<title>TeamLiquid Blogs of the Moment</title>\n")
	webout.write("	</head>\n")
	webout.write("	<body><div id='content'>\n")
	webout.write("		<h1>TeamLiquid Blogs of the Moment</h1>\n")
	webout.write("		<h3>Indexing blogs from the definitive Starcraft 2 site <a href='http://teamliquid.net'>TeamLiquid.net</a></h3>\n")
	webout.write("		<table>\n")
	webout.write("			<tr><th>Ranking Method One <a href='rssOne.xml'>(Subscribe via RSS)</a></th></tr>\n")
	calcBlogsUpAndDown()
	webout.write("			<tr><th>Title</th><th>Author</th><th>Comments</th><th>Views</th><th>Last</th></tr>\n")
	light = True
	for item in current_blogs[:10]:
		webout.write("			<tr class='"+("dark", "light")[light]+"'><td><a href='"+item[1]['link']+"'>"+item[1]['title']+"</a></td><td>"+item[1]['author']+"</td><td>"+str(item[1]['comments'])+"</td><td>"+str(item[1]['views'])+"</td><td>"+item[1]['last']+"<br />"+item[1]['last_poster']+"</td></tr>\n")
		light =  not light
	webout.write("		</table>\n")
	webout.write("		<br/><br/><br/><table>\n")
	webout.write("			<tr><th>Ranking Method Two <a href='rssTwo.xml'>(Subscribe via RSS)</a></th></tr>\n")
	calcBlogsPos()
	webout.write("			<tr><th>Title</th><th>Author</th><th>Comments</th><th>Views</th><th>Last</th></tr>\n")
	light = True
	for item in current_blogs[:10]:
		webout.write("			<tr class='"+("dark", "light")[light]+"'><td><a href='"+item[1]['link']+"'>"+item[1]['title']+"</a></td><td>"+item[1]['author']+"</td><td>"+str(item[1]['comments'])+"</td><td>"+str(item[1]['views'])+"</td><td>"+item[1]['last']+"<br />"+item[1]['last_poster']+"</td></tr>\n")
		light = not light
	webout.write("		</table><h4>Generated at "+str(datetime.datetime.now())+". Created by <a href='http://twitter.com/UltimateHurl'>UltimateHurl</a>, <a href='http://www.teamliquid.net/forum/profile.php?user=UltimateHurl'>my TL</a> and <a href='http://ultimatehurl.com'>my site</a></h4></div>\n")
	webout.write("	</body>\n")
	webout.write("</html>")

def genRSS():
	#rssUpDown
	rssout = codecs.open(path + "rssOne.xml","w", "utf-8")
	rssout.write("<rss version=\"2.0\">\n")
	rssout.write("	<channel>\n")
	rssout.write("	<title>Team Liquid Blogs of the Moment (rank method one)</title>\n")
	rssout.write("	<link>http://www.ultimatehurl.com/liquidblogs</link>\n")
	rssout.write("	<description>The best recent blogs from TeamLiquid.net</description>\n")
	rssout.write("	<lastBuildDate>"+str(datetime.datetime.utcnow())+"</lastBuildDate>\n")
	c.execute("SELECT title,link,desc,date_added FROM rssUpDown ORDER BY date_added DESC LIMIT 10")
	for item in c:
		rssout.write("<item>\n")
		rssout.write("	<title>"+str(item[0])+"</title>\n")
		rssout.write("		<link>\n")
		rssout.write("			"+str(item[1])+"\n")
		rssout.write("		</link>\n")
		rssout.write("		<description>"+str(item[2])+"</description>\n")
		rssout.write("		<guid isPermaLink=\"true\">\n")
		rssout.write("			"+str(item[1])+"\n")
		rssout.write("		</guid>\n")
		rssout.write("		<pubDate>"+str(item[3])+"</pubDate>\n")
		rssout.write("	</item>\n")
	rssout.write("	</channel>\n")
	rssout.write("</rss>")

	#rssPos
	rssout = codecs.open(path + "rssTwo.xml","w", "utf-8")
	rssout.write("<rss version=\"2.0\">\n")
	rssout.write("	<channel>\n")
	rssout.write("	<title>Team Liquid Blogs of the Moment (rank method two)</title>\n")
	rssout.write("	<link>http://www.ultimatehurl.com/liquidblogs</link>\n")
	rssout.write("	<description>The best recent blogs from TeamLiquid.net</description>\n")
	rssout.write("	<lastBuildDate>"+str(datetime.datetime.utcnow())+"</lastBuildDate>\n")
	c.execute("SELECT title,link,desc,date_added FROM rssPos ORDER BY date_added DESC LIMIT 10")
	for item in c:
		rssout.write("<item>\n")
		rssout.write("	<title>"+str(item[0])+"</title>\n")
		rssout.write("		<link>\n")
		rssout.write("			"+str(item[1])+"\n")
		rssout.write("		</link>\n")
		rssout.write("		<description>"+str(item[2])+"</description>\n")
		rssout.write("		<guid isPermaLink=\"true\">\n")
		rssout.write("			"+str(item[1])+"\n")
		rssout.write("		</guid>\n")
		rssout.write("		<pubDate>"+str(item[3])+"</pubDate>\n")
		rssout.write("	</item>\n")
	rssout.write("	</channel>\n")
	rssout.write("</rss>")

if __name__ == '__main__':
	scrapeTL()
	genHTML()
	genRSS()
