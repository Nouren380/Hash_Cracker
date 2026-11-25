const AlgorithmConfig = {
  confirmedByBackend: true,
  attackMethod: {
    id: "dictionary",
    label: "Dictionary Attack"
  },
  list: [
    {
      id: "md5",
      label: "MD5",
      hexLength: 32,
      pattern: /^[a-f0-9]{32}$/i,
      lengthSharedWith: []
    },
    {
      id: "sha1",
      label: "SHA-1",
      hexLength: 40,
      pattern: /^[a-f0-9]{40}$/i,
      lengthSharedWith: []
    },
    {
      id: "sha256",
      label: "SHA-256",
      hexLength: 64,
      pattern: /^[a-f0-9]{64}$/i,
      lengthSharedWith: ["sha3-256", "blake2s256"]
    },
    {
      id: "sha512",
      label: "SHA-512",
      hexLength: 128,
      pattern: /^[a-f0-9]{128}$/i,
      lengthSharedWith: ["sha3-512"]
    }
  ],

  byId(id) {
    return this.list.find((algorithm) => algorithm.id === id) || null;
  }
};
