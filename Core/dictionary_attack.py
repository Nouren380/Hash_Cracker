"""
Hash Cracker - Dictionary Attack Engine
Module: Core/dictionary_attack.py
Authors: Roba, Nouren, Rashad Sameh

Implements dictionary-based cryptographic hash cracking integrated with
hash identification and persistent SQLite database session tracking.
"""

import hashlib
import os
import sys
import time
from typing import Optional

# Ensure project root is in sys.path for robust imports across all invocation styles
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Import hash identification
try:
    from Core.hash_identifier import identify_hash
except ImportError:
    from hash_identifier import identify_hash

# Import database manager
from Database.db_manager import DBManager

# Default password dictionary path
DEFAULT_WORDLIST_PATH = os.path.join(os.path.dirname(__file__), "password_list.txt")


def dictionary_attack(
    target_hash: str,
    wordlist_path: Optional[str] = None,
    db: Optional[DBManager] = None
) -> Optional[str]:
    """
    Executes a dictionary attack against a target hash:
    1. Validates and analyzes hash input format.
    2. Identifies and verifies algorithm support against DB registry.
    3. Loads dictionary wordlist and registers metadata.
    4. Iterates through candidates, generates digests, compares,
       and logs attempts in high-throughput batches to SQLite.
    5. Updates session status (found, not_found, or error) with duration and metrics.

    Args:
        target_hash: The cryptographic hash to be cracked.
        wordlist_path: Optional path to a dictionary file (defaults to Core/password_list.txt).
        db: Optional existing DBManager instance (instantiates new one if None).

    Returns:
        The recovered plaintext password string if found, otherwise None.
    """
    close_db_when_done = False
    if db is None:
        db = DBManager()
        close_db_when_done = True

    start_time = time.time()
    session_id = db.create_session(str(target_hash).strip() if target_hash else "")

    try:
        # ---------------------------------------------------------------------
        # Step 1: Input Validation & Hash Analysis
        # ---------------------------------------------------------------------
        analysis = identify_hash(target_hash)

        if not analysis.get("is_valid_format"):
            db.mark_invalid_hash(session_id)
            print(f"[-] Display Error Message: Invalid Hash Input ({analysis.get('message')})")
            return None

        print(f"[+] Hash Format Identified: {analysis.get('format')} (Length: {analysis.get('length')} chars)")

        # ---------------------------------------------------------------------
        # Step 2: Check Algorithm Support in Database
        # ---------------------------------------------------------------------
        candidates = analysis.get("possible_algorithms", [])
        if not candidates:
            db.mark_unsupported_algorithm(session_id)
            print("[-] Display Error Message: Unsupported Algorithm / Algorithm Not Supported")
            return None

        # Resolve algorithm ID from DB registry
        algo_record = None
        for candidate_name in candidates:
            algo_record = db.get_algorithm_by_name(candidate_name)
            if algo_record:
                break

        if not algo_record:
            algo_record = db.get_algorithm_by_length(analysis.get("length", 0))

        if not algo_record:
            db.mark_unsupported_algorithm(session_id)
            print("[-] Display Error Message: Unsupported Algorithm / Algorithm Not Supported")
            return None

        algo_id = algo_record["id"]
        algo_name = algo_record["name"]
        db.set_algorithm(session_id, detected_algorithm_id=algo_id, selected_algorithm_id=algo_id)
        print(f"[+] Supported Algorithm Selected: {algo_name} (ID: {algo_id})")

        # Determine active algorithms to test (prioritize selected supported algorithm)
        supported_candidates = [
            c for c in candidates if db.get_algorithm_by_name(c) is not None
        ]
        if not supported_candidates:
            supported_candidates = [algo_name]

        # ---------------------------------------------------------------------
        # Step 3: Load Wordlist
        # ---------------------------------------------------------------------
        effective_wordlist_path = wordlist_path if wordlist_path else DEFAULT_WORDLIST_PATH

        if not os.path.isfile(effective_wordlist_path):
            db.mark_wordlist_not_found(session_id)
            print(f"[-] Display Error Message: Wordlist Not Found ('{effective_wordlist_path}')")
            return None

        try:
            with open(effective_wordlist_path, "r", encoding="utf-8", errors="ignore") as file:
                passwords = [line.strip() for line in file if line.strip()]
        except Exception as read_err:
            db.mark_wordlist_not_found(session_id)
            print(f"[-] Display Error Message: Wordlist Not Found / Cannot read ('{effective_wordlist_path}'): {read_err}")
            return None

        wordlist_id = db.add_wordlist(
            name=os.path.basename(effective_wordlist_path),
            file_path=os.path.abspath(effective_wordlist_path),
            word_count=len(passwords)
        )
        db.start_running(session_id, wordlist_id=wordlist_id)
        print(f"[+] Wordlist Available. Loaded {len(passwords)} candidate passwords. Starting attack...\n")

        # ---------------------------------------------------------------------
        # Step 4: Iterate, Hash, Compare & Batch Log
        # ---------------------------------------------------------------------
        clean_target = str(target_hash).strip().lower()
        attempt_order = 0
        batch_attempts = []
        batch_size = 200

        for pwd in passwords:
            for algo in supported_candidates:
                attempt_order += 1
                algo_upper = algo.upper()
                hashed_guess = None

                try:
                    if algo_upper == "MD5":
                        hashed_guess = hashlib.md5(pwd.encode("utf-8")).hexdigest()
                    elif algo_upper == "SHA-1":
                        hashed_guess = hashlib.sha1(pwd.encode("utf-8")).hexdigest()
                    elif algo_upper == "SHA-224":
                        hashed_guess = hashlib.sha224(pwd.encode("utf-8")).hexdigest()
                    elif algo_upper == "SHA-256":
                        hashed_guess = hashlib.sha256(pwd.encode("utf-8")).hexdigest()
                    elif algo_upper == "SHA-384":
                        hashed_guess = hashlib.sha384(pwd.encode("utf-8")).hexdigest()
                    elif algo_upper == "SHA-512":
                        hashed_guess = hashlib.sha512(pwd.encode("utf-8")).hexdigest()
                    elif algo_upper in ("SHA3-224", "SHA3-256", "SHA3-384", "SHA3-512"):
                        internal = algo_upper.lower().replace("-", "_")
                        hashed_guess = hashlib.new(internal, pwd.encode("utf-8")).hexdigest()
                except Exception:
                    continue

                if not hashed_guess:
                    continue

                is_match = (hashed_guess.lower() == clean_target)
                batch_attempts.append((pwd, hashed_guess, is_match, attempt_order))

                # Periodic batch insert to SQLite to maximize throughput
                if len(batch_attempts) >= batch_size:
                    db.log_attempts_batch(session_id, batch_attempts)
                    batch_attempts.clear()

                # If match found
                if is_match:
                    duration_ms = round((time.time() - start_time) * 1000.0, 2)
                    if batch_attempts:
                        db.log_attempts_batch(session_id, batch_attempts)
                        batch_attempts.clear()

                    db.mark_found(
                        session_id=session_id,
                        password=pwd,
                        attempts_count=attempt_order,
                        duration_ms=duration_ms
                    )
                    print(f"[SUCCESS] Password Found! ➔ [{pwd}] (Matched using {algo} in {duration_ms}ms, attempt #{attempt_order})")
                    return pwd

        # ---------------------------------------------------------------------
        # Step 5: Wordlist Exhausted (Not Found)
        # ---------------------------------------------------------------------
        duration_ms = round((time.time() - start_time) * 1000.0, 2)
        if batch_attempts:
            db.log_attempts_batch(session_id, batch_attempts)
            batch_attempts.clear()

        db.mark_not_found(
            session_id=session_id,
            attempts_count=attempt_order,
            duration_ms=duration_ms
        )
        print(f"[-] Password Not Found (Wordlist Exhausted after {attempt_order} attempts, {duration_ms}ms)")
        return None

    finally:
        if close_db_when_done:
            db.close()


if __name__ == "__main__":
    print("========== DICTIONARY ATTACK INTEGRATION TEST ==========")
    sample_target = "e10adc3949ba59abbe56e057f20f883e"  # MD5 of "123456"
    print(f"Target Hash: {sample_target}")
    result = dictionary_attack(sample_target)
    print(f"Result: {result}")
