"""Tests for stats page controllers, :mod:`browse.controllers.stats_page`."""
# mypy: ignore-errors
from datetime import date, datetime
from dateutil.tz import tzutc
from unittest import TestCase, mock
from http import HTTPStatus as status

from werkzeug.exceptions import BadRequest

from browse.controllers import stats_page


class TestStatsPageControllers(TestCase):
    """Tests for :mod:`browse.controllers.stats_page` controllers."""

    @mock.patch("browse.controllers.stats_page.get_hourly_stats_count")
    def test_get_hourly_stats_page(self, mock_get_hourly_stats_count) -> None:  # type: ignore
        """Tests for :func:`.get_hourly_stats_page`."""
        # test bad requested_date_str
        with self.assertRaises(BadRequest):
            stats_page.get_hourly_stats_page(tzutc, requested_date_str="foo")
        with self.assertRaises(BadRequest):
            stats_page.get_hourly_stats_page(tzutc, requested_date_str="201901")

        # test response for good or no date option
        mock_get_hourly_stats_count.return_value = (0, 0, 0)
        for date_str in ["2019", "2019-01-01", "20180202", None]:
            response_data, code, _ = stats_page.get_hourly_stats_page(
                tzutc,
                requested_date_str=date_str
            )
            mock_get_hourly_stats_count.assert_called_once()
            mock_get_hourly_stats_count.reset_mock()
            self.assertEqual(code, status.OK)
            for key in ["current_dt", "requested_dt", "normal_count", "admin_count"]:
                self.assertIn(key, response_data, f"{key} is in response_data")

    @mock.patch("browse.controllers.stats_page.get_hourly_stats")
    def test_get_hourly_stats_csv(self, mock_get_hourly_stats) -> None:  # type: ignore
        """Tests for :func:`.get_hourly_stats_csv`."""
        # test bad requested_date_str
        with self.assertRaises(BadRequest):
            stats_page.get_hourly_stats_csv(requested_date_str="bar")
        with self.assertRaises(BadRequest):
            stats_page.get_hourly_stats_csv(requested_date_str="2017-021")

        # test basic response when no date option is provided
        mock_get_hourly_stats.return_value = list()
        response_data, code, headers = stats_page.get_hourly_stats_csv()
        mock_get_hourly_stats.assert_called_once()
        mock_get_hourly_stats.reset_mock()
        self.assertEqual(code, status.OK)
        self.assertEqual(headers["Content-Type"], "text/csv")
        self.assertIn("csv", response_data, "csv is in response data")
        self.assertEqual(response_data["csv"], "hour,node1\n")

        # test response with mock data, when no date option is provided
        test_td = datetime(2019, 3, 19)
        mock_get_hourly_stats.return_value = [
            mock.Mock(
                ymd=test_td, hour=0, node_num=4, access_type="N", connections=4123
            ),
            mock.Mock(
                ymd=test_td, hour=0, node_num=3, access_type="N", connections=3124
            ),
            mock.Mock(
                ymd=test_td, hour=0, node_num=2, access_type="N", connections=2124
            ),
            mock.Mock(
                ymd=test_td, hour=0, node_num=1, access_type="N", connections=1234
            ),
        ]
        expected_response = (
            "hour,node1,node2,node3,node4\n"
            "2019-03-19T00:00:00Z,1234,2124,3124,4123\n"
        )

        # test response with mock data, when date option is provided
        response_data, code, headers = stats_page.get_hourly_stats_csv(
            requested_date_str="2019-03-19"
        )
        mock_get_hourly_stats.assert_called_once_with(stats_date=date(2019, 3, 19))
        self.assertEqual(code, status.OK)
        self.assertEqual(response_data["csv"], expected_response)

        mock_get_hourly_stats.return_value = [
            mock.Mock(
                ymd=test_td, hour=0, node_num=2, access_type="N", connections=2120
            ),
            mock.Mock(
                ymd=test_td, hour=0, node_num=4, access_type="N", connections=4120
            ),
            mock.Mock(
                ymd=test_td, hour=0, node_num=1, access_type="N", connections=1230
            ),
            mock.Mock(
                ymd=test_td, hour=0, node_num=3, access_type="N", connections=3120
            ),
            mock.Mock(
                ymd=test_td, hour=1, node_num=1, access_type="N", connections=1241
            ),
            mock.Mock(
                ymd=test_td, hour=1, node_num=4, access_type="N", connections=4121
            ),
            mock.Mock(
                ymd=test_td, hour=1, node_num=3, access_type="N", connections=3231
            ),
        ]
        expected_response = (
            "hour,node1,node2,node3,node4\n"
            "2019-03-19T00:00:00Z,1230,2120,3120,4120\n"
            "2019-03-19T01:00:00Z,1241,0,3231,4121\n"
        )

        response_data, code, headers = stats_page.get_hourly_stats_csv()
        self.assertEqual(code, status.OK)
        self.assertEqual(response_data["csv"], expected_response)

    @mock.patch("browse.controllers.stats_page.get_max_download_stats_dt")
    @mock.patch("browse.controllers.stats_page.get_monthly_download_count")
    def test_get_monthly_downloads_page(
        self,  # type: ignore
        mock_get_monthly_download_count,
        mock_get_max_download_stats_dt,
    ) -> None:
        """Tests for :func:`.get_monthly_downloads_page`."""
        # test basic response
        mock_get_monthly_download_count.return_value = 1
        mock_get_max_download_stats_dt.return_value = datetime(2019, 3, 1)
        response_data, code, headers = stats_page.get_monthly_downloads_page()

        mock_get_monthly_download_count.assert_called_once()
        mock_get_max_download_stats_dt.assert_called_once()
        self.assertEqual(code, status.OK)
        self.assertIn("total_downloads", response_data)
        self.assertIn("most_recent_dt", response_data)

    @mock.patch("browse.controllers.stats_page.get_monthly_download_stats")
    def test_get_download_stats_csv(self, mock_get_monthly_download_stats) -> None:  # type: ignore
        """Tests for :func:`.get_monthly_download_stats_csv`."""
        # test basic response
        mock_get_monthly_download_stats.return_value = list()
        response_data, code, headers = stats_page.get_download_stats_csv()
        mock_get_monthly_download_stats.assert_called_once()
        mock_get_monthly_download_stats.reset_mock()
        self.assertEqual(code, status.OK)
        self.assertEqual(headers["Content-Type"], "text/csv")
        self.assertIn("csv", response_data, "csv is in response data")
        self.assertEqual(response_data["csv"], "month,downloads\n")

        # test response with mock data
        mock_get_monthly_download_stats.return_value = [
            mock.Mock(ym=datetime(2017, 1, 1), downloads=1234567),
            mock.Mock(ym=datetime(2017, 2, 1), downloads=2345678),
        ]
        expected_response = "month,downloads\n" "2017-01,1234567\n" "2017-02,2345678\n"
        response_data, code, headers = stats_page.get_download_stats_csv()
        self.assertEqual(code, status.OK)
        self.assertEqual(response_data["csv"], expected_response)

    @mock.patch("browse.controllers.stats_page.get_document_count_by_yymm")
    @mock.patch("browse.controllers.stats_page.get_monthly_submission_count")
    def test_get_monthly_submissions_page(
        self, mock_get_monthly_submission_count, mock_get_document_count_by_yymm
    ) -> None:  # type: ignore
        """Tests for :func:`.get_monthly_submissions_page`."""
        # test basic response
        mock_get_document_count_by_yymm.return_value = 0
        mock_get_monthly_submission_count.return_value = (0, 0)
        response_data, code, headers = stats_page.get_monthly_submissions_page()
        mock_get_monthly_submission_count.assert_called_once()
        mock_get_monthly_submission_count.reset_mock()
        self.assertEqual(code, status.OK)

        for key in [
            "num_migrated",
            "num_deleted",
            "num_submissions",
            "current_dt",
            "arxiv_start_dt",
            "arxiv_age_years",
            "num_submissions_adjusted",
        ]:
            self.assertIn(key, response_data, f"{key} is in response_data")
            self.assertIsNotNone(
                response_data[key], f"response_data[{key}] is not None"
            )

        # test response with mock data
        mock_get_monthly_submission_count.return_value = (1123456, -501)
        response_data, code, headers = stats_page.get_monthly_submissions_page()
        mock_get_monthly_submission_count.assert_called_once()
        self.assertEqual(code, status.OK)
        self.assertEqual(response_data["num_migrated"], 501)
        self.assertEqual(response_data["num_submissions"], 1123301)
        expected_submissions_adjusted = (
            response_data["num_submissions"] + response_data["num_migrated"]
        )
        self.assertEqual(
            response_data["num_submissions_adjusted"], expected_submissions_adjusted
        )
        self.assertGreaterEqual(response_data["num_deleted"], 155)
        self.assertGreater(response_data["arxiv_age_years"], 25, "arXiv may rent a car")
        self.assertIsInstance(response_data["current_dt"], datetime)
        self.assertIsInstance(response_data["arxiv_start_dt"], datetime)

    @mock.patch("browse.controllers.stats_page.get_document_count_by_yymm")
    @mock.patch("browse.controllers.stats_page.get_monthly_submission_stats")
    def test_get_submission_stats_csv(
        self, mock_get_monthly_submission_stats, mock_get_document_count_by_yymm
    ) -> None:  # type: ignore
        """Tests for :func:`.get_submission_stats_csv`."""
        # test basic response
        mock_get_document_count_by_yymm.return_value = 0
        mock_get_monthly_submission_stats.return_value = list()
        response_data, code, headers = stats_page.get_submission_stats_csv()
        self.assertEqual(code, status.OK)
        self.assertEqual(headers["Content-Type"], "text/csv")
        self.assertIn("csv", response_data, "csv is in response data")
        self.assertEqual(response_data["csv"], "month,submissions,historical_delta\n")

        # test response with mock data
        mock_get_document_count_by_yymm.return_value = 0
        mock_get_monthly_submission_stats.return_value = [
            mock.Mock(ym=date(2019, 2, 1), num_submissions=9999, historical_delta=-42),
            mock.Mock(ym=date(2019, 3, 1), num_submissions=10101, historical_delta=0),
        ]
        expected_response = (
            "month,submissions,historical_delta\n"
            "2019-02,9999,-42\n"
            "2019-03,10101,0\n"
        )
        response_data, code, headers = stats_page.get_submission_stats_csv()
        self.assertEqual(code, status.OK)
        self.assertEqual(response_data["csv"], expected_response)
