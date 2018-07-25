"""Tests for Google Scholar metadata tag creation. """

import html
import json
import os
import pprint
from unittest import TestCase
from tests import path_of_for_test

from browse.domain.metadata import DocMetadata
from browse.services.util.metatags import meta_tag_metadata
from browse.services.document.metadata import AbsMetaSession
from app import app

CLASSIC_RESULTS_FILE = path_of_for_test('data/classic_scholar_metadata_tags.json')
ABS_FILES = path_of_for_test('data/abs_files')


class TestAgainstClassicResults(TestCase):
    """Test google scholar metadata created from abs files against classic exresults. """

    def setUp(self):
            app.testing = True
            app.config['APPLICATION_ROOT'] = ''
            app.config['SERVER_NAME'] = 'dev.arxiv.org'
            self.app = app

    def test_same_as_classic(self):

        bad_data = ['1501.00001v1', '1501.99999v1', '1501.00002v1', '1502.00001v1',  # probably fake abs
                    '0704.0019v2',  # title tex escaping problem
                    '0704.0559v1',  # bad double escape in classic
                    ]

        # '0704.0006v1', '0704.0481v1', '0704.0156v2' , '0704.0019v2', '0704.0597v1']

        with open(CLASSIC_RESULTS_FILE) as fp:
            classic_results = json.load(fp)

        def to_str(gs_tag):
            return str(gs_tag['name']) + ' ' + str(gs_tag['content'])

        def to_set(gs_tags):
            return set(map(to_str, gs_tags))

        num_files_tested = 0
        for dir_name, subdir_list, file_list in os.walk(ABS_FILES):
            for fname in file_list:
                fname_path = os.path.join(dir_name, fname)
                # skip any empty files
                if os.stat(fname_path).st_size == 0:
                    continue
                if not fname_path.endswith('.abs'):
                    continue
                mm = AbsMetaSession.parse_abs_file(filename=fname_path)
                if mm.arxiv_id_v in bad_data:
                    continue
                num_files_tested = num_files_tested + 1

                self.assertIsInstance(mm, DocMetadata)

                with self.app.test_request_context():
                    gs_tags = meta_tag_metadata(mm)

                self.assertIsInstance(gs_tags, list)
                if mm.arxiv_id_v not in classic_results:
                    # Could not find google scholar tags in classic results for this
                    # arxiv_id. Not a problem. Probably this abs was added to the
                    # test data after the classic results were generated.
                    # You only should add the google scholar tags to the classic
                    # metadata if you'd like a regression test for it.
                    continue

                classic = set(map(html.unescape, to_set(
                    classic_results[mm.arxiv_id_v])))
                ng = set(map(html.unescape, to_set(gs_tags)))

                if ng != classic:
                    classic_without_doi = set(
                        filter(lambda v: not v.startswith('citation_doi'), classic))
                    ng_without_doi = set(
                        filter(lambda v: not v.startswith('citation_doi'), ng))
                    self.assertSetEqual(ng_without_doi, classic_without_doi,
                                        '''
                                        
For {} NG tags (first result) not same as Classic tags(second results)
Test Num {} 
DOI are ignored.
                                        
classic/expected: {}
                                        
                                                                              
ng/actual: {}

test authors: {}
test title: {}'''.format(mm.arxiv_id_v, num_files_tested, pprint.pformat(classic), pprint.pformat(ng), mm.authors.raw,
                                            mm.title))
