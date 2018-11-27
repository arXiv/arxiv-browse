
from typing import Any, Dict
from unittest import TestCase

from arxivabs.browse.domain.metadata import DocMetadata


class DocMetadataTest(TestCase):
    fields: Dict[str, Any]

    def __init__(self, *args: str, **kwargs: Dict) -> None:
        """Set up some common variables."""
        super().__init__(*args, **kwargs)
        self.fields = {
            # TODO: reasonable mock defaults for future tests
        }

    def test_something(self):
        """Tests that omission of a required field generates an exception."""
        fields = self.fields.copy()
        # TODO: implement a test on a generated DocMetadata

    def test_required_fields(self):
        """Tests that omission of a required field generates an exception."""
        fields = self.fields.copy()

        def run_on_empty_args() -> DocMetadata:
            return DocMetadata(**fields)  # type: ignore

        with self.assertRaises(TypeError) as ctx:
            run_on_empty_args()

        # Do not indent us or we will not run and be tested!:
        self.assertTrue('missing 14 required positional arguments' in str(ctx.exception))
        #
        self.assertTrue('raw_safe' in str(ctx.exception))
        self.assertTrue('arxiv_id' in str(ctx.exception))
        self.assertTrue('arxiv_id_v' in str(ctx.exception))
        self.assertTrue('arxiv_identifier' in str(ctx.exception))
        self.assertTrue('modified' in str(ctx.exception))
        self.assertTrue('title' in str(ctx.exception))
        self.assertTrue('abstract' in str(ctx.exception))
        self.assertTrue('authors' in str(ctx.exception))
        self.assertTrue('submitter' in str(ctx.exception))
        self.assertTrue('categories' in str(ctx.exception))
        self.assertTrue('primary_category' in str(ctx.exception))
        self.assertTrue('primary_archive' in str(ctx.exception))
        self.assertTrue('primary_group' in str(ctx.exception))
        self.assertTrue('secondary_categories' in str(ctx.exception))
        #
        self.assertTrue('journal_ref' not in str(ctx.exception))
        self.assertTrue('report_num' not in str(ctx.exception))
        self.assertTrue('doi' not in str(ctx.exception))
        self.assertTrue('acm_class' not in str(ctx.exception))
        self.assertTrue('msc_class' not in str(ctx.exception))
        self.assertTrue('proxy' not in str(ctx.exception))
        self.assertTrue('comments' not in str(ctx.exception))
        self.assertTrue('version' not in str(ctx.exception))
        self.assertTrue('license' not in str(ctx.exception))
        self.assertTrue('version_history' not in str(ctx.exception))
        self.assertTrue('private' not in str(ctx.exception))
