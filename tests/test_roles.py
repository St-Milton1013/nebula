import unittest

from nebula.cardtruth import CardTruth
from nebula.importer import parse_decklist
from nebula.roles import RoleClassifier
from nebula.tagger import Tags

TAG_STORE = {
    "ramp": {"id": "t1", "label": "ramp", "parents": [], "children": ["t2"]},
    "ramp-creature": {"id": "t2", "label": "ramp-creature", "parents": ["t1"], "children": []},
    "card advantage": {"id": "t3", "label": "card advantage", "parents": [], "children": []},
    "tutor": {"id": "t4", "label": "tutor", "parents": [], "children": []},
    "removal": {"id": "t5", "label": "removal", "parents": [], "children": []},
    "counterspell": {"id": "t6", "label": "counterspell", "parents": [], "children": []},
    "sweeper": {"id": "t7", "label": "sweeper", "parents": [], "children": []},
    "protection": {"id": "t8", "label": "protection", "parents": [], "children": []},
    "hate": {"id": "t9", "label": "hate", "parents": [], "children": []},
    "recursion": {"id": "t10", "label": "recursion", "parents": [], "children": []},
}

BY_ORACLE = {
    "oid-sol": ["ramp"],
    "oid-birds": ["ramp-creature"],
    "oid-draw": ["card advantage"],
    "oid-tutor": ["tutor"],
}

RECORDS = [
    {"name": "Sol Ring", "oracle_id": "oid-sol", "type_line": "Artifact"},
    {"name": "Birds of Paradise", "oracle_id": "oid-birds", "type_line": "Creature - Bird"},
    {"name": "Brainstorm", "oracle_id": "oid-draw", "type_line": "Instant"},
    {"name": "Demonic Tutor", "oracle_id": "oid-tutor", "type_line": "Sorcery"},
    {"name": "Island", "oracle_id": "oid-island", "type_line": "Basic Land - Island"},
    {"name": "Untagged Rock", "oracle_id": "oid-untagged", "type_line": "Artifact"},
]


class TagTests(unittest.TestCase):
    def setUp(self):
        self.tags = Tags(TAG_STORE, BY_ORACLE)

    def test_ancestry_includes_parents(self):
        self.assertEqual(self.tags.ancestors("ramp-creature"), frozenset({"ramp", "ramp-creature"}))
        self.assertEqual(self.tags.ancestors("ramp"), frozenset({"ramp"}))

    def test_slug_for_label(self):
        self.assertEqual(self.tags.slug_for("Card Advantage"), "card advantage")

    def test_tags_for_unknown_oracle(self):
        self.assertEqual(self.tags.tags_for("nope"), [])
        self.assertEqual(self.tags.tags_for(None), [])


class RoleTests(unittest.TestCase):
    def setUp(self):
        self.truth = CardTruth.from_records(RECORDS)
        self.classifier = RoleClassifier(Tags(TAG_STORE, BY_ORACLE), self.truth)

    def test_child_tag_counts_for_parent_role(self):
        roles, state = self.classifier.roles_for("Birds of Paradise")
        self.assertEqual(state, "CLASSIFIED")
        self.assertIn("ramp", roles)

    def test_land_is_its_own_state(self):
        roles, state = self.classifier.roles_for("Island")
        self.assertEqual((roles, state), ([], "LAND"))

    def test_untagged_card_is_reported(self):
        roles, state = self.classifier.roles_for("Untagged Rock")
        self.assertEqual((roles, state), ([], "UNTAGGED"))

    def test_unknown_card_is_unresolved(self):
        roles, state = self.classifier.roles_for("Not A Real Card")
        self.assertEqual((roles, state), ([], "UNRESOLVED"))

    def test_classify_counts_quantities_not_entries(self):
        deck = parse_decklist("Commander\n1 Birds of Paradise\n\nMainboard\n2 Sol Ring\n1 Island\n")
        out = self.classifier.classify(deck)
        self.assertEqual(out["counts"]["ramp"], 3)  # 1 Birds + 2 Sol Ring
        self.assertEqual(out["coverage"]["lands"], 1)
        self.assertEqual(out["coverage"]["nonland"], 2)
        self.assertEqual(out["coverage"]["classified"], 2)

    def test_missing_anchor_makes_it_partial(self):
        thin = Tags({"ramp": TAG_STORE["ramp"]}, {"oid-sol": ["ramp"]})
        classifier = RoleClassifier(thin, self.truth)
        self.assertTrue(classifier.missing_anchors)
        out = classifier.classify(parse_decklist("1 Sol Ring\n"))
        self.assertEqual(out["status"], "PARTIAL")


if __name__ == "__main__":
    unittest.main()
