import Crypto.encryption

import nacl.secret
from os import urandom

def test_encryption():
    """ Test the encryption module. """

    tests_passed = 0
    tests_total = 0

    CORRECT_KEY_SIZE = nacl.secret.SecretBox.KEY_SIZE
    print("Testing key size identification...")
    tests_total += 2
    try:
        test_encryptor = Crypto.encryption.Encryption(urandom(CORRECT_KEY_SIZE - 1))
    except:
        tests_passed += 1

    test_encryptor = Crypto.encryption.Encryption(urandom(CORRECT_KEY_SIZE))
    if isinstance(test_encryptor, Crypto.encryption.Encryption):
        tests_passed += 1

    print("Testing encryption...")
    tests_total += 3
    test_message = urandom(2048)
    encrypted_message = test_encryptor.encrypt(test_message)
    decrypted_message = test_encryptor.decrypt(encrypted_message)
    if decrypted_message == test_message:
        tests_passed += 1

    invalid_message = "123"
    try:
        invalid_encryption = test_encryptor.encrypt(invalid_message)
    except:
        tests_passed += 1

    try:
        invalid_decryption = test_encryptor.decrypt(invalid_message)
    except:
        tests_passed += 1

    print("encryption passed {}/{} tests.".format(tests_passed, tests_total))

    return tests_passed

if __name__ == '__main__':
    test_encryption()
