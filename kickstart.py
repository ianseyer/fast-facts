"""
mfacti is an sms-based wikipedia query simplifier.

query => translation thing => shortened first section of wikipedia

we use beautifulsoup to lightly scrape the first 157 (160-3, to leave room for the "...") characters of the wikipedia entry for the submitted query,
and requests to submit search queries to wikipedias API.

authored November 8th+9th by Gus Ireland, Megan Ruthven, and Ian Seyer
for the Developers Doing Development hack-a-thon held at Chicon Collective in Austin, TX
"""
#foreign
from flask import Flask, render_template, jsonify, request, redirect
import requests, re, string
from bs4 import BeautifulSoup
import twilio.twiml
import xml.etree.ElementTree as ET

#domestic
#none

app = Flask(__name__)
app.secret_key = 'fastfacts'

lang = "en"
number_to_language = {"+15122707266":"en", "+18329393590":"sw"}

def shorten_resp(first):
	first = re.sub('\(.*\) ', '', first)
	first = re.sub('\[.*\] ', '', first)
	out = first[0:157]+"..."
	return out

def handle_wikipedia_query(query, lang):
		"""
		searches via wikipedias API, and then returns the slice of the first paragraph.
		"""
		query = re.sub('[^\w\s]', '', query)
		wikipedia_search_url = "http://"+lang+".wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch="+query+"&continue=&srprop=timestamp"
		wikipedia_response = requests.get(wikipedia_search_url)

		try:
			title = wikipedia_response.json()['query']['search'][0]['title']
		except IndexError: #there were no results
			return ("Nothing was found!", "Nothing was found!", "en")

		wikipedia_render_url = "http://"+lang+".wikipedia.org/w/index.php?action=render&title="+title
		wikipedia_response = requests.get(wikipedia_render_url)
		soup = BeautifulSoup(wikipedia_response.text)
		[each.decompose() for each in soup.find_all('table')] #remove side tables, so we don't accidentally pull in table data
		first = soup.find_all('p')[0].get_text()
		first = re.sub('', '', first)
		out = shorten_resp(soup.find_all('p')[0].get_text())
		if "Kutoka Wikipedia, ensaiklopidia huru" in out: #this phrase is the opening of wikipedia articles (in swahili) that have been translated, so ignore it and pull the next paragraph
			out = shorten_resp(out = soup.find_all('p')[1].get_text())

		return (out, title, lang)

def handle_wolfram_query(query, lang):
	app_id = "U2YWX7-8YK5VU8L2J"
	endpoint = "http://api.wolframalpha.com/v2/query?input="+query+"&format=plaintext&appid="+app_id
	wolfram_response = requests.get(endpoint).text
	root = ET.fromstring(filter(lambda x: x in string.printable, wolfram_response))
	try:
		result = root.findall(".//pod[@title='Result']/subpod/")[0].text
	except IndexError: #no result, or not a useful one
		result = ""
	print result
	return result

@app.route('/',  methods=['GET', 'POST'])
def index():
	return redirect('/search')
	
@app.route('/search', methods=['GET', 'POST'])
def query():
	"""
	the web-based search form
	"""
	if request.method == 'GET':
		#just display the input form
		return render_template('search.html')

	elif request.method == 'POST':
		query = re.sub('!?/._@#:', '', request.form['q'])
		result = handle_wikipedia_query(query, "en")
		return render_template('search.html', result=result[0], link="http://"+result[2]+".wikipedia.org/w/index.php?action=render&title="+result[1], goog="https://www.google.com/search?q="+query)

@app.route('/wolfram')
def wolfram(query="zimbabwe president"):
	output = handle_wolfram_query(query, "en")
	root = ET.fromstring(filter(lambda x: x in string.printable, output))
	try:
		result = root.findall(".//pod[@title='Result']/subpod/")[0].text
	except IndexError: #no result, or not a useful one
		result = ""
	return result

@app.route('/sms')
def sms():
	"""
	find out which language's number was texted, and set the wikipedia language code to that.
	this handles translation for us.
	respond to the incoming text with the output from handle_query
	"""
	resp = twilio.twiml.Response()
	try:
		query = request.args['Body']
		if query is None:
			resp.message("Sorry, you must enter at least a word!") #translate this
			return str(resp)
		print request.args['To']
		wikipedia_result = handle_wikipedia_query(query, number_to_language[request.args['To']])[0]
		wolfram_result = handle_wolfram_query(query, "en")
		resp = twilio.twiml.Response()
		resp.message([unicode(wikipedia_result), unicode(wolfram_result)])
		return str(resp)

	except:
		resp = twilio.twiml.Response()
		resp.message("Sorry, something went wrong!") #don't forget to translate this eventually
		return str(resp)
	

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=8080)
