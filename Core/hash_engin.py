
import hashlib
import hmac
import os


# ==========================================
# 1. Supported Hash Algorithms
# ==========================================

SUPPORTED_ALGORITHMS = {
    "MD5": "md5",
    "SHA-1": "sha1",
    "SHA-224": "sha224",
    "SHA-256": "sha256",
    "SHA-384": "sha384",
    "SHA-512": "sha512",
    "SHA3-224": "sha3_224",
    "SHA3-256": "sha3_256",
    "SHA3-384": "sha3_384",
    "SHA3-512": "sha3_512",
    "BLAKE2B": "blake2b",
    "BLAKE2S": "blake2s"
}


# ==========================================
# 2. Normalize Algorithm Name
# ==========================================

def normalize_algorithm(algorithm: str) -> str:

    if not isinstance(algorithm, str):
        raise TypeError("Algorithm must be a string.")

    normalized = algorithm.strip().upper()

    if normalized not in SUPPORTED_ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    return SUPPORTED_ALGORITHMS[normalized]


# ==========================================
# 3. Get Supported Algorithms
# ==========================================

def get_supported_algorithms() -> list:

    return list(SUPPORTED_ALGORITHMS.keys())


# ==========================================
# 4. Generate Hash
# ==========================================

def hash_text(text: str, algorithm: str = "SHA-256") -> str:

    if not isinstance(text, str):
        raise TypeError("Input must be a string.")

    algo = normalize_algorithm(algorithm)

    encoded_text = text.encode("utf-8")

    hash_object = hashlib.new(algo, encoded_text)

    return hash_object.hexdigest()


# ==========================================
# 5. Hash File
# ==========================================

def hash_file(file_path: str, algorithm: str = "SHA-256") -> str:

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    algo = normalize_algorithm(algorithm)

    hash_object = hashlib.new(algo)

    with open(file_path, "rb") as file:

        for chunk in iter(lambda: file.read(4096), b""):
            hash_object.update(chunk)

    return hash_object.hexdigest()


# ==========================================
# 6. Compare Two Hashes
# ==========================================

def compare_hashes(hash1: str, hash2: str) -> bool:

    if not isinstance(hash1, str) or not isinstance(hash2, str):
        return False

    return hmac.compare_digest(
        hash1.lower(),
        hash2.lower()
    )


# ==========================================
# 7. Verify Password
# ==========================================

def verify_hash(
    password: str,
    target_hash: str,
    algorithm: str
) -> bool:

    generated_hash = hash_text(password, algorithm)

    return compare_hashes(generated_hash, target_hash)


# ==========================================
# 8. MySQL Double SHA-1
# ==========================================

def mysql_hash(password: str) -> str:

    if not isinstance(password, str):
        raise TypeError("Password must be a string.")

    first_hash = hashlib.sha1(
        password.encode("utf-8")
    ).digest()

    second_hash = hashlib.sha1(first_hash).hexdigest()

    return "*" + second_hash.upper()


# ==========================================
# 9. Get Hash Information
# ==========================================

def get_hash_info(algorithm: str) -> dict:

    algo = normalize_algorithm(algorithm)

    hash_object = hashlib.new(algo)

    return {
        "algorithm": algorithm.upper(),
        "internal_name": algo,
        "digest_size_bytes": hash_object.digest_size,
        "digest_size_bits": hash_object.digest_size * 8,
        "hex_digest_length": hash_object.digest_size * 2,
        "block_size": hash_object.block_size
    }


# ==========================================
# 10. Get Digest Length
# ==========================================

def get_digest_length(algorithm: str) -> int:

    algo = normalize_algorithm(algorithm)

    return hashlib.new(algo).digest_size * 2


# ==========================================
# 11. Test Hash Engine
# ==========================================

if __name__ == "__main__":

    password = "123456"

    print("========== HASH ENGINE TEST ==========")

    print("\nSupported Algorithms:")

    for algorithm in get_supported_algorithms():
        print(algorithm)

    print("\nGenerated Hashes:")

    for algorithm in get_supported_algorithms():

        result = hash_text(password, algorithm)

        print(f"{algorithm}: {result}")

    print("\nVerification:")

    target = hash_text(password, "MD5")

    print(verify_hash(password, target, "MD5"))

    print("\nComparison:")

    print(compare_hashes(target, target))

    print("\nHash Information:")

    print(get_hash_info("SHA-256"))

    print("\nMySQL Hash:")

    print(mysql_hash(password))

    print("\n========== TEST COMPLETED ==========")
