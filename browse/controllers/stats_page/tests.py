"""Tests for stats page controllers, :mod:`browse.controllers.stats_page`."""

from unittest import TestCase, mock
from datetime import datetime
from werkzeug import MultiDict
from werkzeug.exceptions import BadRequest

from arxiv import status
from browse.services.database.models import stats_hourly
from browse.controllers import stats_page


class TestStatsPageControllers(TestCase):
    """Tests for :mod:`browse.controllers.stats_page` controllers."""

    @mock.patch('browse.controllers.stats_page.get_hourly_stats_count')
    def test_get_hourly_stats_page(self, mock_get_hourly_stats_count) -> None:
        """Tests for :func:`.get_hourly_stats_page`."""
        with self.assertRaises(BadRequest):
            stats_page.get_hourly_stats_page(requested_date_str='foo')

        with self.assertRaises(BadRequest):
            stats_page.get_hourly_stats_page(requested_date_str='201901')

        mock_get_hourly_stats_count.return_value = (0, 0)
        for date_str in ['2019', '2019-01-01', '20180202', None]:
            response_data, code, _ = stats_page.get_hourly_stats_page(
                requested_date_str=date_str)
            self.assertEqual(code, status.HTTP_200_OK,
                             'Response should be OK.')


    @mock.patch('browse.controllers.stats_page.get_hourly_stats')
    def test_get_hourly_stats_csv(self, mock_get_hourly_stats) -> None:
        """Tests for :func:`.get_hourly_stats_csv`."""
        with self.assertRaises(BadRequest):
            stats_page.get_hourly_stats_csv(requested_date_str='bar')

        with self.assertRaises(BadRequest):
            stats_page.get_hourly_stats_csv(requested_date_str='2017-021')

        mock_get_hourly_stats.return_value = list()
        response_data, code, headers = stats_page.get_hourly_stats_csv()
        self.assertEqual(code, status.HTTP_200_OK, 'Response should be OK.')
        self.assertEqual(headers['Content-Type'], 'text/csv')
        self.assertIn('csv', response_data, 'csv is in response data')
        self.assertEqual(response_data['csv'], "hour,node1,node2,node3,node4\n")

        # mock_get_hourly_stats.return_value = [
        #     mock(ymd=datetime(2019, 3, 19), hour=0, node_num=1)
        # ]
