"""Tests for Google Scholar metadata tag creation. """

import html
import json
import os
import pprint
from unittest import TestCase

# from datetime import datetime
# from dateutil.tz import tzutc
from browse.domain.metadata import DocMetadata
from browse.domain.metatags import meta_tag_metadata
from browse.services.document.metadata import AbsMetaSession

CLASSIC_RESULTS_FILE = 'tests/data/classic_scholar_metadata_tags.json'
ABS_FILES = 'tests/data/abs_files'


class TestAgainstClassicResults(TestCase):
    """Test google scholar metadata created from abs files against classic exresults. """

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
                num_files_tested += 1
                m = AbsMetaSession.parse_abs_file(filename=fname_path)
                if m.arxiv_id_v in bad_data:
                    continue
                num_files_tested = num_files_tested + 1

                self.assertIsInstance(m, DocMetadata)

                gs_tags = meta_tag_metadata(m)
                self.assertIsInstance(gs_tags, list)
                if m.arxiv_id_v not in classic_results:
                    print("could not find google scholar tags in classic results for '" + m.arxiv_id_v + "'")

                classic = set(map(html.unescape, to_set(classic_results[m.arxiv_id_v])))
                ng = set(map(html.unescape, to_set(gs_tags)))

                if ng != classic:
                    classic_without_doi = set(filter(lambda v: not v.startswith('citation_doi'), classic))
                    ng_without_doi = set(filter(lambda v: not v.startswith('citation_doi'), ng))
                    self.assertSetEqual(ng_without_doi, classic_without_doi,
                                        '''
                                        
For {} NG tags (first result) not same as Classic tags(second results)
Test Num {} 
DOI are ignored.
                                        
classic/expected: {}
                                        
                                                                              
ng/actual: {}

test authors: {}
test title: {}'''.format(m.arxiv_id_v, num_files_tested, pprint.pformat(classic), pprint.pformat(ng), m.authors,
                         m.title))
