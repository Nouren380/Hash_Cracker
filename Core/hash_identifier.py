import base64
import binascii
import re
from typing import Any


# Common hash algorithms grouped by digest length (hex characters)
HEX_HASH_CANDIDATES = {
    32: ["MD5", "NTLM", "LM"],
    40: ["SHA-1", "RIPEMD-160", "Tiger-160"],
    56: ["SHA-224", "SHA3-224"],
    64: ["SHA-256", "SHA3-256", "BLAKE2s-256"],
    96: ["SHA-384", "SHA3-384"],
    128: ["SHA-512", "SHA3-512", "BLAKE2b-512"]
}


def _result(
    value: str,
    is_valid: bool,
    format_name: str,
    algorithm: str = None,
    candidates: list = None,
    confidence: str = "unknown",
    encoding: str = "unknown",
    digest_size_bytes: int = None,
    details: dict = None,
    message: str = ""
) -> dict:

    return {
        "hash": value,
        "is_valid_format": is_valid,
        "format": format_name,
        "algorithm": algorithm,
        "possible_algorithms": candidates or (
            [algorithm] if algorithm else []
        ),
        "identification_confidence": confidence,
        "length": len(value),
        "length_characters": len(value),
        "input_size_bytes": len(value.encode("utf-8")),
        "encoding": encoding,
        "digest_size_bytes": digest_size_bytes,
        "details": details or {},
        "message": message
    }


def decode_base64(payload: str):
    """Decode Base64 payload."""

    try:
        padded = payload + "=" * (-len(payload) % 4)
        return base64.b64decode(padded, validate=True)

    except (ValueError, binascii.Error):
        return None


