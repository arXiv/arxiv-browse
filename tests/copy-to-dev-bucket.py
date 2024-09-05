
dev_bucket = "gs://arxiv-developmint/arxiv-sync-test-01"
src_bucket = "gs://arxiv-production/arxiv-production-data"

def make_copy_plan(src_bucket: str, dev_bucket: str) -> List[Tuple[str, str]]:
    """Make a list of copy operations to copy the contents of one bucket to another."""

    with open("data/used-arxiv-ids.txt", encoding="iso-8859-1") as fd:
        used_ids = fd.readlines()

    for id in used_ids:
        [yymm, five] = id.split(".")
        if int(yymm)