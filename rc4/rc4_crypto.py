"""
RC4 and RC4+ Cryptographic Algorithms
Contains KSA and PRGA implementations for both variants
"""


class RC4Engine:
    """Base class for RC4 cipher engine"""

    def __init__(self, N=256):
        """Initialize RC4 engine with state size N"""
        self.N = N
        self.S = []
        self.i = 0
        self.j = 0

    def ksa(self, key):
        """
        Key Scheduling Algorithm
        Initialize and mix the state using the provided key

        Args:
            key: string key for initialization

        Returns:
            list of tuples: (i, j, operation_description) for visualization
        """
        # Initialize S
        self.S = list(range(self.N))
        self.i = 0
        self.j = 0

        # Convert key to bytes
        key_bytes = [ord(c) for c in key]
        key_length = len(key_bytes)

        steps = []

        # KSA mixing
        j = 0
        for i in range(self.N):
            j = (j + self.S[i] + key_bytes[i % key_length]) % self.N
            self.S[i], self.S[j] = self.S[j], self.S[i]

            # Record step for visualization (sample steps to avoid too much data)
            if i < 10 or i % (self.N // 10) == 0:
                steps.append((i, j, f"swap S[{i}]↔S[{j}]"))

        # Reset for PRGA
        self.i = 0
        self.j = 0

        return steps

    def reset_prga(self):
        """Reset PRGA indices"""
        self.i = 0
        self.j = 0


class RC4Classic(RC4Engine):
    """Classic RC4 PRGA implementation"""

    def prga_step(self):
        """
        Generate one keystream byte using classic RC4 PRGA

        Returns:
            dict with keys: output_byte, i, j, t, details (for logging)
        """
        self.i = (self.i + 1) % self.N
        self.j = (self.j + self.S[self.i]) % self.N

        # Swap
        self.S[self.i], self.S[self.j] = self.S[self.j], self.S[self.i]

        # Output byte
        t = (self.S[self.i] + self.S[self.j]) % self.N
        output_byte = self.S[t]

        return {
            "output_byte": output_byte,
            "i": self.i,
            "j": self.j,
            "t": t,
            "details": {
                "algorithm": "RC4",
                "swap": f"S[{self.i}] ↔ S[{self.j}]",
            },
        }


class RC4Plus(RC4Engine):
    """RC4+ PRGA implementation (Polak & Boryczka 2019)"""

    def __init__(self):
        """RC4+ requires N=256"""
        super().__init__(N=256)

    def prga_step(self):
        """
        Generate one keystream byte using RC4+ PRGA (Algorithm 1)

        Returns:
            dict with keys: output_byte, i, j, t, t_prime, t_double,
                          idx1, idx2, details (for logging)
        """
        # Ensure we're working in 8-bit space
        self.i = (self.i + 1) & 0xFF
        self.j = (self.j + self.S[self.i]) & 0xFF

        # Swap
        self.S[self.i], self.S[self.j] = self.S[self.j], self.S[self.i]

        # Calculate t
        t = (self.S[self.i] + self.S[self.j]) & 0xFF

        # Calculate idx1 and idx2 for t_prime
        idx1 = ((self.i >> 3) ^ ((self.j << 5) & 0xFF)) & 0xFF
        idx2 = (((self.i << 5) & 0xFF) ^ (self.j >> 3)) & 0xFF

        # Calculate t_prime
        t_prime = ((self.S[idx1] + self.S[idx2]) & 0xFF) ^ 0xAA
        t_prime &= 0xFF

        # Calculate t_double
        t_double = (self.j + self.S[self.j]) & 0xFF

        # Calculate output byte
        output_byte = (((self.S[t] + self.S[t_prime]) & 0xFF) ^ self.S[t_double]) & 0xFF

        return {
            "output_byte": output_byte,
            "i": self.i,
            "j": self.j,
            "t": t,
            "t_prime": t_prime,
            "t_double": t_double,
            "idx1": idx1,
            "idx2": idx2,
            "details": {
                "algorithm": "RC4+",
                "swap": f"S[{self.i}] ↔ S[{self.j}]",
            },
        }


def encrypt_decrypt(plaintext_bytes, keystream):
    """
    XOR plaintext/ciphertext with keystream

    Args:
        plaintext_bytes: bytes to encrypt/decrypt
        keystream: list of keystream bytes

    Returns:
        list of result bytes
    """
    return [p ^ k for p, k in zip(plaintext_bytes, keystream)]


def generate_keystream(engine, length):
    """
    Generate keystream of specified length

    Args:
        engine: RC4Engine instance (RC4Classic or RC4Plus)
        length: number of bytes to generate

    Returns:
        tuple: (keystream list, steps list with details for each byte)
    """
    keystream = []
    steps = []

    for _ in range(length):
        result = engine.prga_step()
        keystream.append(result["output_byte"])
        steps.append(result)

    return keystream, steps
