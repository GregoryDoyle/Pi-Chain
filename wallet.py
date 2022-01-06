'''
The Wallet Class
'''

from cryptomath import generate_keys
from hashlib import sha1, sha256


class Wallet:

    def __init__(self, prime_digits=6):
        key_dict = generate_keys(prime_digits)
        self.public_key = key_dict.get("Public key")
        self.__private_key = key_dict.get("Private key")

        (e, n) = self.public_key
        d = self.__private_key

        self.address = sha1(sha256(str(d * e % n).encode()).hexdigest().encode()).hexdigest()
