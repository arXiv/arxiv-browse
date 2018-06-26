import mmh3


def create_hash(secret: str, url: str) -> str:
    # murmer is faster and more random that MD5 which was used in arXiv classic
    return mmh3.hash_bytes(secret + url).hex()


def is_hash_valid(secret: str, url: str, ct_hash: str) -> bool:
    return ct_hash == create_hash(secret, url)
