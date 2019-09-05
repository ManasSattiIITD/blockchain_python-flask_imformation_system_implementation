from flask import Flask, request,render_template, redirect
from hashlib import sha256
import requests
import json
import time
import datetime


class Block:
	index = -1
	def __init__(self, information, previous_hash,nonce):
		self.hash = self.calculate_hash()
		self.nonce = nonce
		self.information = information
		self.timestamp = time.time()
		self.previous_hash = previous_hash
		self.index+=1

	def calculate_hash(self):
		data = json.dumps(self.__dict__,sort_keys= True)
		apple = sha256(data.encode('utf-8')).hexdigest()
		self.hash = apple
		return apple

class Blockchain:

	nonce_level = 2

	def __init__(self):
		self.uncomfirmed_blocks = []
		self.chain = []
		self.create_genesis_block()

	def create_genesis_block(self):
		genesis_block = Block( [], "0",0)
		genesis_block_hash = genesis_block.hash
		self.chain.append(genesis_block)

	def add_unconfirmed_block(self, block_nought):
		self.uncomfirmed_blocks.append(block_nought)

	@property
	def last_block(self):
		return self.chain[-1]

	def proof_of_work(self, block):
		block.nonce = 0
		temp_hash = block.calculate_hash()
		while not temp_hash.startswith('0'*Blockchain.nonce_level):
			block.nonce+=1
			temp_hash = block.calculate_hash()
		return temp_hash

	
	@classmethod
	def verify_pow(cls, block, hash_temp):
		return (hash_temp.startswith('0'*cls.nonce_level) and hash_temp == block.hash)

	def add_block(self,block,hash_from_proof):
		previous_hash_1 = self.last_block.hash
		if previous_hash_1 != block.previous_hash:
			return False
		if not Blockchain.verify_pow(block, hash_from_proof):
			return False
		self.chain.append(block)
		return True

	def mine(self):
		if not self.uncomfirmed_blocks:
			return False
		end_block = self.last_block
		temp_block = Block(self.uncomfirmed_blocks,end_block.hash,0)
		hash_from_proof = self.proof_of_work(temp_block)
		self.add_block(temp_block, hash_from_proof)
		self.uncomfirmed_blocks = []
		return temp_block.index


	@classmethod
	def validity_check(cls,chain):
		res = True
		previous_hash = '0'
		for block in chain:
			if not cls.verify_pow(block,block.hash) or previous_hash != block.previous_hash:
				result = False
				break
			previous_hash = block.hash
		return res




def consensus():
	global blockchain
	longest = None
	length_of_chain = len(blockchain.chain)

	for i in nodes:
		print(f'''{i}/chain''')
		response = requests.get(f'''{i}/chain''')
		print("Content ",response.content)
		length = response.json()['length']
		chain = response.json()['chain']
		if length > length_of_chain and Blockchain.validity_check():
			length_of_chain = length
			longest = chain
	if longest:
		blockchain = longest
		return True
	else:
		return False

def brodcast_the_newly_mined_block(block):
	for i in nodes:
		url = f"""{i}add_block"""
		requests.post(url, data=json.dumps(block.__dict__, sort_keys=True))


def create_chain_from_dump(chain_dump):
	blockchain = Blockchain()
	for idx, block_data in enumerate(chain_dump):
		block = Block(block_data["information"],block_data["previous_hash"],0)
		temp_hash = block_data['hash']
		if idx > 0:
			added = blockchain.add_block(block, temp_hash)
			if not added:
				raise Exception("The chain dump is tampered!")
		else:
			blockchain.chain.append(block)
	return blockchain




app = Flask(__name__)
blockchain = Blockchain()
blockchain.create_genesis_block()
nodes = set()



@app.route('/chain',methods=['GET'])
def whatischain():
	consensus()
	chain_data = []
	for block in blockchain.chain:
		chain_data.append(block.__dict__)
	return json.dumps({"length": len(chain_data),"chain": chain_data,"nodes":list(nodes)})



@app.route('/unconfirmed_block', methods=['POST'])
def unconfirmed_block():

	# def check_format(info):
	# 	format = ["author","content"]
	# 	for i in format:
	# 		if not info.get(i):
	# 			return False
	# 	return True

	data = request.get_json()
	required_fields = ["author","content"]
	print(data)
	for i in required_fields:
		if  not data.get(i):
			return "Invalid transaction data", 404
	data["timestamp"] = time.time()
	blockchain.add_unconfirmed_block(data)
	return "Success", 201



@app.route('/mining',methods=['GET'])
def mine_unconfirmed_blocks():
	res = blockchain.mine()
	if not res:
		return render_template('/empty_error.html')
	return f"""Block #{res} is mined."""


@app.route('/register_node', methods = ['POST'])
def register_new_nodes():
	node_address = request.get_json()["node_address"]
	if not node_address:
		return "Invalid", 400
	nodes.add(node_address)
	return whatischain()


@app.route('/register_with_existing_node', methods=['POST'])
def register_with_existing_node():
	node_address = request.get_json()["node_address"]
	if not node_address:
		return "Invalid", 400
	data = {"node_address": request.host_url}
	headers = {"Content-Type" : "application/json"}
	response = requests.post(node_address + "/register_node",data = json.dumps(data), headers = headers)
	if response.status_code == 200:
		global blockchain
		global nodes
		chain_dump = response.json()['chain']
		blockchain = create_chain_from_dump(chain_dump)
		nodes.update(response.json()['peers'])
		return "Registration successful", 200
	else:
		return response.content , response.status_code


		
@app.route('/add_block', methods = ['POST'])
def verify_and_add():
	block_data = request.get_json()
	block = Block(block_data['information'],block_data['previous_hash'],0)
	hash_from_proof = block_data['hash']
	added = blockchain.add_block(block, hash_from_proof)

	if not added:
		return "The block was discarded by the node", 400
	return "Block added to the chain", 201


@app.route('/pending_blocks')
def get_pending_blocks():
	return json.dumps(blockchain.unconfirmed_blocks)


def timestamp_to_string(epoch_time):
	return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')
