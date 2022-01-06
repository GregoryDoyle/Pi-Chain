'''
The Blockchain class
'''

from block import Block, package_block
import numpy as np
import pandas as pd

pd.options.display.float_format = '{:,.0f}'.format


class Blockchain:
    MINING_REWARD = 10
    MINING_DIFFICULTY = 6

    def __init__(self):
        self.chain = []
        self.block_count = 0
        self.transaction_count = 0
        self.ledger = pd.DataFrame([["MINE", np.Inf]], columns=['Address', 'Amount'])

    '''
    Blockchain properties
    '''

    @property
    def last_block(self):
        if self.chain != []:
            return self.chain[-1]
        else:
            return []

    '''
    Add new block    
    '''

    def add_block(self, block: Block, proof: str):
        print(f'Attempting to add block # {self.block_count + 1} to the chain.', end='\r\n')

        if self.last_block != []:
            if block.previous_hash != self.last_block["DATA"]["Block Hash"]:
                print(
                    f'Previous hash failure. Previous hash in new block {block.previous_hash}. Previous hash in the blockchain last block: {self.last_block["DATA"]["Block Hash"]}')
                return False
        else:
            if block.previous_hash != "" or block.index != 0:
                print(f'Trying to add non-genesis block as first block in chain.')
                return False
        if not proof.startswith("0" * self.MINING_DIFFICULTY) and proof == block.compute_hash():
            print(f'Proof failure. Submitted proof: {proof}. Block hash: {block.compute_hash()}')
            return False

        self.chain.append(package_block(block, proof))
        self.block_count += 1
        self.update_ledger()
        print(f'Block added to chain successfully. Total blocks in chain: {self.block_count}', end='\r\n')
        return True

    '''
    Ledger Methods
    '''

    def consolidate_ledger(self, ledger: pd.DataFrame):
        alias_list = list(ledger['Address'])
        alias_list.remove("MINE")
        for alias in alias_list:
            temp_df = ledger.loc[ledger['Address'] == alias]
            final_amount = int(temp_df['Amount'].sum())
            final_row = pd.DataFrame([[alias, final_amount]], columns=['Address', 'Amount'])
            ledger = ledger.drop(ledger.index[ledger['Address'] == alias])
            ledger = ledger.append(final_row, ignore_index=True)
        return ledger

    def update_ledger(self):
        '''
        When a new block is added to the chain, it will contain valid transactions.
        Thus, we need only to enact the transactions in the list, that is, debit the receiver and credit the sender.
        At the end we consolidate the ledger by accruing all transactions for a given address
        '''
        temp_transactions = self.last_block["TRANSACTIONS"]
        for receipt in temp_transactions:
            sender_alias = receipt.get("Sender")
            receiver_alias = receipt.get("Receiver")
            exchange_amount = receipt.get("Amount")

            debit = pd.DataFrame([[receiver_alias, exchange_amount]], columns=['Address', 'Amount'])
            credit = pd.DataFrame([[sender_alias, -1 * exchange_amount]], columns=['Address', 'Amount'])

            if sender_alias == "MINE":
                self.ledger = self.ledger.append(debit, ignore_index=True)
                self.ledger = self.consolidate_ledger(self.ledger)
            else:
                self.ledger = self.ledger.append(credit, ignore_index=True)
                self.ledger = self.ledger.append(debit, ignore_index=True)
                self.ledger = self.consolidate_ledger(self.ledger)
            self.transaction_count += 1

    '''
    Validate Transactions
    '''

    def validate_transactions(self, transactions: list):
        '''
        A transaction will be considered valid if the sender in the ledger has sufficient funds
        We will keep a local ledger of the transactions, as an earlier transaction may affect a later transaction
        This local ledger will be temporary, as the transactions may be accepted in a block not mined by the node
        The blockchain ledger is only updated when a block is added
        Validate transactions will be called on a list of transactions (dicts) which will be added to the chain.
        This list of transactions will include the mining transaction, and later transactions can depend on the mining reward.
        Those transactions which are dependent on the miner reward may be rejected by other nodes.
        '''
        local_ledger = self.ledger.copy()
        firm_transactions = []
        for receipt in transactions:
            sender_alias = receipt.get("Sender")
            receiver_alias = receipt.get("Receiver")
            exchange_amount = receipt.get("Amount")
            signature = receipt.get("Signature")

            debit = pd.DataFrame([[receiver_alias, exchange_amount]], columns=['Address', 'Amount'])
            credit = pd.DataFrame([[sender_alias, -1 * exchange_amount]], columns=['Address', 'Amount'])

            if sender_alias == "MINE":
                local_ledger = local_ledger.append(debit, ignore_index=True)
                local_ledger = self.consolidate_ledger(local_ledger)
                firm_transactions.append(receipt)
            else:
                alias_list = list(local_ledger['Address'])
                if sender_alias in alias_list:
                    sender_amount = int(local_ledger.loc[local_ledger['Address'] == sender_alias]['Amount'])
                    if sender_amount >= exchange_amount:
                        local_ledger = local_ledger.append(credit, ignore_index=True)
                        local_ledger = local_ledger.append(debit, ignore_index=True)
                        local_ledger = self.consolidate_ledger(local_ledger)
                        firm_transactions.append(receipt)
                    else:
                        print(f'Insufficient funds for sender: {sender_alias}', end='\r\n')
                        print(f'Rejecting transaction with signature: {signature}', end='\r\n\n')

                else:
                    print(f'Sender {sender_alias} not found in ledger.')
                    print(f'Rejecting transaction with signature: {signature}', end='\r\n\n')

        return firm_transactions
