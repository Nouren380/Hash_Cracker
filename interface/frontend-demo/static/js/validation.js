const HashValidation = {
  validate(rawHash) {
    const value = (rawHash || "").trim();
    if (!value) return { valid: false, message: "Enter a hash value." };
    if (!/^[a-f0-9]+$/i.test(value)) return { valid: false, message: "Use only hexadecimal characters (0-9, a-f), with no spaces." };
    return { valid: true, message: "", normalized: value };
  }
};
