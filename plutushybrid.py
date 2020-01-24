import binascii
import mnemonic
import bip32utils
import random
import os
import sys
import pickle
import hashlib
import multiprocessing
from mnemonic import Mnemonic
from random import choice, seed
from binascii import hexlify, unhexlify

DATABASE = r'database/JAN_13_2020/'   

def b2h(b):
    h = hexlify(b)
    return h if sys.version < "3" else h.decode("utf8")

def generate_new():
    mnemo = Mnemonic("english")
    data = "".join(chr(choice(range(0, 256))) for _ in range(8 * (0 % 3 + 2)))
    if sys.version >= "3":
        data = data.encode("latin1")
    data = b2h(data)
    mnemonic_words = mnemo.to_mnemonic(unhexlify(data))
    return mnemonic_words
  
def generate_private_key(mnemonic_words):
    mobj = mnemonic.Mnemonic("english")
    seed = mobj.to_seed(mnemonic_words)
    bip32_root_key_obj = bip32utils.BIP32Key.fromEntropy(seed)
    bip32_child_key_obj = bip32_root_key_obj.ChildKey(
        44 + bip32utils.BIP32_HARDEN
    ).ChildKey(
        0 + bip32utils.BIP32_HARDEN
    ).ChildKey(
        0 + bip32utils.BIP32_HARDEN
    ).ChildKey(0).ChildKey(0)
    return bip32_child_key_obj.WalletImportFormat()
    
def generate_address(mnemonic_words):
    mobj = mnemonic.Mnemonic("english")
    seed = mobj.to_seed(mnemonic_words)
    bip32_root_key_obj = bip32utils.BIP32Key.fromEntropy(seed)
    bip32_child_key_obj = bip32_root_key_obj.ChildKey(
        44 + bip32utils.BIP32_HARDEN
    ).ChildKey(
        0 + bip32utils.BIP32_HARDEN
    ).ChildKey(
        0 + bip32utils.BIP32_HARDEN
    ).ChildKey(0).ChildKey(0)
    return bip32_child_key_obj.Address()

def process(new, private_key, address, database):
	"""
	Accept an address and query the database. If the address is found in the 
	database, then it is assumed to have a balance and the wallet data is 
	written to the hard drive. If the address is not in the database, then it 
	is assumed to be empty and printed to the user.
	Average Time: 0.0000026941 seconds
	"""
	if address in database[0] or \
	   address in database[1] or \
	   address in database[2] or \
	   address in database[3]:
		with open('KEYS.txt', 'a') as file:
			file.write('Private Key: ' + str(private_key) + '\n' +
				   'Word Seed: ' + str(new) + '\n' +
			           'address: ' + str(address) + '\n\n')                      
	else: 
		print('Address = ', str(address), '\n', 'Private Key = ', str(private_key), '\n', 'Seed = ', str(new))

def main(database):
	"""
	Create the main pipeline by using an infinite loop to repeatedly call the 
	functions, while utilizing multiprocessing from __main__. Because all the 
	functions are relatively fast, it is better to combine them all into 
	one process.
	"""
	while True:
		new = generate_new()			# 0.0000061659 seconds
		private_key = generate_private_key(new) 	# 0.0031567731 seconds
		address = generate_address(new)		# 0.0000801390 seconds
		process(new, private_key, address, database) 
		
if __name__ == '__main__':
	"""
	Deserialize the database and read into a list of sets for easier selection 
	and O(1) complexity. Initialize the multiprocessing to target the main 
	function with cpu_count() concurrent processes.
	"""
	database = [set() for _ in range(4)]
	count = len(os.listdir(DATABASE))
	half = count // 2
	quarter = half // 2
	for c, p in enumerate(os.listdir(DATABASE)):
		print('\rreading database: ' + str(c + 1) + '/' + str(count), end = ' ')
		with open(DATABASE + p, 'rb') as file:
			if c < half:
				if c < quarter: database[0] = database[0] | pickle.load(file)
				else: database[1] = database[1] | pickle.load(file)
			else:
				if c < half + quarter: database[2] = database[2] | pickle.load(file)
				else: database[3] = database[3] | pickle.load(file)
	print('DONE')

	# To verify the database size, remove the # from the line below
	#print('database size: ' + str(sum(len(i) for i in database))); quit()

	for cpu in range(multiprocessing.cpu_count()):
		multiprocessing.Process(target = main, args = (database, )).start()
