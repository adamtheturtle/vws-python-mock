"""
Tests for helper function for adding a target to a Vuforia database.
"""

import io
from typing import Optional

import pytest
from mock_vws import MockVWS
from mock_vws.database import VuforiaDatabase

from vws import VWS
from vws.exceptions import UnknownTarget


class TestAddTarget:
    """
    Tests for adding a target.
    """

    def test_add_target(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when adding one target.
        """
        name = 'x'
        width = 1
        target_id = client.add_target(
            name=name,
            width=width,
            image=high_quality_image,
        )
        target_record = client.get_target_record(target_id=target_id)
        assert target_record['name'] == name
        assert target_record['width'] == width
        assert target_record['active_flag'] is True

    def test_add_two_targets(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        No exception is raised when adding two targets with different names.

        This demonstrates that the image seek position is not changed.
        """
        client.add_target(name='x', width=1, image=high_quality_image)
        client.add_target(name='a', width=1, image=high_quality_image)

    @pytest.mark.parametrize('application_metadata', [None, b'a'])
    def test_valid_metadata(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
        application_metadata: Optional[bytes],
    ) -> None:
        """
        No exception is raised when ``None`` or bytes is given.
        """
        client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            application_metadata=application_metadata,
        )

    @pytest.mark.parametrize('active_flag', [True, False])
    def test_active_flag_given(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
        active_flag: bool,
    ) -> None:
        """
        It is possible to set the active flag to a boolean value.
        """
        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
            active_flag=active_flag,
        )
        target_record = client.get_target_record(target_id=target_id)
        assert target_record['active_flag'] is active_flag


class TestCustomBaseVWSURL:
    """
    Tests for using a custom base VWS URL.
    """

    def test_custom_base_url(self, high_quality_image: io.BytesIO) -> None:
        """
        It is possible to use add a target to a database under a custom VWS
        URL.
        """
        base_vws_url = 'http://example.com'
        with MockVWS(base_vws_url=base_vws_url) as mock:
            database = VuforiaDatabase()
            mock.add_database(database=database)
            client = VWS(
                server_access_key=database.server_access_key.decode(),
                server_secret_key=database.server_secret_key.decode(),
                base_vws_url=base_vws_url,
            )

            client.add_target(
                name='x',
                width=1,
                image=high_quality_image,
            )


class TestListTargets:
    """
    Tests for listing targets.
    """

    def test_list_targets(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        It is possible to get a list of target IDs.
        """
        id_1 = client.add_target(name='x', width=1, image=high_quality_image)
        id_2 = client.add_target(name='a', width=1, image=high_quality_image)
        assert sorted(client.list_targets()) == sorted([id_1, id_2])


class TestDelete:
    """
    Test for deleting a target.
    """

    def test_delete_target(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        It is possible to delete a target.
        """
        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
        )

        client.wait_for_target_processed(target_id=target_id)
        client.delete_target(target_id=target_id)
        with pytest.raises(UnknownTarget):
            client.get_target_record(target_id=target_id)


class TestGetTargetSummaryReport:
    """
    Tests for getting a summary report for a target.
    """

    def test_get_target_summary_report(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        Details of a target are returned by ``get_target_summary_report``.
        """
        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
        )

        result = client.get_target_summary_report(target_id=target_id)
        expected_keys = {
            'status',
            'result_code',
            'transaction_id',
            'database_name',
            'target_name',
            'upload_date',
            'active_flag',
            'tracking_rating',
            'total_recos',
            'current_month_recos',
            'previous_month_recos',
        }
        assert result.keys() == expected_keys


class TestGetDatabaseSummaryReport:
    """
    Tests for getting a summary report for a database.
    """

    def test_get_target(self, client: VWS) -> None:
        """
        Details of a database are returned by ``get_database_summary_report``.
        """
        report = client.get_database_summary_report()
        expected_keys = {
            'active_images',
            'current_month_recos',
            'failed_images',
            'inactive_images',
            'name',
            'previous_month_recos',
            'processing_images',
            'reco_threshold',
            'request_quota',
            'request_usage',
            'result_code',
            'target_quota',
            'total_recos',
            'transaction_id',
        }
        assert report.keys() == expected_keys


class TestGetTargetRecord:
    """
    Tests for getting a record of a target.
    """

    def test_get_target_record(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        Details of a target are returned by ``get_target_record``.
        """
        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
        )

        result = client.get_target_record(target_id=target_id)

        expected_keys = {
            'target_id',
            'active_flag',
            'name',
            'width',
            'tracking_rating',
            'reco_rating',
        }
        assert result.keys() == expected_keys


class TestWaitForTargetProcessed:
    """
    Tests for waiting for a target to be processed.
    """

    def test_wait_for_target_processed(
        self,
        client: VWS,
        high_quality_image: io.BytesIO,
    ) -> None:
        """
        It is possible to wait until a target is processed.
        """
        target_id = client.add_target(
            name='x',
            width=1,
            image=high_quality_image,
        )
        report = client.get_target_summary_report(target_id=target_id)
        assert report['status'] == 'processing'
        client.wait_for_target_processed(target_id=target_id)
        report = client.get_target_summary_report(target_id=target_id)
        assert report['status'] != 'processing'