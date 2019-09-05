from flask import Flask, request,render_template, redirect
from hashlib import sha256
import requests
import json
import time
import datetime
from app import app

CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"
posts = []



def fetch_post_from_nodes():
	chain_node_address = f"""{CONNECTED_NODE_ADDRESS}/chain"""
	response = None
	response = requests.get(chain_node_address)
	if response != None:
		if response.status_code == 200:
			content = []
			chain  = json.loads(response.content)
			for block in chain["chain"]:
				for info in block["information"]:
					info["hash"] = block["previous_hash"]
					info["nonce"]=0
					content.append(info)
			global posts
			posts = sorted(content, key=lambda k: k['timestamp'], reverse = True)
		else:
			return "Error in fetching_posts_from_nodes"



def timestamp_to_string(epoch_time):
	return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')



@app.route('/')
def index():
	fetch_post_from_nodes()
	return render_template('index.html',title = "Satti's Information Blockchain Implementation v1.2",posts=posts,node_address = CONNECTED_NODE_ADDRESS, readable_time = timestamp_to_string)




@app.route('/submit',methods = ['POST'])
def submit_information():
	post_content = request.form['content']
	author = request.form["author"]
	post_objects = {
	'author' : author,
	'content' : post_content,
	}
	new_data_address = f"""{CONNECTED_NODE_ADDRESS}/unconfirmed_block"""
	requests.post(new_data_address, json=post_objects, headers={'Content-type' : 'application/json'})
	return redirect('/')

