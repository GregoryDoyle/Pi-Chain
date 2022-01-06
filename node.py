'''
The Node class:

    The Node will manage the blockchain.
    The Node will be responsible for submitting new blocks to be added to the chain.
    New Blocks can either be mined from the Node or forwarded on from another Node.

    Each Node will run an Event Listener - which listens for incoming requests
    When a request is received, the Event Listener will spawn a new thread to handle it.

    Additionally, each Node has the option to run a Miner.
    The Miner will gather the local transactions in the Node and attempt to package them into a block.
    "Mining" the block will be to search for a "proof-of-work" hash value.
    This hash value will satisfy the condition that the hash begin with a certain number of zeros.
    How many numbers of zeros needed as prefix is called the difficulty of the proof of work.
    More zeros means a harder difficulty as it will take a longer time to find the requisite hash, on average.

    In a Node, transactions will be divided into 3 groups:
        -free
        -firm
        -confirmed
    -A transaction is confirmed whenever it has been saved to the blockchain.
    -A transaction being used by a miner for a block is called firm.
    -Transactions sent to the Node and not used by the miner are called free.

    When a Node receives a new transaction, it is the responsibility of the Node to forward the transaction to the network.
    If a Node connects to the network, it's the responsibility of the Node to get the free transactions from the network.

    Every Node is responsible for staying in sync with the other Nodes.
    That means if a Node adds a new block, it is the responsibility of the Node to communicate this to the network.
    However, it may happen that Nodes get out of sync, and they match up to block n but differ at block n+1.

    ***
    In order to do this, the Node will keep a list of hashes used in its blockchain.
    The hashlist of one Node can then be compared to the hashlist of another Node to see where they differ.
    ***

    Whenever Nodes get out of sync, they will use a consensus gathering mechanism to decide which chain is correct.
    In addition to the hashlist, each Node will keep track of the index and timestamp of last block added.
    The block index, last block hash and last block timestamp will be bundled into what we call its "status."
    Each Node will also get the status of every other Node in order to gather consensus.

    In order to gather consensus, we first find those Nodes with greatest index - this will be the consensus index.
    This is because we assume those Nodes have valid blocks, and those Nodes without need that block added.
    Hence, from those Nodes with greatest index we find the most common hash - this will be the consensus hash value.
    If there are two or more hash values which are equally as common, we choose the block with the earliest timestamp.

    Thus, each Node is in charge of managing their own blockchain in order to keep up with consensus.
    A Node must distribute its status to the network whenever this changes.
    Further, a Node must gather consensus whenever it receives a status update from a Node.
    A Node with the consensus index and consensus hashtime in its status is said to be a "consensus Node."
    If a Node gathers consensus and finds it is NOT in consensus, it will request updates only from those consensus Nodes.

    ***
    CONSENSUS UPDATE ALGORITHM
    ***
    After a Node gathers consensus:
        -If its index is behind the consensus index, it will stop mining.
            -If its index is 1 behind the consensus index, the Node will wait for the next block.
            -If its index is more than 1 behind the consensus index, it will find out where it matches with a random
                consensus node, and remove blocks up to the matching one, then get all missing blocks from the
                consensus nodes.
        -If its index matches the consensus_index but its hashtime doesn't match the consensus hashtime
            -It will compare its hashlist to a random consensus node's hashlist
            -From this, it will not how many blocks in its chain match consensus
            -The Node will then remove all blocks that don't match, and get the missing blocks from consensus nodes

    A Node will gather consensus when:
        -It adds a new block
        -It receives a status update from a Node

    A Node will update its status when:
        -It adds a new block

    A Node will send status updates to the network when:
        -Its status changes
    '''

from block import Block, block_from_package, package_block
from blockchain import Blockchain
from miner import Miner
from transaction import Transaction
from networking import close_socket, create_socket, package_and_send_data, receive_data
from wallet import Wallet

import threading
import datetime
import socket
import json
import time

import numpy as np
import pandas as pd


