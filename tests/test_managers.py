import unittest
from pathlib import Path

from django.test import SimpleTestCase, tag

from complex_rest_dtcd_supergraph.managers import Manager


TEST_DIR = Path(__file__).resolve().parent


@tag("neo4j")
class TestManager(SimpleTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pass  # clear the db

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def tearDown(self) -> None:
        pass


if __name__ == "__main__":
    unittest.main()
