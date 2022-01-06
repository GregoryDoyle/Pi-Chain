'''
The Miner class
'''

from block import Block

import datetime


class Miner:
    '''

    '''

    def __init__(self, difficulty: int):
        self.mining_difficulty = difficulty
        self.is_mining = False

    def mine_block(self, block: Block):
        '''
        We are given an unmined block: this contains all elements of the block save the block hash.
        We continually compute the hash of the block, increasing the nonce each time, until we've satisfied the proof conditions
        '''
        self.is_mining = True
        start_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        print(f'Miner: Starting mining of block {block.index + 1} at start time: {start_timestamp}')

        proof = block.compute_hash()
        while not proof.startswith("0" * self.mining_difficulty) and self.is_mining:
            block.nonce += 1
            proof = block.compute_hash()
        if self.is_mining:
            finish_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
            print(f'Miner: Finished mining block {block.index + 1} at finish time: {finish_timestamp} ')
            return block, proof
        else:
            return block, ""

    def stop_mining(self):
        self.is_mining = False
