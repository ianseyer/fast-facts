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

def handle_query(query):
		request_url = "http://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch="+query+"&continue=&srprop=timestamp"
		r = requests.get(request_url)

		title = r.json()['query']['search'][0]['title']
		request_url = "http://en.wikipedia.org/w/index.php?action=render&title="+title
		response = requests.get(request_url)
		soup = BeautifulSoup(response.text)
		[each.decompose() for each in soup.find_all('table')]
		out = soup.find_all('p')[0].get_text()[0:157]+"..."
		return (out, title)

@app.route('/search', methods=['GET', 'POST'])
def query():

	if request.method == 'GET':
		#just display the input form
		return render_template('search.html')

	elif request.method == 'POST':
		result = handle_query(request.form['q'])
		return render_template('search.html', result=result[0], link="http://en.wikipedia.org/w/index.php?action=render&title="+result[1])

@app.route('/sms')
def sms():
	query = request.args['Body']
	print query
	result = handle_query(query)

	resp = twilio.twiml.Response()
	print removeNonAscii(result[0])
	resp.message(unicode(result[0]))
	return str(resp)
	

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=80)
