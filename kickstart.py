"""
fast facts is an sms-based wikipedia query simplifier.

query => translation thing => shortened first section

"""
#foreign`
from flask import Flask, render_template, jsonify, request
import requests, re
from bs4 import BeautifulSoup

#domestic

app = Flask(__name__)
app.secret_key = 'fastfacts'

@app.route('/search', methods=['GET', 'POST'])
def query():

	if request.method == 'GET':
		#just display the input form
		return render_template('search.html')

	elif request.method == 'POST':
		print 'method was post'
		print request.form['q']
		#display the form and results
		query = request.form['q']

		request_url = "http://en.wikipedia.org/w/api.php?action=query&format=json&list=search&srsearch="+query+"&continue=&srprop=timestamp"
		r = requests.get(request_url)

		title = r.json()['query']['search'][0]['title']
		request_url = "http://en.wikipedia.org/w/index.php?action=render&title="+title
		response = requests.get(request_url)
		soup = BeautifulSoup(response.text)

		out = soup.p.get_text()[0:157]+"..."
		return render_template('search.html', result=out)

if __name__ == '__main__':
	app.run(debug=True)