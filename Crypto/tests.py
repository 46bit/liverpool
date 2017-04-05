import Crypto.encryption

import nacl.secret
from os import urandom, remove

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
    plain_text_sizes = [0, 2048, 2048576]
    tests_total += len(plain_text_sizes)
    for s in plain_text_sizes:
        test_message = urandom(s)
        encrypted_message = test_encryptor.encrypt(test_message)
        decrypted_message = test_encryptor.decrypt(encrypted_message)
        if decrypted_message == test_message:
            tests_passed += 1

    tests_total += 2
    invalid_message = "123"
    try:
        invalid_encryption = test_encryptor.encrypt(invalid_message)
    except:
        tests_passed += 1

    try:
        invalid_decryption = test_encryptor.decrypt(invalid_message)
    except:
        tests_passed += 1

    print("Testing key derivation.")
    tests_total += 3
    test_keys_strs = ["111", "11111111111111111111111111111111", "1111111111111111111111111111111111111111111111111111111111111111"]
    test_keys_bytes = [str.encode(i) for i in test_keys_strs]
    invalid_test_key = 123
    size = nacl.secret.SecretBox.KEY_SIZE
    if all(map(lambda x: len(x) == size, (map(test_encryptor.derive_32_byte_key, test_keys_strs)))):
        tests_passed += 1
    if all(map(lambda x: len(x) == size, (map(test_encryptor.derive_32_byte_key, test_keys_bytes)))):
        tests_passed += 1

    try:
        test_encryptor.derive_32_byte_key(invalid_test_key)
    except:
        tests_passed += 1

    print("encryption passed {}/{} tests.".format(tests_passed, tests_total))

    return tests_passed


def test_file():

    print("Testing file encrytions...")
    test_file = open("temp.txt",'wb+')
    test_text = str.encode("This is a test.\nThis is a test.")
    test_key = urandom(32)
    test_encryptor = Crypto.encryption.Encryption(test_key)
    encrypted_text = test_encryptor.encrypt(test_text)
    test_file.write(encrypted_text)
    test_file.close()
    test_file = open("temp.txt",'rb')
    test_file_content = test_file.read()
    test_decryptor = Crypto.encryption.Encryption(test_key)
    test_read = test_decryptor.decrypt(test_file_content)
    test_file.close()
    remove("temp.txt")
    if test_read == test_text:
        print("File operations passed 1/1 test.")
        return 1
    else:
        return 0

if __name__ == '__main__':
    test_encryption()
    test_file()
