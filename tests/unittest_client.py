from datetime import datetime, timezone
import os
import unittest
import uuid

from cord.client import CordClient
from cord.exceptions import (
    AuthenticationError, AuthorisationError,
    OperationNotAllowed, ResourceExistsError)
from cord.orm.label_row import LabelRow
from tests.test_data.interpolation_test_blurb import INTERPOLATION_TEST_BLURB
from tests.test_data.test_blurb import TEST_BLURB

LABEL_READ_WRITE_KEY = 'aJpUqf1UifGGc-c10MjbQ_ze7G6SOs0d-SwfO8D_Ntg'
LABEL_READ_KEY = '1xI0y7cHYPPZRzCpDvk9WIBMfeonkKVBxjjgJHuYiUI'
LABEL_WRITE_KEY = 'CPNuaX5_eubBdx9CJ-sZrj1ZkqL_51L-Dd27dZ9bi_4'
PROJECT_ID = '5036161d-3da4-4711-8301-d1901fc7b349'
DATA_ID = 'e8296743-577e-4b5b-b151-0a6254535ed3'
IMG_GROUP_DATA_ID = ''
LABEL_ID = '23813f86-b352-4c61-bde1-bf8ab00611d5'
OH = "0b402f38-bc7b-4cae-be94-f963a6713de5"

DATASET_ID = '93acfbf8-77db-48d9-90a9-2a9b9065511c'
DATASET_KEY = 'G26da4vZFI096OSnwSVZbO9TDIyYF2_OdODKNakJEQk'

"""
    Dev tests for Client (local)
"""


class UnitTests(unittest.TestCase):
    def setUp(self):
        pass

    @classmethod
    def setUpClass(cls):
        super(UnitTests, cls).setUpClass()
        cls.read_c = CordClient.initialise(PROJECT_ID, LABEL_READ_KEY)
        cls.write_c = CordClient.initialise(PROJECT_ID, LABEL_WRITE_KEY)
        cls.rw_c = CordClient.initialise(PROJECT_ID, LABEL_READ_WRITE_KEY)
        cls.dt_c = CordClient.initialise(DATASET_ID, DATASET_KEY)

    def test_create_label_wrong_data_hash(self):
        with self.assertRaises(AuthorisationError):
            self.rw_c.create_label_row('some_random_data_hash')

    def test_create_label_when_exists(self):
        with self.assertRaises(ResourceExistsError):
            self.rw_c.create_label_row(DATA_ID)
            self.rw_c.create_label_row(DATA_ID)

    def test_create_label_with_readonly(self):
        with self.assertRaises(OperationNotAllowed):
            self.read_c.create_label_row(DATA_ID)

    def test_1(self):
        with self.assertRaises(AuthenticationError) as excinfo:
            CordClient.initialise(PROJECT_ID)
        self.assertEqual(
            'API key not provided',
            str(excinfo.exception)
        )

    def test_2(self):
        with self.assertRaises(AuthenticationError) as excinfo:
            CordClient.initialise(api_key=LABEL_READ_WRITE_KEY)
        self.assertEqual(
            'Project ID or dataset ID not provided',
            str(excinfo.exception)
        )

    def test_3(self):
        with self.assertRaises(AuthenticationError):
            client = CordClient.initialise(PROJECT_ID, uuid.uuid4())

    def test_4(self):
        with self.assertRaises(AuthenticationError):
            client = CordClient.initialise(uuid.uuid4(), LABEL_READ_WRITE_KEY)

    def test_5(self):
        assert isinstance(self.rw_c.get_label_row(LABEL_ID), LabelRow)

    def test_6(self):
        with self.assertRaises(AuthorisationError):
            self.rw_c.get_label_row('test')

    def test_7(self):
        with self.assertRaises(OperationNotAllowed):
            self.write_c.get_label_row(LABEL_ID)

    def test_8(self):
        new_test_blurb = TEST_BLURB.copy()
        wrong_id = "97681cfa-0c3a-4ebe-aba3-f17e136fc231"
        new_test_blurb['data_units'][DATA_ID] = new_test_blurb['data_units'][wrong_id]
        del new_test_blurb['data_units'][wrong_id]
        new_test_blurb['data_units'][DATA_ID]["data_hash"] = DATA_ID
        blurb = self.rw_c.save_label_row(LABEL_ID, TEST_BLURB)
        assert blurb is True

    def test_10(self):
        with self.assertRaises(AuthorisationError):
            self.rw_c.save_label_row('test', TEST_BLURB)

    def test_11(self):
        with self.assertRaises(OperationNotAllowed):
            self.read_c.save_label_row(LABEL_ID, TEST_BLURB)

    def test_12(self):
        test_blurb = INTERPOLATION_TEST_BLURB.copy()
        for key, val in test_blurb.items():
            new_list = []
            for v in test_blurb[key]["objects"]:
                v["objectHash"] = OH
                new_list.append(v.copy())
            test_blurb[key]["objects"] = new_list.copy()
        objects = self.rw_c.object_interpolation(test_blurb,
                                                 ['60f75ddb-aa68-4654-8c85-f6959dbb62eb'])
        assert isinstance(objects, dict)

    def test_upload_video(self):
        path = os.path.dirname(__file__)
        video_path = os.path.join(path, 'test_data', 'media', 'video.mp4')
        self.dt_c.upload_video(video_path)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        dataset = self.dt_c.get_dataset()
        assert len(dataset) > 0
        passed = False
        for dt in dataset.get('data_rows', []):
            if dt.get('data_title', '') == 'video.mp4':
                then_time = datetime.strptime(
                    dt.get('created_at'), '%Y-%m-%d %H:%M:%S'
                )
                delta = int((now - then_time).total_seconds())
                if delta >= 0 & delta <= 1 * 60:
                    passed = True
        assert passed

    def test_upload_image_group(self):
        path = os.path.dirname(__file__)
        im1 = os.path.join(path, 'test_data', 'media', 'screen1.png')
        im2 = os.path.join(path, 'test_data', 'media', 'screen1.png')
        image_group_name = self.dt_c.create_image_group([im1, im2])
        assert 'image-group-' in image_group_name,\
            'Upload did not complete successfully'


if __name__ == '__main__':
    unittest.main()
