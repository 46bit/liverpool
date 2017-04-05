import nacl.secret
import nacl.utils
import nacl.hash
import nacl.encoding

import sys
import base64
from time import gmtime, strftime

class Encryption:

    def __init__(self, key_bytes):
        """ Initialise an encryptor, requires a 32-byte key.
            Raises RuntimeError if key size is invalid. """

        key_size = nacl.secret.SecretBox.KEY_SIZE
        if len(key_bytes) != key_size:
            self.raise_error("Invalid size of encryption key, correct size is " + str(key_size))

        self.__key_bytes = key_bytes
        self.__secret_box = nacl.secret.SecretBox(self.__key_bytes)


    def encrypt(self, file_bytes):
        """ Encrypt the input file in bytes with the encryptor's
            encryption key, return the output bytes with the nounce
            included.
        """

        if not isinstance(file_bytes, bytes):
            self.raise_error("Data being encrypted is not in bytes.")
        file_b64 = base64.b64encode(file_bytes)

        return self.__secret_box.encrypt(file_b64, encoder=nacl.encoding.Base64Encoder)


    def decrypt(self, encrypted_bytes):
        """ Decrypt the encrypted file with the encryptor's
            encryption key, return the output bytes of the
            clear text.
        """

        if not isinstance(encrypted_bytes, bytes):
            self.raise_error("Data being decrypted is not in bytes.")

        file_b64 = self.__secret_box.decrypt(encrypted_bytes, encoder=nacl.encoding.Base64Encoder)

        return base64.b64decode(file_b64)

    def derive_32_byte_key(self, source_key):
        """ Given any str or bytes, derive a 32-byte key by
            first hashing with SHA256 and then take first half
            of hash string. This is deterministic.
        """

        # Accept both strings and bytes
        if isinstance(source_key, str):
            source_key = str.encode(source_key)

        if not isinstance(source_key, bytes):
            self.raise_error("Input key is not in bytes or string.")

        hashed_key = nacl.hash.sha256(source_key, encoder=nacl.encoding.HexEncoder)
        derived_key = hashed_key[:nacl.secret.SecretBox.KEY_SIZE]

        return derived_key


    @classmethod
    def raise_error(self, error_message):
        """ Utilities function for raising and logging error messages. """

        caller_name = str(sys._getframe(1).f_code.co_name)
        message = strftime("%Y-%m-%d %H:%M:%S", gmtime()) + caller_name + ": " + str(error_message) + "\n"

        try:
            # If we cannot write to the directory or file, not making a fuss.
            log_file = open('crypt.log', 'w+')
            log_file.write(message)
        except:
            pass

        raise RuntimeError(message)
