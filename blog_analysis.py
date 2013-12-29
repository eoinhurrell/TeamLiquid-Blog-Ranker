import sqlite3 as lite
con = lite.connect('blogs.db')
cur = con.cursor()    
cur.execute('CREATE TEMP VIEW unique_blogs AS SELECT * FROM blogs GROUP BY title')
cur.execute('CREATE TEMP VIEW featured_blogs AS SELECT DISTINCT unique_blogs.title AS title,unique_blogs.link AS link,unique_blogs.views AS views,unique_blogs.comments AS comments FROM unique_blogs,featured WHERE unique_blogs.link == featured.link')
cur.execute('CREATE TEMP VIEW reg_blogs AS SELECT DISTINCT unique_blogs.title AS title,unique_blogs.link AS link,unique_blogs.views AS views,unique_blogs.comments AS comments FROM unique_blogs WHERE NOT EXISTS (SELECT 1 FROM featured_blogs WHERE featured_blogs.link = unique_blogs.link)')

# data = cur.fetchone()
# rows = cur.fetchall()
# for row in rows:
# 	print row

#STATS
#Number of blogs
cur.execute('SELECT COUNT(id) FROM (SELECT * FROM blogs GROUP BY title)')
data = cur.fetchone()
print "Number of unique blogs: "+str(data[0])

#Number of regular blogs
cur.execute('SELECT COUNT(title) FROM reg_blogs')
data = cur.fetchone()
print "Number of regular blogs: "+str(data[0])
reg_num = int(data[0])

#Number of featured blogs
cur.execute('SELECT COUNT(title) FROM featured_blogs')
data = cur.fetchone()
print "Number of featured blogs: "+str(data[0])
feat_num = int(data[0])

#Earliest and latest additions
cur.execute('SELECT MIN(date_added) FROM blogs')
data = cur.fetchone()
print "Started scrapping: "+str(data[0])

cur.execute('SELECT MAX(date_added) FROM blogs')
data = cur.fetchone()
print "Last scrape: "+str(data[0])

#Show how average view/comment number differ from blogs to featured blogs 

feat_views = 0
feat_comms = 0
cur.execute('SELECT * FROM featured_blogs')
rows = cur.fetchall()
for row in rows:
	feat_num+=1
	feat_views+= int(row[2])
	feat_comms+= int(row[3])

print "Average views for a featured blog: " + str(feat_views/feat_num)
print "Average comments for a featured blog: " + str(feat_comms/feat_num)

reg_views = 0
reg_comms = 0
cur.execute('SELECT * FROM reg_blogs')
rows = cur.fetchall()
for row in rows:
	reg_num+=1
	reg_views+= int(row[2])
	reg_comms+= int(row[3])

print "Average views for a regular blog: " + str(reg_views/reg_num)
print "Average comments for a regular blog: " + str(reg_comms/reg_num)

#Show average time featured vs regular stay in sidebar
featured_links = []
feat_scans = 0
cur.execute('SELECT * FROM featured_blogs')
rows = cur.fetchall()
for row in rows:
	featured_links.append(row[1])
for link in featured_links:
	cur.execute('SELECT COUNT(link) FROM featured WHERE link = "%s" GROUP BY link' % link)
	data = cur.fetchone()
	feat_scans += int(data[0])
avg_feat = 0.0
avg_feat = float(((feat_scans*15))/len(featured_links))
print "Featured blogs stay in sidebar an average of " + str(avg_feat/60) + " hours."


reg_links = []
reg_scans = 0
cur.execute('SELECT * FROM reg_blogs')
rows = cur.fetchall()
for row in rows:
	reg_links.append(row[1])
for link in reg_links:
	l = link.replace('http://teamliquid.net','')
	cur.execute('SELECT COUNT(link) FROM latest WHERE link = "%s" GROUP BY link' % l)
	data = cur.fetchone()
	if data != None:
		print l
		reg_scans += int(data[0])
avg_reg = 0.0
avg_reg = float(((reg_scans*15))/len(reg_links))
print "Regular blogs stay in sidebar an average of " + str(avg_reg) + " minutes."

avg_reg/=60
if avg_reg == 0:avg_reg = 1

#Random, assuming constant rate of views etc
exp_views = avg_feat*((reg_views/reg_num)/avg_reg)
exp_comms = avg_feat*((reg_comms/reg_num)/avg_reg)
print "If a regular blog was on the sidebar for the same amount of time as a featured blog,it would get "
print str(int(exp_views)) + " views"
print str(int(exp_comms)) + " comments."

#Lastly an arch, initial impact, impact of being listed and impact of being on the featured list
# feat_first_seen = 0
# feat_last_listed = 0
# feat_last_seen = 0
# 
# for link in featured_links:
# 	cur.execute('SELECT * FROM blogs WHERE link = "%s" ORDER BY id' % link)
# 	rows = cur.fetchall()
# 	r = 0
# 	for row in rows:
# 		if r == 0:
# 			feat_first_seen = row[]
# 		r+=1
# 
# first_seen = 0
# last_listed = 0
# last_seen = 0

feat_overlap = 0
for link in featured_links:
	cur.execute('SELECT COUNT(link) FROM rssPos WHERE link = "%s" GROUP BY link' % link)
	data = cur.fetchone()
	if data != None:
		feat_overlap += 1
print str(feat_overlap) +" featured blogs were ranked by method 1."
reg_overlap = 0
for link in reg_links:
	cur.execute('SELECT COUNT(link) FROM rssPos WHERE link = "%s" GROUP BY link' % link)
	data = cur.fetchone()
	if data != None:
		reg_overlap += 1
print str(reg_overlap) +" reg blogs were ranked by method 1."

feat_overlap = 0
for link in featured_links:
	cur.execute('SELECT COUNT(link) FROM rssUpDown WHERE link = "%s" GROUP BY link' % link)
	data = cur.fetchone()
	if data != None:
		feat_overlap += 1
print str(feat_overlap) +" featured blogs were ranked by method 2."
reg_overlap = 0
for link in reg_links:
	cur.execute('SELECT COUNT(link) FROM rssUpDown WHERE link = "%s" GROUP BY link' % link)
	data = cur.fetchone()
	if data != None:
		reg_overlap += 1
print str(reg_overlap) +" reg blogs were ranked by method 2."

#impossible to show decrease for others?
con.close() 