def identify_hash(value: str) -> dict:
    """
    Identify a hash and extract its metadata.

    Returns:
        Dictionary containing hash information.
    """

    if not isinstance(value, str):
        value = str(value)

    value = value.strip()

    # 1. Empty input
    if not value:
        return _result(
            value,
            False,
            "Empty",
            confidence="none",
            message="Please enter a hash."
        )

    # 2. Invalid spaces
    if any(char.isspace() for char in value):
        return _result(
            value,
            False,
            "Invalid",
            confidence="none",
            message="Hash cannot contain spaces."
        )

    # 3. Argon2
    argon = re.fullmatch(
        r"\$(argon2id|argon2i|argon2d)"
        r"\$v=(\d+)\$m=(\d+),t=(\d+),p=(\d+)"
        r"\$([A-Za-z0-9+/]+)\$([A-Za-z0-9+/]+)",
        value
    )

    if argon:
        variant, version, memory, time, parallel, salt, digest = argon.groups()

        return _result(
            value,
            True,
            "Argon2 PHC",
            variant.upper(),
            confidence="high",
            encoding="PHC",
            details={
                "version": int(version),
                "memory_cost_kib": int(memory),
                "time_cost": int(time),
                "parallelism": int(parallel),
                "salt_length": len(salt),
                "digest_length": len(digest)
            },
            message="Argon2 format identified."
        )

    # 4. bcrypt
    bcrypt = re.fullmatch(
        r"\$(2a|2b|2y)\$(\d{2})\$([./A-Za-z0-9]{53})",
        value
    )

    if bcrypt:
        version, cost, payload = bcrypt.groups()

        return _result(
            value,
            True,
            "bcrypt",
            "bcrypt",
            confidence="high",
            encoding="Modular Crypt Format",
            details={
                "version": version,
                "cost_factor": int(cost),
                "payload_length": len(payload)
            },
            message="bcrypt format identified."
        )

    # 5. scrypt
    scrypt = re.fullmatch(
        r"\$scrypt\$ln=(\d+),r=(\d+),p=(\d+)"
        r"\$([A-Za-z0-9./]+)\$([A-Za-z0-9./]+)",
        value
    )

    if scrypt:
        log_n, r, p, salt, digest = scrypt.groups()

        return _result(
            value,
            True,
            "scrypt PHC",
            "scrypt",
            confidence="high",
            encoding="PHC",
            details={
                "cost_parameter_ln": int(log_n),
                "block_size": int(r),
                "parallelization": int(p),
                "salt_length": len(salt),
                "digest_length": len(digest)
            },
            message="scrypt format identified."
        )

    # 6. PBKDF2 Django
    pbkdf2 = re.fullmatch(
        r"pbkdf2_(sha1|sha256|sha384|sha512)"
        r"\$(\d+)\$([^$]+)\$([^$]+)",
        value,
        re.IGNORECASE
    )

    if pbkdf2:
        digest, iterations, salt, checksum = pbkdf2.groups()

        return _result(
            value,
            True,
            "Django PBKDF2",
            f"PBKDF2-HMAC-{digest.upper()}",
            confidence="high",
            encoding="Django format",
            details={
                "iterations": int(iterations),
                "salt_length": len(salt),
                "derived_key_length": len(checksum)
            },
            message="PBKDF2 format identified."
        )

    # 7. MySQL 4.1+
    if re.fullmatch(r"\*[0-9a-fA-F]{40}", value):

        return _result(
            value,
            True,
            "MySQL 4.1+",
            "MySQL SHA-1 (Double SHA-1)",
            confidence="high",
            encoding="Hexadecimal",
            digest_size_bytes=20,
            message="MySQL password hash identified."
        )

    # 8. LDAP hashes
    ldap_formats = {
        "{MD5}": ("MD5", 16),
        "{SHA}": ("SHA-1", 20),
        "{SSHA}": ("Salted SHA-1", 20),
        "{SSHA256}": ("Salted SHA-256", 32),
        "{SSHA384}": ("Salted SHA-384", 48),
        "{SSHA512}": ("Salted SHA-512", 64)
    }

    for prefix, (algorithm, size) in ldap_formats.items():

        if value.startswith(prefix):

            payload = decode_base64(value[len(prefix):])

            if payload is not None:

                return _result(
                    value,
                    True,
                    "LDAP Hash",
                    algorithm,
                    confidence="high",
                    encoding="Base64",
                    digest_size_bytes=size,
                    details={
                        "decoded_size_bytes": len(payload),
                        "salted": algorithm.startswith("Salted")
                    },
                    message="LDAP hash identified."
                )

    # 9. Unix MD5-crypt
    if re.fullmatch(
        r"\$1\$[./A-Za-z0-9]{1,8}\$[./A-Za-z0-9]{22}",
        value
    ):

        return _result(
            value, True, "Unix MD5-crypt",
            "MD5-crypt", confidence="high",
            encoding="Modular Crypt Format"
        )

    # 10. Unix SHA-256-crypt
    if re.fullmatch(
        r"\$5\$(?:rounds=\d+\$)?[./A-Za-z0-9]{1,16}\$[./A-Za-z0-9]{43}",
        value
    ):

        return _result(
            value, True, "Unix SHA-256-crypt",
            "SHA-256-crypt", confidence="high",
            encoding="Modular Crypt Format"
        )

    # 11. Unix SHA-512-crypt
    if re.fullmatch(
        r"\$6\$(?:rounds=\d+\$)?[./A-Za-z0-9]{1,16}\$[./A-Za-z0-9]{86}",
        value
    ):

        return _result(
            value, True, "Unix SHA-512-crypt",
            "SHA-512-crypt", confidence="high",
            encoding="Modular Crypt Format"
        )

    # 12. Raw hexadecimal hashes
    if re.fullmatch(r"[0-9a-fA-F]+", value):

        length = len(value)

        if length % 2 != 0:
            return _result(
                value,
                False,
                "Invalid Hexadecimal",
                confidence="none",
                encoding="Hexadecimal",
                message="Hexadecimal input must have an even length."
            )

        candidates = HEX_HASH_CANDIDATES.get(length)

        if candidates:

            return _result(
                value,
                True,
                "Raw Hexadecimal Digest",
                algorithm=None,
                candidates=candidates,
                confidence="low",
                encoding="Hexadecimal",
                digest_size_bytes=length // 2,
                details={
                    "hex_length": length,
                    "possible_algorithms": candidates
                },
                message=(
                    "Multiple algorithms may match this length. "
                    "Exact identification is not guaranteed."
                )
            )

        return _result(
            value,
            True,
            "Unknown Hexadecimal",
            confidence="low",
            encoding="Hexadecimal",
            digest_size_bytes=length // 2,
            message="Hexadecimal input, but no supported digest length matched."
        )

    # 13. Unknown hash
    return _result(
        value,
        False,
        "Unknown",
        confidence="none",
        message="Unsupported hash format."
    )


# Alternative function name
analyze_hash = identify_hash


# Testing
if __name__ == "__main__":

    test_hashes = [
        "5d41402abc4b2a76b9719d911017c592",
        "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    ]

    for hash_value in test_hashes:

        result = identify_hash(hash_value)

        print("\n========== HASH ANALYSIS ==========")

        for key, val in result.items():
            print(f"{key}: {val}")