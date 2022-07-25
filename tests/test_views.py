import unittest
from pathlib import Path

import neomodel
from django.urls import reverse
from django.test import Client, tag
from rest_framework import status
from rest_framework.test import APISimpleTestCase

from .misc import load_data, sort_payload


TEST_DIR = Path(__file__).resolve().parent
DATA_DIR = TEST_DIR / "data"
URL_RESET = reverse("supergraph:reset")  # post here resets the db
CLIENT = Client()


def reset_db():
    neomodel.clear_neo4j_database(neomodel.db)


class Neo4jTestCaseMixin:
    """A mixin for API tests of a Neo4j-based endpoint.

    Adds calls to reset the database on class setup and on teardowns of each test.
    """

    @classmethod
    def setUpClass(cls) -> None:
        # clean db on start
        reset_db()

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def tearDown(self) -> None:
        # clean after each test
        reset_db()


@tag("neo4j")
class TestFragmentListView(Neo4jTestCaseMixin, APISimpleTestCase):
    url = reverse("supergraph:fragments")

    def test_post(self):
        response = self.client.post(self.url, data={"name": "sales"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        fragment = response.data["fragment"]
        self.assertIn("id", fragment)
        self.assertEqual(fragment["name"], "sales")

    def test_get(self):
        names = {"hr", "marketing", "sales"}
        for name in names:
            self.client.post(self.url, data={"name": name}, format="json")
        response = self.client.get(self.url)
        data = response.data
        fragments = data["fragments"]
        self.assertEqual({f["name"] for f in fragments}, names)


@tag("neo4j")
class TestFragmentDetailView(Neo4jTestCaseMixin, APISimpleTestCase):
    def setUp(self) -> None:
        # default fragment
        response = self.client.post(
            TestFragmentListView.url,
            data={"name": "sales"},
            format="json",
        )
        self.fragment = response.data["fragment"]
        self.pk = self.fragment["id"]
        self.url = reverse("supergraph:fragment-detail", args=(self.pk,))

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fragment = response.data["fragment"]
        self.assertEqual(fragment["id"], self.pk)
        self.assertEqual(fragment["name"], "sales")

    def test_put(self):
        data = {"name": "marketing"}
        response = self.client.put(self.url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # get detail back with the same pk
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fragment = response.data["fragment"]
        self.assertEqual(fragment["name"], "marketing")

    def test_delete(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GraphEndpointTestCaseMixin:
    def merge(self, graph: dict):
        data = {"graph": graph}
        return self.client.put(self.url, data=data, format="json")

    def retrieve(self) -> dict:
        r = self.client.get(self.url)
        return r.data["graph"]

    def assert_merge_retrieve_eq(self, graph: dict):
        self.merge(graph)
        fromdb = self.retrieve()
        sort_payload(fromdb)
        self.assertEqual(fromdb, graph)

    def assert_merge_retrieve_eq_from_json(self, path):
        data = load_data(path)
        self.assert_merge_retrieve_eq(data)


@unittest.skip("not implemented")
@tag("neo4j")
class TestRootGraphView(
    GraphEndpointTestCaseMixin, Neo4jTestCaseMixin, APISimpleTestCase
):
    url = reverse("supergraph:root-graph")

    def test_get_empty(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        graph = r.data["graph"]
        self.assertEqual(graph, {"nodes": [], "edges": []})

    def test_basic(self):
        path = DATA_DIR / "basic.json"
        self.assert_merge_retrieve_eq_from_json(path)

    def test_basic_attributes(self):
        path = DATA_DIR / "basic-attributes.json"
        self.assert_merge_retrieve_eq_from_json(path)

    def test_basic_nested_attributes(self):
        path = DATA_DIR / "basic-nested-attributes.json"
        self.assert_merge_retrieve_eq_from_json(path)

    def test_basic_edges(self):
        path = DATA_DIR / "basic-edges.json"
        self.assert_merge_retrieve_eq_from_json(path)

    def test_basic_nested_edges(self):
        path = DATA_DIR / "basic-nested-edges.json"
        self.assert_merge_retrieve_eq_from_json(path)

    def test_basic_ports(self):
        path = DATA_DIR / "basic-ports.json"
        self.assert_merge_retrieve_eq_from_json(path)

    def test_basic_nested_ports(self):
        path = DATA_DIR / "basic-nested-ports.json"
        self.assert_merge_retrieve_eq_from_json(path)

    def test_basic_groups(self):
        path = DATA_DIR / "basic-groups.json"
        self.assert_merge_retrieve_eq_from_json(path)

    def test_sample(self):
        path = DATA_DIR / "sample.json"
        self.assert_merge_retrieve_eq_from_json(path)

    @tag("slow")
    def test_n25_e25(self):
        path = DATA_DIR / "n25_e25.json"
        self.assert_merge_retrieve_eq_from_json(path)

    @tag("slow")
    def test_n50_e25(self):
        path = DATA_DIR / "n50_e25.json"
        self.assert_merge_retrieve_eq_from_json(path)

    @tag("slow")
    def test_n25_then_n50(self):
        # first merge
        old = load_data(DATA_DIR / "n25_e25.json")
        self.merge(old)

        # over-write
        new_path = DATA_DIR / "n50_e25.json"
        self.assert_merge_retrieve_eq_from_json(new_path)


@unittest.skip("not implemented")
class TestFragmentGraphView(
    GraphEndpointTestCaseMixin, Neo4jTestCaseMixin, APISimpleTestCase
):
    def setUp(self):
        super().setUp()

        # create a fragment
        r = self.client.post(
            TestFragmentListView.url, data={"name": "marketing"}, format="json"
        )
        id_ = r.data["fragment"]["id"]
        self.url = reverse("supergraph:fragment-graph", args=(id_,))

    @tag("slow")
    def test_n25_e25(self):
        path = DATA_DIR / "n25_e25.json"
        self.assert_merge_retrieve_eq_from_json(path)

    @tag("slow")
    def test_n50_e25(self):
        path = DATA_DIR / "n50_e25.json"
        self.assert_merge_retrieve_eq_from_json(path)

    @tag("slow")
    def test_n25_then_n50(self):
        old = load_data(DATA_DIR / "n25_e25.json")
        self.merge(old)
        new_path = DATA_DIR / "n50_e25.json"
        self.assert_merge_retrieve_eq_from_json(new_path)

    def test_basic_groups(self):
        path = DATA_DIR / "basic-groups.json"
        self.assert_merge_retrieve_eq_from_json(path)


# TODO combined tests
@unittest.skip("not implemented")
class TestFragmentGroupInteraction(
    GraphEndpointTestCaseMixin, Neo4jTestCaseMixin, APISimpleTestCase
):
    def setUp(self):
        super().setUp()

        # create a fragment
        r = self.client.post(
            TestFragmentListView.url, data={"name": "marketing"}, format="json"
        )
        id_ = r.data["fragment"]["id"]
        self.url = reverse("supergraph:fragment-graph", args=(id_,))

    @unittest.expectedFailure
    def test_root_merge_overwrite(self):
        # merge fragment with some data
        old = load_data(DATA_DIR / "basic.json")
        self.merge(old)

        # merge root with other data
        new = {"nodes": [{"primitiveID": "cloe"}], "edges": []}
        self.merge(new)  # FIXME this sends req to fragment URL, not root URL

        # make sure fragment is empty
        fragment = self.retrieve()
        self.assertEqual(fragment, {"nodes": [], "edges": []})

    # TODO interaction tests
    # merge
    # fragment, then root
    # root management over-writes fragments data
    # merge f1, f2, get root = combination
    # merge of existing nodes preserves frontier connections
    # merge fragment, then root with same vertices / edges


if __name__ == "__main__":
    unittest.main()
