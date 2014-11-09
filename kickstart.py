"""
fast facts is an sms-based wikipedia query simplifier.

query => translation thing => shortened first section of wikipedia

"""
#foreign`
from flask import Flask, render_template, jsonify, request, redirect
import requests, re
from bs4 import BeautifulSoup
import twilio.twiml

#domestic
#none

app = Flask(__name__)
app.secret_key = 'fastfacts'

lang = "en"
API_KEY = "NOOOOOOOO"
number_to_language = {"+15122707266":"en", "+18329393590":"sw"}

def handle_query(query, lang):
		query = re.sub('!?/._@#:', '', query)
		request_url = "http://"+lang+".wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch="+query+"&continue=&srprop=timestamp"
		r = requests.get(request_url)

		title = r.json()['query']['search'][0]['title']
		request_url = "http://"+lang+".wikipedia.org/w/index.php?action=render&title="+title
		response = requests.get(request_url)
		soup = BeautifulSoup(response.text)
		[each.decompose() for each in soup.find_all('table')]
		first = soup.find_all('p')[0].get_text()
		first = re.sub('', '', first)
		out = soup.find_all('p')[0].get_text()[0:157]+"..."
		if "Kutoka Wikipedia, ensaiklopidia huru" in out:
			out = soup.find_all('p')[1].get_text()[0:157]+"..."
		return (out, title, lang)

@app.route('/',  methods=['GET', 'POST'])
def index():
	return redirect('/search')
	
@app.route('/search', methods=['GET', 'POST'])
def query():
	if request.method == 'GET':
		#just display the input form
		return render_template('search.html')

	elif request.method == 'POST':
		query = re.sub('!?/._@#:', '', request.form['q'])
		result = handle_query(query, "en")
		return render_template('search.html', result=result[0], link="http://"+result[2]+".wikipedia.org/w/index.php?action=render&title="+result[1], goog="https://www.google.com/search?q="+query)

@app.route('/sms')
def sms():
	"""

	"""
	resp = twilio.twiml.Response()
	try:
		query = request.args['Body']
		if query is None:
			resp.message("Sorry, you must enter at least a word!") #translate this
			return str(resp)
		print request.args['To']
		result = handle_query(query, number_to_language[request.args['To']])	
		resp = twilio.twiml.Response()
		resp.message(unicode(result[0]))
		return str(resp)

	except:
		resp = twilio.twiml.Response()
		resp.message("Sorry, something went wrong!") #don't forget to translate this eventually
		return str(resp)
	

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0', port=8080)
