"""Script to make some fake data to test with"""

from pathlib import Path

from cloudpathlib.anypath import to_anypath

testdata=[
    ('/ps_cache/acc-phys/pdf/9502/9502001v1.pdf', 'early id'),

    ('/ftp/arxiv/papers/1809/1809.00949.pdf', 'pdf only, single version aka 1809.00949v1.pdf'),

    ('/ftp/arxiv/papers/1208/1208.6335.pdf','pdf only, two versions, current version aka 1208.6335v2.pdf'),
    ('/orig/arxiv/papers/1208/1208.6335v1.pdf','pdf only, two versions, old version'),

    ('/ftp/cs/papers/0212/0212040.pdf', 'old id, single version, aka cs/0212040v1.pdf'),

    ('/ftp/arxiv/papers/2101/2101.04792.pdf', '4 versions, current version aka 2101.04792v4.pdf'),
    ('/orig/arxiv/papers/2101/2101.04792v3.pdf', '4 versions'),
    ('/orig/arxiv/papers/2101/2101.04792v2.pdf', '4 versions'),
    ('/orig/arxiv/papers/2101/2101.04792v1.pdf', '4 versions'),

    ('/orig/cs/papers/0012/0012007v1.pdf', 'early id, 3 versions, first 2 are pdf, 3rd is tex'),
    ('/orig/cs/papers/0012/0012007v2.pdf', 'early id, 3 versions, first 2 are pdf, 3rd is tex'),
    ('/ps_cache/cs/pdf/0012/0012007v3.pdf', 'early id, 3 versions, first 2 are pdf, 3rd is tex'),

    ('/ps_cache/cs/pdf/0011/0011004v1.pdf', 'early id, 2 versions, tex'),
    ('/ps_cache/cs/pdf/0011/0011004v2.pdf', 'early id, 2 versions, tex'),
]

for pathstr, desc in testdata:
    if not to_anypath(f"gs://arxiv-production-data{pathstr}").exists():
        print(f"pathstr {pathstr} does not exist at GCP! Double check and try again.")
        continue

    datapth = Path('./data' + pathstr)
    parent = datapth.parent
    parent.mkdir(parents=True, exist_ok=True)

    datapth.write_text(f"contents {datapth.name}\n{desc}")
    print(f"Wrote {pathstr}")
