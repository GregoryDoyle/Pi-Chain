'''
The Transaction class.
'''

from wallet import Wallet

from hashlib import sha256
import json, datetime


class Transaction:
    '''

    '''

    def __init__(self, sender: str, receiver: str, amount: int):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    def sign_transaction(self, sender_key: int):
        self.sender_key = sender_key
        return sha256(json.dumps(self.__dict__, sort_keys=True).encode()).hexdigest()

    def receipt(self, signature):
        '''
        Readable package
        '''
        if self.sender == "MINE":
            alias = "MINE"
        else:
            alias = self.sender

        return {"Amount": self.amount, "Sender": alias, "Receiver": self.receiver,
                "Timestamp": self.timestamp, "Signature": signature}

    def verify_transaction(self, sender_key: int, signature: str):
        try:
            assert self.sender_key == sender_key
        except AttributeError:
            print(f'Transaction hasn\'t been signed yet.', end='\r\n')
            return False
        except AssertionError:
            print(f'Private key failure for {sender_key}', end='\r\n')
            return False

        try:
            assert signature == sha256(json.dumps(self.__dict__, sort_keys=True).encode()).hexdigest()
        except AssertionError:
            print(f'Signature dictionaries don\'t match.', end='\r\n')
            return False

        return True
