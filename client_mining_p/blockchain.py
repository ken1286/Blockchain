import hashlib
import json
from time import time
from uuid import uuid4

from flask import Flask, jsonify, request


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Create the genesis block
        self.new_block(proof=100, previous_hash=1)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain

        A block should have:
        * Index
        * Timestamp
        * List of current transactions
        * The proof used to mine this block
        * The hash of the previous block

        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        # Append the chain to the block
        self.chain.append(block)

        # Return the new block
        return block

    def hash(self, block):
        """
        Creates a SHA-256 hash of a Block

        :param block": <dict> Block
        "return": <str>
        """

        # Use json.dumps to convert json into a string
        # Use hashlib.sha256 to create a hash
        # It requires a `bytes-like` object, which is what
        # .encode() does.
        # It convertes the string to bytes.
        # We must make sure that the Dictionary is Ordered,
        # or we'll have inconsistent hashes

        # TODO: Create the block_string
        string_object = json.dumps(block, sort_keys=True)
        block_string = string_object.encode()

        # TODO: Hash this string using sha256
        raw_hash = hashlib.sha256(block_string)
        hex_hash = raw_hash.hexdigest()

        # By itself, the sha256 function returns the hash in a raw string
        # that will likely include escaped characters.
        # This can be hard to read, but .hexdigest() converts the
        # hash to a string of hexadecimal characters, which is
        # easier to work with and understand

        # TODO: Return the hashed block string in hexadecimal format
        return hex_hash

    @property
    def last_block(self):
        return self.chain[-1]

    # def proof_of_work(self, block):
    #     """
    #     Simple Proof of Work Algorithm
    #     Stringify the block and look for a proof.
    #     Loop through possibilities, checking each one against `valid_proof`
    #     in an effort to find a number that is a valid proof
    #     :return: A valid proof for the provided block
    #     """
    #     # Proof is a SHA256 hash with 3 leading zeroes
    #     block_string = json.dumps(block, sort_keys=True).encode()
    #     proof = 0
    #     while not self.valid_proof(block_string, proof):
    #         proof += 1
    #     return proof

    @staticmethod
    def valid_proof(block_string, proof):
        """
        Validates the Proof:  Does hash(block_string, proof) contain 3
        leading zeroes?  Return true if the proof is valid
        :param block_string: <string> The stringified block to use to
        check in combination with `proof`
        :param proof: <int?> The value that when combined with the
        stringified previous block results in a hash that has the
        correct number of leading zeroes.
        :return: True if the resulting hash is a valid proof, False otherwise
        """
        guess = f'{block_string}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        # return True or False
        return guess_hash[:6] == "000000"

    def new_transaction(self, sender, recipient, amount):
        transaction = {'sender': sender,
                       'recipient': recipient, 'amount': amount}

        self.current_transactions.append(transaction)

        return self.last_block['index'] + 1


# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    if not all(k in values for k in required):
        response = {'message': 'Missing Values'}
        return jsonify(response), 400

    index = blockchain.new_transaction(
        values['sender'], values['recipient'], values['amount'])

    response = {'message': 'Transaction successful'}
    return jsonify(response), 200


@app.route('/last_block', methods=['GET'])
def last():
    last_block = blockchain.last_block
    print(last_block)
    response = {
        'last_block': last_block
    }
    return jsonify(response), 200


@app.route('/mine', methods=['POST'])
def mine():
    # Use data = request.get_json() to pull the data out of the POST
    data = request.get_json()
    print(data)
    if 'proof' not in data or 'id' not in data:
        return jsonify({'message': 'Proof and ID required'}), 400
    # Run the proof of work algorithm to get the next proof
    print(data)

    # proof = blockchain.proof_of_work(blockchain.last_block)
    proof = data['proof']

    # Forge the new Block by adding it to the chain with the proof
    previous_hash = blockchain.hash(blockchain.last_block)
    last_block_string = json.dumps(
        blockchain.last_block, sort_keys=True).encode()

    # if blockchain.valid_proof(last_block_string, proof):
    if blockchain.valid_proof(last_block_string, proof):
        block = blockchain.new_block(proof, previous_hash)

        blockchain.new_transaction(
            sender="0",
            recipient=data['id'],
            amount=1
        )

        response = {
            'message': "New Block Forged",
            'index': block['index'],
            'transactions': block['transactions'],
            'proof': block['proof'],
            'previous_hash': block['previous_hash'],
        }
        return jsonify(response), 200
    else:
        return jsonify({'message': 'FAILURE'}), 200


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'length': len(blockchain.chain),
        'chain': blockchain.chain,
    }
    return jsonify(response), 200


@app.route('/', methods=['GET'])
def home():
    return "<h1>Welcome to blockchain!</h1>", 200


# Run the program on port 5000
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
