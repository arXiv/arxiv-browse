"""For an arXiv id, gets from the production bucket all related files
such as abs, src and contents of the ps_cache.

Sanitizes them of email addresses, saves them in the test directoires.

"""

import os
import sys
import argparse
from pathlib import Path

from arxiv.identifier import Identifier

from google.cloud import storage

from arxiv_dissemination.services import key_patterns


def get_article_for_test(bucket, save_base_dir: str, arxiv_id: Identifier):
    """Gets from the production bucket all the files related to an arxiv_id,
    sanitizes them of email addresses, saves them in the test directoires"""
    abs_current = key_patterns.abs_path_current(arxiv_id)
    get_object_for_test(bucket, save_base_dir, abs_current)

    other_current = f"{key_patterns.abs_path_current_parent(arxiv_id)}/{arxiv_id.filename}"
    get_objs_matching_keyprefix(bucket, save_base_dir,other_current)

    abs_orig = f"{key_patterns.abs_path_orig_parent(arxiv_id)}/{arxiv_id.filename}"
    get_objs_matching_keyprefix(bucket, save_base_dir, abs_orig)

    ps_cache = f"{key_patterns._ps_cache_part('pdf',arxiv_id)}/{arxiv_id.filename}"
    get_objs_matching_keyprefix(bucket, save_base_dir, ps_cache)



def get_objs_matching_keyprefix(bucket, save_base_dir:str, key_prefix:str) -> int:
    print(f"Trying to get all objects in gs://{bucket.name}/{key_prefix}* to {save_base_dir}/")
    blobs =  list(bucket.client.list_blobs(bucket, prefix=key_prefix, max_results=100))
    count= sum([get_object_for_test(bucket, save_base_dir, blob.name)
                for blob in blobs])
    print(f"Items in gs://{bucket.name} is {len(blobs)} copied {count}")


def get_object_for_test(bucket, save_base_dir:str, key:str) -> int :
    print(f"trying to get gs://{bucket.name}/{key} to {save_base_dir}/{key}")
    blob = bucket.blob(key)
    if not blob.exists():
        raise Exception(f"Object {key} does not exist in bucket")

    base = Path(save_base_dir)
    target = base / key
    if target.exists():
        print(f"{key} exists locally, skipping")
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)
    blob.download_to_filename(target)
    print(f"Successfully got gs://{bucket.name}/{key} to {save_base_dir}/{key}")
    return 1

    



def sanitize_abs_file(abs_file:Path):
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=sys.modules[__name__].__doc__,)
    parser.add_argument('id', type=str, help="id of article to get")
    parser.add_argument('save_base_dir', type=Path)
    parser.add_argument('bucket', type=str)
    args = parser.parse_args()

    gs_client = storage.Client()
    bucket = gs_client.bucket(args.bucket)
    if not bucket.exists():
            raise Exception(f"GS bucket {bucket} does not exist.")



    get_article_for_test(bucket,
                         args.save_base_dir,
                         Identifier(args.id))
