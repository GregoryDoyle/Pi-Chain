'''
A module for all mathematical cryptographic methods used in the π-Chain
'''

from math import sqrt, floor
import pandas as pd
import numpy as np
import os

'''
Mathematical Methods
'''


def is_prime(n: int) -> bool:
    '''
    Returns True if n is prime, false otherwise.
    Uses trial division method.
    '''
    if type(n) != int:
        return False
    if n == 2:
        return True
    if n <= 1 or n % 2 == 0:
        return False

    for x in range(3, int(sqrt(n) + 1), 2):
        if n % x == 0:
            return False
    return True


def is_square(n: int) -> bool:
    '''
    Returns true if n is a square, False otherwise.
    '''
    if type(n) != int or n < 0:
        return False
    root = int(sqrt(n))
    if root ** 2 == n:
        return True
    return False


def fermat_factor(n: int) -> list:
    '''
    Factors using Fermat's method. Returns a list of 2 factors.
    '''
    if is_prime(n) == True:
        return [1, n]
    root = int(sqrt(n))
    for x in range(root, n):
        factor = x ** 2 - n
        if is_square(factor) == True:
            p = x - int(sqrt(factor))
            q = x + int(sqrt(factor))
            return [p, q]


def gcd(a: int, b: int) -> int:
    '''
    Returns the greatest common divisor of a and b. Follows the euclidean algorithm.
    '''
    a = abs(a)
    b = abs(b)  # units don't matter
    if a == 0 and b == 0:
        return 0
    if a == 0 and b != 0:
        return b
    if a != 0 and b == 0:
        return a
    d = 1  # divisor
    if a > b:
        t = a
        a = b  # we ensure that a <= b
        b = t  # t = a, a -> b, b-> t = a(original value)
    while d != 0:
        d = b % a  # d = b (mod a)
        t = a  # then calculate a (mod d)
        a = d  # until we find a divisor
        b = t
    return b


def generate_primelist(prime_digits=6):
    '''
    We generate a list of primes having prime_digits and save it to disk.
    '''
    filename = "primelist{0}.csv".format(prime_digits)
    print('Generating list of primes.', end='\r\n')
    prime_list = []
    primelength = 10 ** prime_digits
    num = 10 ** (prime_digits - 1)
    while num < primelength:
        if is_prime(num) == True:
            prime_list.append(num)
        pctdone = int(num / primelength * 100)
        print(str(pctdone) + "% percent done", end='\r')
        num += 1
    print(f'{prime_digits}-digit list of primes generated.', end='\r\n')
    prime_df = pd.DataFrame(prime_list)
    prime_df.to_csv(filename, index=False)


'''
RSA Encryption
'''


def generate_keys(prime_digits=6) -> dict:
    '''
    We generate a public and private RSA key and return it as a dict of these values.
    '''
    filename = "primelist{0}.csv".format(prime_digits)
    if os.path.isfile(filename) == False:
        generate_primelist(prime_digits)
    prime_df = pd.read_csv(filename)
    length = len(prime_df.index)
    p = int(prime_df.iloc[np.random.randint(0, length)]['0'])
    q = p
    while q == p:
        q = int(prime_df.iloc[np.random.randint(0, length)]['0'])
    phi_n = (p - 1) * (q - 1)
    ##Find e and d
    e = 0
    while gcd(e, phi_n) != 1:
        e = np.random.randint(1, phi_n)
    d = pow(e, -1, mod=phi_n)
    n = p * q
    key_dict = {"Public key": (e, n), "Private key": d}
    return key_dict
