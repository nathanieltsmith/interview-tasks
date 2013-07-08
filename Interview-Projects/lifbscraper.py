import urllib
import mechanize
import cookielib
import re 
import _mysql
"""
User specified variables
-For this script to work you will need to provide your own values for a facebook and linkedin account in the fbEmail, liEmail, fbPass and liPass
- You'll also need to fill in values appropriate to your database in dbHost, dbUser, dbPwd and dbName
- The tables are described as they were emailed to me.  You should double check that the tables described here are identical to those in your database
- The BATCH_SIZE variable determines how many entries are taken from the database at a time.  It's currently set to 10, but you can change it as you see fit
"""


#Facebook Account Details
fbEmail = ''
fbPass = ''

#LinkedIn Account Details
liEmail = ''
liPass = ''

#Database Details
dbHost = ''
dbUser = ''
dbPwd = ''
dbName = ''

#DBTables
SEARCH_TABLE_NAME = 'search'
#The fields for the search table:
ID = 'id'
FIRST_NAME = 'first_name'
MIDDLE_NAME = 'middle_name'
LAST_NAME = 'last_name'
FULL_NAME = 'fullname'
ADDRESS = 'address'
CITY = 'city'
STATE = 'state'
BIRTHDAY = 'age'
CRAWL = 'crawl'
URL = 'url'
BATCH_SIZE = 10  # The number of unsearched records to check at once.

# Things that must be parsed from the website for a record to be accepted
requiredFields = (FIRST_NAME, LAST_NAME, FULL_NAME, CITY, STATE)

REJECTED_URL_TABLE_NAME = 'rejected'
#The fields for the rejected table.
REJECTED_URL = 'url'

def initDatabase():
	try:
		return _mysql.connect(host=dbHost,user=dbUser, passwd=dbPwd,db=dbName)
	except:
		log("Error %d: %s" % (e.args[0], e.args[1]))
		sys.exit(1)

def initBrowser():
	browser = mechanize.Browser()
	browser.set_handle_robots(False)
	cj = cookielib.CookieJar()
	cookies = mechanize.CookieJar(cj)
	browser.set_cookiejar(cj)
	browser.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.517.41 Safari/534.7')]
	return browser
	
def connectToFB(browser):
	browser.open('http://www.facebook.com')
	browser.select_form(nr=0)
	browser.form['session_key'] = liEmail
	browser.form['session_password'] = liPass
	browser.submit()

def connectToLI(browswer):
	browser.open('http://www.linkedin.com')
	browser.select_form(nr=0)
	browser.form['email'] = fbEmail
	browser.form['pass'] = fbPass
	browser.submit()
"""
Extracts info from the source text of a Facebook 'info' page.  ie a page like http://www.facebook.com/somefacebookid/info  

This was written on June 3rd, 2012 and may break if Facebook changes its layout
"""
def extractFBData(fbPage):

	# Get their name
	namePattern = """<title>(.*)</title>"""
	name = parseName(namePattern, fbPage)

	# Extract a list of the user's friends as a list of FB ID #s
	friendPattern = r""""OrderedFriendsListInitialData",\[\],\{"list"\:\[([^\]]*)\]"""
	friendsList = search(friendPattern, fbPage)[1:-1].split('","')
	if friendsList:
		friendsList = ['http://www.facebook.com/'+x+'/info' for x in friendsList]
		
	# Get the birthday
	birthdayPattern = r"""Birthday</th><td class="data">(.*?)</td>"""
	birthday = search(birthdayPattern, fbPage)
	
	# Get the address.  Compress it to one line
	addressPattern = r""">Address</th><td class="data"><span class="fsm"><ul class="uiList">(.*?)</ul>"""
	address = re.search(addressPattern, fbPage)
	if address:
		address = remove_li_tags(address)[:-2]
	# Get their current location.
	locationPattern = r"""([^>]*)</a></span><div class="fsm fwn fcg">Current City"""
	location = search(locationPattern, fbPage).split(', ')
	city = location[0]
	if len(location) > 1:
		state = location[1]
	else:
		state = ""
	

	info = {"friend":friendsList, FIRST_NAME:name[0], MIDDLE_NAME:name[1], LAST_NAME:name[2], FULL_NAME:name[3], BIRTHDAY:birthday, CITY:city, STATE:state, ADDRESS:address}
	return info

def extractLIData(liPage):
	# Get their name
	
	namePattern = """fullName: '(.*?)',"""
	name = parseName(namePattern, liPage)
	
	# Extract a list of the user's friends as a list of FB ID #s
	friendPattern = r""""(/profile/view\?id=[0-9]*)"""
	friendsList = ['http://www.linkedin.com/' + x for x in (re.findall(friendPattern, liPage) or [])]  
#	friendsList = []	
	# Get the birthday
	birthdayPattern = r"""<dt>Birthday:.*?</dt>.*?<dd>.*?<p>(.*?)</p>"""
	birthday = search(birthdayPattern, liPage)

	# Get the address.  Compress it to one line
	addressPattern = r"""<dt>Address:</dt>\s*<dd>\s*<p>(.*?)</p>"""
	address = search(addressPattern, liPage)

	if address:
		address = remove_br_tags(address)
	# Get their current location.
	locationPattern = r""""location" >(.*?)</a>"""
	location = search(locationPattern, liPage).split(', ')
	city = location[0]
	if len(location) > 1:
		state = location[1]
	else:
		state = ""
	info = {"friend":friendsList, FIRST_NAME:name[0], MIDDLE_NAME:name[1], LAST_NAME:name[2], FULL_NAME:name[3], BIRTHDAY:birthday, CITY:city, STATE:state, ADDRESS:address}
	print info
	return info
	
