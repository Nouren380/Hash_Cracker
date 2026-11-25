import hashlib
try:
    from .hash_identifier import identify_hash
except ImportError:
    from hash_identifier import identify_hash
from pathlib import Path

def dictionary_attack(target_hash: str, wordlist_path: str = str(Path(__file__).with_name("password_list.txt"))) -> str | None:
    """
    Implements the dictionary attack flow:
    1. Validate & Analyze Hash
    2. Check Algorithm Support
    3. Load Dictionary Wordlist
    4. Iterate, Hash, and Compare
    """
    
    # الخطوة الأولى والثانية: Validate input & Analyze Hash
    analysis = identify_hash(target_hash)
    
    if not analysis.get("is_valid_format"):
        print(f"[-] Display Error Message: Invalid Hash Input ({analysis.get('message')})")
        return None

    print(f"[+] Hash Format Identified: {analysis.get('format')}")
    
    # الخطوة الثالثة: Check if Algorithm is Supported
    candidates = analysis.get("possible_algorithms", [])
    if not candidates:
        print("[-] Unsupported Algorithm / Algorithm Not Supported")
        return None

    print(f"[+] Supported Algorithms Found: {candidates}")

    # الخطوة الرابعة: Load Dictionary Wordlist
    try:
        with open(wordlist_path, "r", encoding="utf-8") as file:
            passwords = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"[-] Display Error Message: Wordlist Not Found ('{wordlist_path}')")
        return None

    print(f"[+] Wordlist Available. Loaded {len(passwords)} candidate passwords. Starting attack...\n")

    # الخطوة الخامسة: Read Next Candidate Password & Generate / Compare Hash
    for pwd in passwords:
        for algo in candidates:
            algo_upper = algo.upper()
            hashed_guess = None

            try:
                if algo_upper == "MD5":
                    hashed_guess = hashlib.md5(pwd.encode("utf-8")).hexdigest()
                elif algo_upper == "SHA-1":
                    hashed_guess = hashlib.sha1(pwd.encode("utf-8")).hexdigest()
                elif algo_upper == "SHA-256":
                    hashed_guess = hashlib.sha256(pwd.encode("utf-8")).hexdigest()
                elif algo_upper == "SHA-512":
                    hashed_guess = hashlib.sha512(pwd.encode("utf-8")).hexdigest()
                # تقدري تزودي أي خوارزميات تانية هنا حسب الاحتياج
            except Exception:
                continue

            # مقارنة الـ Hash المتولد مع الـ Target Hash
            if hashed_guess and hashed_guess.lower() == str(target_hash).lower():
                print(f"[SUCCESS] Password Found! ➔ [{pwd}] (Matched using {algo})")
                return pwd

    # لو القوس خلص ومافيش أي ماتش حصل
    print("[-] Password Not Found (Wordlist Exhausted)")
    return None


if __name__ == "__main__":
    # تجربة عملية مطابقة للفلوشارت
    sample_target = "e10adc3949ba59abbe56e057f20f883e" # الـ MD5 بتاع كلمة 123456
    print(f"Target Hash: {sample_target}")
    dictionary_attack(sample_target, wordlist_path=str(Path(__file__).with_name("password_list.txt")))