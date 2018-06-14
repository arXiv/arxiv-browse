from typing import List, Optional


def grep_f_count(filename: str, query: str) -> Optional[int]:
    """Like counting lines from grep -F "query" filename"""
    try:
        search_file: List[str] = [line.strip() for line in open(filename)]
        return sum(map(lambda ln: 1 if query in ln else 0, search_file))
    except IOError:
        return None