def search(pattern, page):
	s = re.search(pattern, page, re.MULTILINE|re.UNICODE|re.DOTALL)
	if s:
		return s.group(1)
	else:
		return ""

def remove_li_tags(data):
	p = re.compile(r'</li>')
	mod = p.sub(', ', data)
	q = re.compile(r'<.*?>')
	return q.sub('', mod)

def remove_br_tags(data):
	p = re.compile(r'<br>')
	return p.sub(', ', data)

def getUrls(db):	
	searchString = 'SELECT '+ URL + ' FROM ' + SEARCH_TABLE_NAME + ' WHERE ' + CRAWL + ' = 0 LIMIT = '+ str(BATCH_SIZE)+';'
	try:
		cur = db.cursor()
		cur.execute(searchString)
		urls =  [x[0] for x in cur.fetchall()]
	except:
		log("Failed to Load urls from database")
	try:
		for myUrl in urls:
			updateString = 'UPDATE ' + SEARCH_TABLE_NAME + ' SET '+ CRAWL + ' = 1 WHERE ' + URL + '= "' + myUrl + '";'
	except:
		log("Failed to set records to crawled")
	return urls
	
def addToDB(data, myUrl, db):
	fields = (FIRST_NAME, MIDDLE_NAME, LAST_NAME, FULL_NAME, ADDRESS, CITY, STATE, BIRTHDAY)
	updateString = '('
	for field in fields:
		updateString = updateString + field + ', '
	updateString = updateString[:-2] + ' ) = ('
	for field in fields:
		updateString = updateString + '"'+ (data[field] or '') + '", '
	updateString = 'UPDATE ' + SEARCH_TABLE_NAME + ' SET '+ updateString[:-3] +') WHERE ' + URL+ '= "' + myUrl + '";'
	try:
		cur = db.cursor()
		cur.execute(updateString)
	except:
		log('Failed to add new record to database: ' + updateString)
	
def removeFromDB(myUrl, db):
	insertString  =  'INSERT into ' + REJECTED_URL_TABLE_NAME + ' ('+URL + ') VALUES ("'+myUrl+'");' 
	deleteString =  'DELETE FROM ' + SEARCH_TABLE_NAME + ' WHERE ' + URL + ' = "' + myUrl + '";'
	try:
		cur = db.cursor()
		cur.execute(insertString)
		cur.execute(deleteString)
	except:
		log('SQL failed: ' + insertString + ' and ' + deleteString)
	
def releaseUrl(myUrl, db):
	updateString = 'UPDATE ' + SEARCH_TABLE_NAME + ' SET '+ CRAWL + ' =0 WHERE ' + URL + '= "' + myUrl + '";'
	try:
		cur = db.cursor()
		cur.execute(updateString)
	except:
		log('SQL failed: ' + updateString )
		
	
def parseName(namePattern, html):
	name = search(namePattern, html).split()
	nameParts = len(name)
	# Semantic information isn't available in the HTML so the first word is the first name the last is the last name
	# Everything else is the middle name.
	firstName = name[0]
	if nameParts >= 2:
		lastName = name[-1]
	else:
		lastName = ""
	if nameParts >= 3:
		middleName = " ".join(name[1:-1])
	else:
		middleName = ""
	fullName = " ".join(name)
	return (firstName, middleName, lastName, fullName)
	
def addFriendsToDB(friends, db):
	try:
		cur = db.cursor()
		for friend in friends:
			searchString1 =  'SELECT '+ URL + ' FROM ' + SEARCH_TABLE_NAME + ' WHERE '+URL+ ' = "'+ friend + '";'
			cur.execute(searchString1)
			if not cur.fetchall():
				searchString2 =  'SELECT '+ REJECTED_URL + ' FROM ' + REJECTED_URL_TABLE_NAME + ' WHERE '+REJECTED_URL+ ' = "'+ friend +'";'
				cur.execute(searchString2)
				if not cur.fetchall():
					insertString  =  'INSERT into ' + SEARCH_TABLE_NAME + ' ('+URL + ', '+ CRAWL +') VALUES ("'+friend+'",  0);' 
					cur.execute(insertString)
	except:
		log('Failed to add friends to database.')
		
def validateData(data):
	for field in requiredFields:
		if not data[field]:
			log("No value for "+ field+ " data rejected")
			return False
	log ("Record validated for " + data[FULL_NAME])
	return True
	
"""
log
A method for status output.  Right now it just prints the information, but I left it as a function
so that you can modify it to suit your will.
"""
def log(message):
	print message
	
def main():
	#initialize connections
	log('Starting up')
	db = initDatabase()
	br = initBrowser()
	try:
		connectToFB(br)
		connectToLI(br)
	except:
		log("Unable to connect to websites")
		sys.exit(1)
	urls = getUrls(db)
	while urls:
		for url in urls:
			try:
				log("Attempting to load page at " + url)
				page = br.open(url).read() #check that this is the correct call
			except:
				log("Failed to load page at " + url)
				releaseUrl(url, db)
				page = ''
			if (page):
				if 'facebook' in url:
					data = extractFBData(page)
				elif 'linkedin' in url:
					data = extractLIData(page)
				else:
					log("Unrecognized url: " + url)
					break
			else:
				log("Page at " + url + " failed to load")
				break
			if (validateData(data)):
				log("Adding data from " + url + " to the database")
				addToDB(data, db)
			else:
				log("Page at "+ url +" contains insufficient data")
				removeFromDB(url, db)
			if data['friend']:
				addFriendsToDB(data['friend'], db)
		urls = getUrls(db)

main()