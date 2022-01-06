'''
The Block class
'''
import json
from hashlib import sha256


class Block:
    '''
    The Block will be instantiated using only the previous block hash.
    Mining the block will require finding a suitable hash value for the object dictionary.
    This gets added separately in the package_block function.
    The Block object itself never stores its own hash.
    '''

    def __init__(self, index: int, previous_hash: str, transactions: list, timestamp: str, nonce=0,
                 node=None):
        self.index = index
        self.previous_hash = previous_hash
        self.transactions = transactions
        self.node = node
        self.nonce = nonce
        self.timestamp = timestamp

    def compute_hash(self):
        return sha256(json.dumps(self.__dict__, sort_keys=True).encode()).hexdigest()


'''
Package block method and recover block from package method.
'''


def block_from_package(packaged_block: dict):
    return Block(
        packaged_block["DATA"]["Index"],
        packaged_block["DATA"]["Previous Hash"],
        packaged_block["TRANSACTIONS"],
        packaged_block["DATA"]["Timestamp"],
        nonce=packaged_block["DATA"]["Nonce"],
        node=packaged_block["DATA"]["Node Address"]
    )


def package_block(block: Block, proof: str):
    data_dict = {
        "Index": block.index,
        "Block Hash": proof,
        "Nonce": block.nonce,
        "Previous Hash": block.previous_hash,
        "Number of transactions": len(block.transactions),
        "Node Address": block.node,
        "Timestamp": block.timestamp
    }
    return {
        "DATA": data_dict,
        "TRANSACTIONS": block.transactions
    }
