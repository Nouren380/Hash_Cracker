const HashValidation = {
  validate(rawHash, algorithmId) {
    const value = rawHash || "";

    if (value.length === 0) {
      return { valid: false, message: "Enter a hash value." };
    }

    if (value.trim().length === 0) {
      return { valid: false, message: "The hash cannot be whitespace only." };
    }

    const trimmed = value.trim();

    if (/\s/.test(trimmed)) {
      return { valid: false, message: "The hash cannot contain spaces." };
    }

    const algorithm = AlgorithmConfig.byId(algorithmId);

    if (!algorithm) {
      return { valid: false, message: "Select a hash algorithm." };
    }

    if (algorithm.pattern && !algorithm.pattern.test(trimmed)) {
      return {
        valid: false,
        message: `This does not look like a valid ${algorithm.label} hash (expected ${algorithm.hexLength} hex characters).`
      };
    }

    return { valid: true, message: "", normalized: trimmed };
  }
};
