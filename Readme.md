<center>
    <H1>π-Chain: An object-oriented blockchain.</H1>
    <h2> Written in Python, designed for big data.</h2>
</center>

This is the readme file for π-chain. We will go over the design briefly so we can understand the flow of events.

<h3>Addresses</h3>
We use the RSA encryption scheme to determine the π-address. From RSA we generate a public key (e,n) and a private key
d, where n = p*q, and d * e = 1 (mod (p-1)(q-1)). The values p and q are prime, and given n, solving for p and q is
difficult.

The address is then calculated to be the sha1 hash value (a hash similar to MD5) of the 'numeric address' which is d *
e (mod n).

For each address, the primes used are generated randomly among a list of n-digit primes. The greater the number of n,
the more secure the address will be. The default prime digit length is 6.

Finally, we can generate a MINE specific address for use in the blockchain by instantiating with is_miner = True.

<h3>Transactions</h3>
A Transaction will be an object containing a sender address, a receiver address, an amount and a timestamp when created.
Each transaction will also contain a digital signature, which will be the hash value of the object dictionary. The
signature will not be part of the object, but will be included in the transaction receipt for security.

For ease of use, the receipt will be a dict type containing all the object variables along with the receipt. As the
timestamp is included in the signature, no two transactions can be the same.

<h3>Block</h3>
The Block class will contain a list of transaction receipts, along with some pertinent identifying information: index in
the chain, previous block hash, nonce, host address and creation timestamp. The block will be saved onto the chain as a
dictionary containing DATA and TRANSACTIONS keys.

The TRANSACTIONS key will return a list of transaction receipts, which are of dict type.

The DATA key will contain a dict of all identifying information about the block, including the block hash. The block
hash must be included when the block is to be added to the chain. When the block is saved into DATA and TRANSACTION
dictionaries, it is said to be packaged. The Block class will also contain static methods used to package the block and
unpack the package back into a Block object.

The Blocks in the chain will be indexed, so the block at index n will contain the previous hash of block n-1. The sole
exception is the genesis block, which will have index = 0 and previous_hash = "".

<h3>Blockchain</h3>
The Blockchain object acts as a datastore for Blocks, which contain a list of transaction receipts. Each Blockchain
instance will be able to add a new block provided it meets the blockchain proof requirements, and will keep a running
ledger of all transactions saved to the chain.

When a new Blockchain object is instantiated, we create a ledger for the blockchain. With no blocks added, this ledger
will contain only the Mine address. Otherwise, the ledger will contain a copy of the result of each transaction, with an
amount value given for each address on the chain. Whenever a new block is added to the chain, the ledger gets updated
with the included transactions.

Before a new Block is mined, the Blockchain will validate the list of transactions by creating a copy of the running
ledger, then verifying each transaction against this ledger in turn. Note that the list of transactions is expected to
contain a MINE transaction, as transactions are validated only before being saved in a Block. Those transactions which
are rejected are returned, along with the validated transactions.

<h3>Node</h3>

The Node is the communications hub for the Blockchain. A Node will run an instance of the Blockchain, and communicate
with all other Nodes. Further, each Node will be able to accept Transactions from a client.

The Node will be responsible for adding Blocks to the Blockchain. Either a Node will mine a new block (see Miner below)
or a Node will receive a block update from another node. If the block update received can be added to the chain, then it
is added and propagated through the network. Otherwise, if the Block fails to be added, the two Nodes are out of sync,
and rectification of the chain must occur.

A new Node is instantiated with an empty Blockchain. We give the Node object some properties which belong to the
Blockchain, such as last_block and ledger.

The Node will handle communication with the network, and so we instantiate using the local host of the user along with
port 41000. Each Node will communicate with one another over this port. Further, each Node will run an event listener,
to handle communication from the other Nodes. This event listener will run in its own thread, and will spawn a new
thread for each event received from the network. We emphasize that we need the event handler running in a single thread
to maintain the communication pipe with the client.

By default the Node starts with the event listener turned <b>off</b>
and it must be manually started.

Each Node has the capability to run as a Miner, and so a Miner object is created when a Node is instantiated. However,
the Miner will be <b>TURNED OFF</b> to start, and so will need to be enabled by the user.

<h3>Miner</h3>
The Miner object will be instantiated by the Node. When the Node submits a Block to the Miner, the Miner will use this
Block in its proof of work calculations. Either the Miner will finish its proof of work or it will be interrupted. In
both cases, the Miner will return the Block being mined along with its current nonce. If the Miner is interrupted, it
returns an empty string. Otherwise, if the Miner is successful, it will return the hash value satisfying the
proof-of-work conditions.





<center>
    <H2>Flow of events</H2>
</center>

Suppose we have a Node N running as a Miner. Whenever N receieves a Transaction T, it is placed into the "free
transaction" pool. N will look to propagate this transaction to as many other nodes as possible.

Whenver N begins to mine a new block, it will take all the free transactions, append a mining transaction, and validate
these transactions against the blockchain. Those transactions which are valid will be taken from free transactions and
placed in the "firm transactions" list. Any transaction found invalid by the Blockchain will be removed.

If N successfully mines a new Block, then the firm transactions are saved to the chain, and so we clear the firm
transactions list. If N instead receives a new Block updated, then N's firm transactions are compared against the new
Block - any in the new Block are removed from the firm transactions list. Once all of the firm transactions have been
checked against the new Block, they are returned to the free transaction pool, and the firm transaction list is cleared.



<center>
    <h2>Interaction between Node and Miner</h2>
</center>

The Node instantiates a Miner instance, and will call Miner.mine_block(). The mine_block function will run under the
condition that the proof has has not been found and Miner.is_mining = True. The Node can Miner.stop_mining() which acts
as an interrupt to the Miner. The Miner will return an empty string as proof hash, which will be handled gracefully by
the Node.

The Node will run the mine function in its own thread. 