class Node:
    '''
    Global Variables
    '''
    DEFAULT_PORT = 41000
    DEFAULT_RANGE = 99

    HEADER = 8
    FORMAT = 'utf-8'

    LOCALHOST = socket.gethostbyname(socket.gethostname())
    LISTENER_TIMEOUT = 10

    '''
    Initialization
    '''

    def __init__(self):
        '''

        '''

        '''Instantiate an empty Blockchain'''
        self.blockchain = Blockchain()

        '''Give the node an address in a Wallet'''
        self.local_wallet = Wallet()
        self.local_address = self.local_wallet.address

        '''Get mining information from Blockchain'''
        self.mining_reward = self.blockchain.MINING_REWARD
        self.mining_difficulty = self.blockchain.MINING_DIFFICULTY

        '''Create Miner object for node'''
        self.miner = Miner(self.mining_difficulty)

        '''Establish mining and listening flags - disable to start'''
        self.is_mining = False
        self.is_listening = False

        '''Create empty transaction lists'''
        self.free_transactions = []
        self.firm_transactions = []

        '''Setup Node address using provided host'''
        self.local_host = self.LOCALHOST
        self.node_port = self.DEFAULT_PORT
        self.local_node = (self.local_host, self.node_port)

        '''Create empty node list'''
        self.node_list = []

        '''Create consensus variables'''
        self.consensus_index = -1
        self.consensus_hash = ""
        self.consensus_time = datetime.datetime.max.isoformat()

        '''Create consensus dictionary'''
        self.consensus_dict = {}

        '''Start event listener'''
        self.start_event_listener()

        '''TESTING'''
        self.MAIN_NODE = (self.local_host, self.DEFAULT_PORT)

        '''********************************************************'''

    '''
    Node Properties
    '''

    @property
    def last_block(self):
        return self.blockchain.last_block

    @property
    def block_count(self):
        return self.blockchain.block_count

    @property
    def transaction_count(self):
        return self.blockchain.transaction_count

    @property
    def ledger(self):
        return self.blockchain.ledger

    @property
    def status(self):
        if self.last_block != []:
            status_dict = {
                "INDEX": self.last_block["DATA"]["Index"],
                "HASH": self.last_block["DATA"]["Block Hash"],
                "TIME": self.last_block["DATA"]["Timestamp"]
            }
        else:
            status_dict = {
                "INDEX": -1,
                "HASH": "",
                "TIME": datetime.datetime.max.isoformat()
            }
        return status_dict

    @property
    def consensus(self) -> dict:
        consensus_dict = {
            "Consensus Index": self.consensus_index,
            "Consensus Hash": self.consensus_hash,
            "Consensus Timestamp": self.consensus_time
        }
        return consensus_dict

    @property
    def consensus_nodes(self) -> list:
        consensus_node_list = []
        for node in self.consensus_dict:
            status_dict = self.consensus_dict.get(node)
            temp_index = status_dict.get("INDEX")
            temp_hash = status_dict.get("HASH")
            temp_time = status_dict.get("TIME")
            if temp_time == self.consensus_time \
                    and temp_index == self.consensus_index \
                    and temp_hash == self.consensus_hash:
                consensus_node_list.append(node)
        return consensus_node_list

    @property
    def hashlist(self) -> list:
        hashlist = []
        for package in self.blockchain.chain:
            hash = package["DATA"]["Block Hash"]
            hashlist.append(hash)
        return hashlist

    '''
    Update Status Function
    '''

    def update_status(self):
        '''
        Update status function will populate the consensus_dict with the latest local status
        '''
        self.consensus_dict.update({self.local_node: self.status})

    '''
    Thread Management
    '''

    def get_running_threads(self):
        print(f'Total number of running threads: {threading.active_count()}', end='\r\n')

    '''
    Display
    '''

    def pretty_transactions(self):
        print("----------", end='\r\n')
        print(f'Free Transactions:', end='\r\n-----\r\n')
        for r in self.free_transactions:
            print('Receipt: ', end='\r\n')
            print(json.dumps(r, indent=1), end='\r\n\n')

        print("----------")

        print(f'Firm Transactions:', end='\r\n-----\r\n')
        for r in self.firm_transactions:
            print('Receipt: ', end='\r\n')
            print(json.dumps(r, indent=1), end='\r\n\n')

    def pretty_chain(self):
        for x in range(0, self.block_count):
            print(f'Block {x + 1}', end='\r\n-----\r\n')
            print(json.dumps(self.blockchain.chain[x], indent=1), end='\r\n')

    def pretty_data(self):
        print('\r\nBlockchain Data', end='\r\n=====\r\n')
        print(f'Number of blocks: {self.block_count}', end='\r\n')
        print(f'Total transactions saved to chain: {self.transaction_count}', end='\r\n')
        print(f'Event listener running: {self.is_listening}', end='\r\n')
        print(f'Miner running: {self.is_mining}', end='\r\n')
        print('=====', end='\r\n')
        print('\r\nNode Data', end='\r\n=====\r\n')
        print(f'Local node is at address: {self.local_host}', end='\r\n')
        print(f'Local node listens on port: {self.node_port}', end='\r\n')
        print(f'Total number of connected nodes: {len(self.node_list)}', end='\r\n')
        print(f'List of connected nodes: {self.node_list}', end='\r\n')
        print('=====', end='\r\n')
        print('\r\nThread Data', end='\r\n=====\r\n')
        print(f'Active threads: {threading.active_count()}', end='\r\n')
        print('=====', end='\r\n')
        print('\r\nConsensus Dict', end='\r\n=====\r\n')
        print('-----', end='\r\n')
        for d in self.consensus_dict:
            print(f'Node: {d}', end='\r\n')
            temp_dict = self.consensus_dict.get(d)
            index = temp_dict["INDEX"]
            hash = temp_dict["HASH"]
            ttime = temp_dict["TIME"]
            print(f'Index: {index}', end='\r\n')
            print(f'Hash: {hash}', end='\r\n')
            print(f'Timestamp: {ttime}', end='\r\n')
            print('-----', end='\r\n')
        print('=====', end='\r\n')
        print('\r\nLedger Data', end='\r\n=====\r\n')
        print(f'{self.ledger}', end='\r\n=====\r\n\n')

    def pretty_last_block(self):
        print(f'Block {self.block_count}', end='\r\n-----\r\n')
        print(json.dumps(self.last_block, indent=1), end='\r\n')

    '''
    Mining
    '''

    def start_miner(self):
        '''
        Start Miner function.
            Miner can only be running if the Event Listener is also running.
            If the Node is listening, and the Miner hasn't started, we start running the Miner in its own thread.
        '''
        if self.is_listening:
            if not self.is_mining:
                self.is_mining = True
                self.mining_thread = threading.Thread(target=self.mine_block)
                self.mining_thread.start()
                print(f'\r\nNODE: Miner started. Active threads: {threading.active_count()}', end='\r\n')
            else:
                print(f'\r\nMiner is already running.', end='\r\n')
        else:
            print(f'\r\nEvent Listener not running, mining is disabled.', end='\r\n')

    def stop_miner(self):
        '''
        Stop Miner function.

        If the Miner is running:
            We call Miner.stop_mining() which sends an interrupt to the Miner.mine_block function.
            This function returns an empty string rather than a proof-of-work hash value, which is gracefully handled.
            The Node.mine_block function will close the mining thread and set self.is_mining = False.
        '''
        if self.is_mining:
            self.miner.stop_mining()
            while self.mining_thread.is_alive():
                pass
            print(f'NODE: Miner stopped. Active threads: {threading.active_count()}', end='\r\n')
        else:
            print(f'Miner not running. Active threads: {threading.active_count()}', end='\r\n')

    def mine_block(self):
        '''
        The mine block function is run in its own thread. The other active threads are:
            -main thread (CLI)
            -event listener
        Until interrupted, the mine_block function will continually mine new blocks and add them to the local chain.
        An interrupt will be in the form of a new block sent to the node, or a manual stop command.
       '''
        interrupted = False
        while not interrupted:
            '''
            Prep new Block
            '''
            mining_transaction = Transaction("MINE", self.local_address, self.mining_reward)
            signature = mining_transaction.sign_transaction(self.local_wallet._Wallet__private_key)
            self.free_transactions.insert(0, mining_transaction.receipt(signature))

            self.firm_transactions = self.blockchain.validate_transactions(self.free_transactions)
            self.free_transactions = []

            mining_timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

            if self.last_block == []:
                new_block = Block(0, "", self.firm_transactions.copy(), mining_timestamp, nonce=0, node=self.local_node)
            else:
                new_block = Block(self.last_block["DATA"]["Index"] + 1, self.last_block["DATA"]["Block Hash"],
                                  self.firm_transactions.copy(), mining_timestamp, nonce=0, node=self.local_node)

            '''
            Mine new Block
            '''
            mined_block, proof = self.miner.mine_block(new_block)

            '''
            Add new Block
            '''
            if proof != "":
                new_package = package_block(mined_block, proof)
                if self.add_block(new_package):
                    self.send_block_to_network(new_package)
                    self.send_status_to_network()
            else:
                print(f'Mining interrupt received.')
                self.firm_transactions.pop(0)
                if self.free_transactions != []:
                    self.free_transactions.extend(self.firm_transactions)
                else:
                    self.free_transactions = self.firm_transactions.copy()
                self.firm_transactions = []
                interrupted = True
            '''Set Mining to False if we are closing the Mining thread.'''
        self.is_mining = False

    '''
    Add New Block
    '''

    def add_block(self, package: dict) -> bool:
        '''
        This will try and add a block package to the chain. Return True/False.
        '''

        added = False

        block = block_from_package(package)
        proof = package["DATA"]["Block Hash"]
        confirmed_transactions = package["TRANSACTIONS"]

        '''If the block gets added successfully'''
        if self.blockchain.add_block(block, proof):
            self.firm_transactions = self.sieve_transactions(self.firm_transactions, confirmed_transactions)
            self.free_transactions = self.sieve_transactions(self.free_transactions, confirmed_transactions)
            self.update_status()
            added = True
        else:
            print(f'Failed to add block with package: {package}')

        return added

    '''
    Transactions
    '''

    def sieve_transactions(self, sieve_list: list, filter_list: list) -> list:
        sieve_index = sieve_list.copy()
        for s in sieve_index:
            if s in filter_list:
                sieve_list.remove(s)
        return sieve_list

    def sort_transactions(self, transaction_list: list) -> list:
        unique_list = []
        for x in transaction_list:
            if x not in unique_list:
                unique_list.append(x)
        return sorted(unique_list, key=lambda k: k['Timestamp'])

    def add_free_transaction(self, receipt: dict):
        if receipt not in self.free_transactions and receipt not in self.firm_transactions:
            self.free_transactions.append(receipt)
            self.free_transactions = self.sort_transactions(self.free_transactions)

    def distribute_transactions(self, node: tuple):
        for receipt in self.free_transactions:
            self.send_transaction_to_node(node, receipt)

    '''
    Consensus
    '''

    def gather_consensus(self):
        '''
        Consensus Algorithm:
            -First, find the greatest index.
            -Add all nodes which have that index to a list
            -From that list, find the hash with highest frequency
            -If there's other hash values with highest frequency, choose the hash with least timestamp
            -Change internal consensus variables
        '''
        '''
        First get the greatest index
        '''
        greatest_index = -1
        for node in self.consensus_dict:
            temp_index = int(self.consensus_dict.get(node).get("INDEX"))
            if temp_index > greatest_index:
                greatest_index = temp_index

        '''
        Find all nodes with greatest index
        '''
        indexed_node_list = []
        for node in self.consensus_dict:
            temp_index = int(self.consensus_dict.get(node).get("INDEX"))
            if temp_index == greatest_index:
                indexed_node_list.append(node)

        '''
        Create hashtime frequency count
        '''

        hash_freq_dict = {}
        for indexed_node in indexed_node_list:
            indexed_hash = self.consensus_dict.get(indexed_node).get("HASH")
            indexed_time = self.consensus_dict.get(indexed_node).get("TIME")
            indexed_hashtime = (indexed_hash, indexed_time)
            if indexed_hashtime in hash_freq_dict.keys():
                hashtime_count = hash_freq_dict.get(indexed_hashtime)
                hash_freq_dict.update({indexed_hashtime: hashtime_count + 1})
            else:
                hash_freq_dict.update({indexed_hashtime: 1})

        '''
        Find a hash with greatest frequency
        '''
        hash_freq = 0
        for k in hash_freq_dict:
            temp_freq = hash_freq_dict.get(k)
            if temp_freq > hash_freq:
                hash_freq = temp_freq

        '''
        Find all hashes with same frequency
        '''
        hashtime_list = [k for k, v in hash_freq_dict.items() if v == hash_freq]

        '''
        Sort duplicates by timestamp
        '''
        (temp_hash, temp_time) = ("", datetime.datetime.max.isoformat())
        for t in hashtime_list:
            (hash, timestamp) = t
            if timestamp < temp_time:
                temp_hash = hash
                temp_time = timestamp

        '''
        Modify consensus variables
        '''
        self.consensus_hash = temp_hash
        self.consensus_time = temp_time
        self.consensus_index = greatest_index

    def achieve_consensus(self):
        '''
        Will interrupt mining to achieve consensus
        TODO: Disable new block events during achieve consensus
        '''
        resume_mining = self.is_mining

        if resume_mining:
            self.stop_miner()
            while self.is_mining:
                pass

        self.match_to_consensus_chain()
        self.get_missing_blocks()
        self.send_status_to_network()

        if resume_mining:
            self.start_miner()

    def match_to_consensus_chain(self):
        '''
        Will modify the chain to match up to greatest index.
        '''

        matching_index = self.get_greatest_matching_index()

        '''If no matching blocks, remove all blocks from chain'''
        if matching_index == -1:
            self.blockchain.chain = []
            self.blockchain.block_count = 0
            self.blockchain.transaction_count = 0

        else:
            '''Otherwise we have at least one matching block'''
            current_index = self.last_block["DATA"]["Index"]
            while current_index > matching_index:
                '''Remove all blocks above the matching index'''
                transaction_count = len(self.last_block["TRANSACTIONS"])
                self.blockchain.chain.pop(current_index)
                self.blockchain.block_count -= 1
                self.blockchain.transaction_count -= transaction_count
                current_index = self.last_block["DATA"]["Index"]

    def get_missing_blocks(self):

        node_modulus = len(self.consensus_nodes)
        node_count = 0
        c_nodes = self.consensus_nodes.copy()

        while int(self.status.get("INDEX")) < self.consensus_index:
            get_node = c_nodes[node_count]
            next_package = self.get_indexed_block_from_node(get_node, int(self.status.get("INDEX") + 1))
            if self.add_block(next_package):
                self.update_status()
            else:
                print(f'\r\nUnable to add package at index {int(self.status.get("INDEX") + 1)}', end='\r\n')
            node_count = (node_count + 1) % node_modulus

    '''
    Event Listener
    '''

    def start_event_listener(self):
        if not self.is_listening:
            self.is_listening = True
            self.listening_thread = threading.Thread(target=self.event_listener)
            self.listening_thread.start()
            print(f'NODE: Event listener started. Active threads: {threading.active_count()}', end='\r\n')
        else:
            print(f'NODE: Event listener already running. Active threads: {threading.active_count()}', end='\r\n')

    def stop_event_listener(self):
        '''
        Stopping the event listener means stopping all activity in the Node.
        We shut down the Miner if it's running and then stop listening.
        We also clear the consensus dict as the info may be out of date if event listener starts up again.
        We finally send a disconnect message to the network, which will mutually remove nodes from the node_list and consensus dict
        '''
        if self.is_mining:
            self.stop_miner()
            print('Closing Miner along with Listener.')
        if self.is_listening:
            print(f'Event listener shutting down within the next {self.LISTENER_TIMEOUT} seconds.')
            print('Sending disconnect message to node network.')
        else:
            print('Event listener not running.')
        self.is_listening = False
        self.disconnect_from_network()
        while self.listening_thread.is_alive():
            pass
        print(f'\r\nNODE: Event listener stopped. Active threads: {threading.active_count()}', end='\r\n')

    def event_listener(self):

        '''
        We start event listener on default port. If port occupied, increase port number by 1 until socket is bound.
        We use a temp socket for if the socket fails to bind, we need to recreate the socket in order to bind correctly.
        We automatically add local addresses to the node list if they are found
        '''
        port_assigned = False
        while not port_assigned:
            try:
                temp_socket = create_socket()
                temp_socket.bind(self.local_node)
                port_assigned = True
            except OSError:
                print(f'Node already running on port {self.node_port} at host address {self.local_host}.',
                      end='\r\n')
                self.node_port += 1
                self.local_node = (self.local_host, self.node_port)

        '''
        Once the port is assigned and the event listener is running we can add our status to the consensus dict
        '''
        self.update_status()

        '''
        The socket has a set timeout - it will listen for events, then timeout and repeat. 
        This is to allow manual stopping of event listener.
        '''
        listening_socket = create_socket()
        listening_socket.settimeout(self.LISTENER_TIMEOUT)
        listening_socket.bind(self.local_node)
        listening_socket.listen()

        '''
        The event listener will continue listening until manually stopped.
        Each new event will create a new event thread which will handle the event.
        '''
        while self.is_listening:
            try:
                event, addr = listening_socket.accept()
                event_thread = threading.Thread(target=self.handle_event, args=(event, addr,))
                event_thread.start()
            except socket.timeout:
                pass
        print(f'\r\nClosing event listener for node: {self.local_node}.', end='\r\n')
        close_socket(listening_socket)

    '''
    Event Handler   
    '''

    def handle_event(self, event, addr):
        event_dict = receive_data(event)
        data_type = next(iter(event_dict))
        data = event_dict[data_type]

        print(f'Event handler triggered of type {data_type}. Active threads: {threading.active_count()}', end='\r\n')

        if data_type == "node":
            self.node_connect_event(event, data)
        elif data_type == "network":
            self.network_connect_event(event, data)
        elif data_type == "disconnect":
            self.disconnect_event(event, data)
        elif data_type == "transaction":
            self.new_transaction_event(event, data)
        elif data_type == "get transactions":
            self.get_transaction_event(event, data)
        elif data_type == "new block":
            self.new_block_event(event, data)
        elif data_type == "status":
            self.status_event(event, data)
        elif data_type == "indexed block":
            self.indexed_block_event(event, data)
        elif data_type == "hashmatch":
            self.hash_match_event(event, data)
        else:
            print(f'\r\n{data_type} event receieved from {addr}.', end='\r\n')
            print(f'\r\r{data} received from {addr}')

    '''
    Events
    '''

    '''Connect/Disconnect Events'''

    def node_connect_event(self, client: socket, node: list):
        new_node = list_to_node(node)
        if new_node not in self.node_list:
            self.node_list.append(new_node)
            print(f'Node connection receieved from {new_node}', end='\r\n')
        package_and_send_data(client, "confirm", self.local_node)

    def network_connect_event(self, client: socket, node: list):
        package_and_send_data(client, "node list", self.node_list)
        self.node_connect_event(client, node)
        new_node = list_to_node(node)
        print(f'Node list returned to {new_node}.', end='\r\n')

    def disconnect_event(self, client: socket, node: list):
        new_node = list_to_node(node)
        if new_node in self.node_list:
            self.node_list.remove(new_node)
        if new_node in self.consensus_dict.keys():
            self.consensus_dict.pop(new_node)
        package_and_send_data(client, "confirm", self.local_node)
        print(f'Disconnect received from {node}. Removing from network.', end='\r\n')

    '''Transaction Events'''

    def new_transaction_event(self, client: socket, receipt: dict):
        self.add_free_transaction(receipt)
        package_and_send_data(client, "confirm", self.local_node)
        print(f'Transaction event confirmed.', end='\r\n')

    def get_transaction_event(self, client: socket, node: list):
        new_node = list_to_node(node)
        package_and_send_data(client, "confirm", True)
        self.distribute_transactions(new_node)

    '''Block Events'''

    def new_block_event(self, client: socket, package: dict):
        '''
        A new block event means we are sent a block from another node.
        We will need to verify the status of those nodes which don't have the current block.
        '''
        resume_mining = self.is_mining
        if resume_mining:
            self.stop_miner()
            while self.is_mining:
                pass

        if self.add_block(package):
            package_and_send_data(client, "confirm", True)

        else:
            package_and_send_data(client, "confirm", False)

        '''Send new status to all nodes'''
        self.send_status_to_network()

        if resume_mining:
            self.start_miner()

    def indexed_block_event(self, client: socket, index: int):
        try:
            return_package = self.blockchain.chain[index]
            package_and_send_data(client, "indexed block", return_package)
        except IndexError:
            package_and_send_data(client, "index error", {})

    '''Status Events'''

    def status_event(self, client: socket, status: dict):
        node_as_list, status_dict = status
        node = list_to_node(node_as_list)
        self.consensus_dict.update({node: status_dict})
        package_and_send_data(client, "status", [node_to_list(self.local_node), self.status])

        self.gather_consensus()
        if self.local_node not in self.consensus_nodes:
            self.achieve_consensus()
        else:
            lagging_nodes = []
            for node in self.node_list:
                if node not in self.consensus_nodes:
                    lagging_nodes.append(node)

            for node in lagging_nodes:
                self.send_status_to_node(node)

    '''Hash Match Event'''

    def hash_match_event(self, client: socket, hash_list: list):
        min_length = min(len(hash_list), len(self.hashlist))
        match_index = -1
        for x in range(0, min_length):
            if hash_list[x] == self.hashlist[x]:
                match_index += 1
        package_and_send_data(client, "match index", match_index)

    '''*****************End of Events**************************'''

    '''
    Connect and Disconnect
    '''

    def connect_to_node(self, node: tuple):
        '''
        Connect to a specific node and exchange addresses.
        '''
        try:
            node_socket = create_socket()
            node_socket.connect(node)
            package_and_send_data(node_socket, "node", self.local_node)
            confirm_dict = receive_data(node_socket)
            confirm_node = list_to_node(confirm_dict.get("confirm"))
            if node == confirm_node and node not in self.node_list:
                self.node_list.append(node)
            print(f'Successfully exchanged addresses with node {node}', end='\r\n')
            close_socket(node_socket)

        except ConnectionRefusedError:
            print(f'Unable to connect to node at address: {node}', end='\r\n')

    def connect_to_network(self, node: tuple):
        '''
        Connect to a specific node, get its node list and exchange addresses with all new nodes.
        Event listener must be running to connect
        '''
        new_nodes = []
        '''
        Get Node List and Exchange Node Address
        '''
        if node != self.local_node and self.is_listening:
            try:
                network_socket = create_socket()
                network_socket.connect(node)
                package_and_send_data(network_socket, "network", self.local_node)

                '''Get Node List'''
                node_list_dict = receive_data(network_socket)
                for L in node_list_dict.get("node list"):
                    new_node = list_to_node(L)
                    if new_node not in self.node_list and new_node != self.local_node:
                        self.node_list.append(new_node)
                        new_nodes.append(new_node)

                confirm_dict = receive_data(network_socket)
                confirm_node = list_to_node(confirm_dict.get("confirm"))
                if node == confirm_node and node not in self.node_list:
                    self.node_list.append(node)
                print(f'Node list obtained successfully from {node}.', end='\r\n')
                close_socket(network_socket)

            except ConnectionRefusedError:
                print(f'Unable to connect to node at address: {node}', end='\r\n')

            '''
            Exchange Addresses with all new nodes
            '''

            for node in new_nodes:
                try:
                    self.connect_to_node(node)
                except ConnectionRefusedError:
                    print(f'Unable to connect to node at address: {node}', end='\r\n')

            '''
            Send existing free transactions to network
            '''
            for receipt in self.free_transactions:
                self.send_transaction_to_network(receipt)

            '''
            Get all free transactions from node
            '''
            self.get_transactions_from_node(node)

            '''
            Catch up to network
            '''
            self.achieve_consensus()

            print(f'Successfully connected to network with nodes: {self.node_list}', end='\r\n')
        elif node == self.local_node:
            print(f'{node} is the local node. Cannot use to connect to wider network.', end='\r\n')
        elif not self.is_listening:
            print('Event listener not running.', end='\r\n')

    def disconnect_from_network(self):
        '''
        Send disconnect message to all nodes. Remove node from node list once confirmed.
        '''
        for node in self.node_list:
            try:
                disconnect_socket = create_socket()
                disconnect_socket.connect(node)
                package_and_send_data(disconnect_socket, "disconnect", self.local_node)
                confirm_dict = receive_data(disconnect_socket)
                confirm_host, confirm_port = confirm_dict.get("confirm")
                confirm_node = (confirm_host, confirm_port)
                print(f'\r\nLocal node address removed from node @ {confirm_node}.', end='\r\n')
                close_socket(disconnect_socket)
            except ConnectionRefusedError:
                print(f'Unable to connect to node at {node}.')
        self.node_list = []
        self.consensus_dict = {}

    '''
    Send to Network
    '''

    def send_transaction_to_network(self, receipt: dict):
        for node in self.node_list:
            self.send_transaction_to_node(node, receipt)

    def send_block_to_network(self, package: dict):
        for node in self.node_list:
            self.send_block_to_node(node, package)

    def send_status_to_network(self):
        for node in self.node_list:
            self.send_status_to_node(node)

    '''
    Send to Node
    '''

    def send_transaction_to_node(self, node: tuple, receipt: dict):
        try:
            send_socket = create_socket()
            send_socket.connect(node)
            package_and_send_data(send_socket, "transaction", receipt)
            confirm_dict = receive_data(send_socket)
            confirm_node = list_to_node(confirm_dict.get("confirm"))
            if confirm_node == node:
                print(f'Transaction sent successfully to {node}', end='\r\n')
            close_socket(send_socket)
        except ConnectionRefusedError:
            print(f'Unable to send transaction to {node}.', end='\r\n')

    def send_block_to_node(self, node: tuple, package: dict):
        try:
            send_socket = create_socket()
            send_socket.connect(node)
            package_and_send_data(send_socket, "new block", package)
            confirm_dict = receive_data(send_socket)
            confirm_bool = bool(confirm_dict.get("confirm"))
            if confirm_bool:
                print(f'New block added successfully to the chain in node {node}', end='\r\n')
            else:
                print(f'New block failed to be added to the chain in node {node}', end='\r\n')
            close_socket(send_socket)
        except ConnectionRefusedError:
            print(f'Unable to send block to node {node}')

    def send_status_to_node(self, node: tuple):
        try:
            send_socket = create_socket()
            send_socket.connect(node)
            package_and_send_data(send_socket, "status", [node_to_list(self.local_node), self.status])
            confirm_dict = receive_data(send_socket)
            node_as_list, status_dict = confirm_dict.get("status")
            self.consensus_dict.update({list_to_node(node_as_list): status_dict})
            print(f'\r\nSuccessfully exchanged statuses with {list_to_node(node_as_list)}', end='\r\n')
            close_socket(send_socket)
        except ConnectionRefusedError:
            print(f'Unable to send status to node {node}', end='\r\n')

    '''
    Request from Node
    '''

    def get_transactions_from_node(self, node: tuple):
        try:
            get_socket = create_socket()
            get_socket.connect(node)
            package_and_send_data(get_socket, "get transactions", self.local_node)
            confirm_dict = receive_data(get_socket)
            print(f'Free transactions requested from node {node} returned with status {confirm_dict.get("confirm")}')
            close_socket(get_socket)
        except ConnectionRefusedError:
            print(f'Unable to get transactions from node: {node}', end='\r\n')

    def get_indexed_block_from_node(self, node: tuple, index: int):
        block_package = {}
        try:
            get_socket = create_socket()
            get_socket.connect(node)
            package_and_send_data(get_socket, "indexed block", index)
            return_dict = receive_data(get_socket)
            return_key = next(iter(return_dict))
            if return_key == "indexed block":
                print(f'Retrieve block at index {index} from {node} successfully.', end='\r\n')
                block_package = return_dict.get(return_key)
            else:
                print(f'Failed to retrieve block at index {index} from {node} successfully.', end='\r\n')

        except ConnectionRefusedError:
            print(f'Unable to connect to {node} to retrieve index {int} block', end='\r\n')

        return block_package

    '''
    Hashlist Exchange
    '''

    def get_greatest_matching_index(self):
        '''
        We iterate over every consensus node until we connect.
        Then from a consensus node we find the greatest index for which the two hashlist's match
        Return the greatest index value
        '''

        '''First get consensus to update the consensus nodes'''
        self.gather_consensus()

        match_index = -1
        index_found = False
        node_count = 0
        while not index_found and node_count < len(self.consensus_nodes):
            node = self.consensus_nodes[node_count]
            if node != self.local_node:
                try:
                    get_socket = create_socket()
                    get_socket.connect(node)
                    package_and_send_data(get_socket, "hashmatch", self.hashlist)
                    index_dict = receive_data(get_socket)
                    # print(f'\r\nReceived hashmatch return dict: {index_dict}', end='\r\n')
                    match_index = index_dict.get("match index")
                    print(f'Match index obtained from node {node}. It is: {match_index}.', end='\r\n')
                    close_socket(get_socket)
                    index_found = True
                except ConnectionRefusedError:
                    print(f'Unable to get index from consensus node {node}. Trying another.', end='\r\n')
                    node_count += 1
            else:
                node_count += 1

        if self.consensus_nodes == [self.local_node] and self.last_block != []:
            return self.last_block["DATA"]["Index"]
        else:
            return match_index

    '''
    Testing
    '''

    def generate_transactions(self, n=1):
        for x in range(0, n):
            wally = Wallet()
            sample_transaction = Transaction(self.local_address, wally.address,
                                             np.random.randint(1, self.mining_reward))
            signature = sample_transaction.sign_transaction(self.local_wallet._Wallet__private_key)
            receipt = sample_transaction.receipt(signature)
            self.add_free_transaction(receipt)
            self.send_transaction_to_network(receipt)
        print(f'{n} transaction(s) generated.', end='\r\n')


'''********************************************************'''
'''
Helper functions
    We can't send a tuple as its not JSON serializable.
    So to send nodes, we have to send as a list.
'''


def node_to_list(node: tuple):
    host, port = node
    return [host, port]


def list_to_node(node_as_list: list):
    host, port = node_as_list
    return (host, port)
