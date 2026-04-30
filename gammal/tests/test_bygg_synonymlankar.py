import unittest
from collections import defaultdict

from ordbok.bygg_synonymlankar import (
    Lexem,
    build_links_and_unresolved,
    classify_candidate,
    parse_concept_uri,
)


class TestByggSynonymlankar(unittest.TestCase):
    def test_parse_concept_uri_with_pos(self):
        self.assertEqual(parse_concept_uri("/c/en/run/v"), ("en", "run", "v"))

    def test_parse_concept_uri_without_pos(self):
        self.assertEqual(parse_concept_uri("/c/sv/hund"), ("sv", "hund", None))

    def test_classify_target_evidence_match(self):
        status = classify_candidate("v", {"v"}, set())
        self.assertEqual(status, "validated")

    def test_classify_source_only_match(self):
        status = classify_candidate("n", set(), {"n"})
        self.assertEqual(status, "validated")

    def test_classify_unknown_when_no_evidence(self):
        status = classify_candidate("a", set(), set())
        self.assertEqual(status, "unknown")

    def test_classify_contradiction(self):
        status = classify_candidate("v", {"n"}, set())
        self.assertEqual(status, "contradiction_only")

    def test_classify_mixed_conflict(self):
        status = classify_candidate("n", {"n", "a"}, set())
        self.assertEqual(status, "mixed_conflict")

    def test_build_links_infers_pos_for_unknown_source(self):
        lexemes = [
            Lexem(1, "犬", "犬", "ja", "Unknown", "N5", "n5.csv", None),
            Lexem(2, "dog", "dog", "en", "Noun", "A1", "oxford5000.json", "n"),
        ]
        pos_map = {lang: defaultdict(set) for lang in {"sv", "en", "fr", "es", "it", "ja", "de"}}
        candidates = {
            ("en", "dog"): [
                {
                    "target_lang": "ja",
                    "target_lemma": "犬",
                    "source_pos": "n",
                    "target_uri_pos": None,
                    "target_exists": True,
                }
            ],
            ("ja", "犬"): [
                {
                    "target_lang": "en",
                    "target_lemma": "dog",
                    "source_pos": None,
                    "target_uri_pos": None,
                    "target_exists": True,
                }
            ]
        }

        links, unresolved = build_links_and_unresolved(lexemes, pos_map, candidates)
        forward = [l for l in links if l["source_lexem_id"] == 1 and l["target_lexem_id"] == 2]
        self.assertEqual(len(forward), 1)
        self.assertEqual(forward[0]["source_pos"], "Noun")
        self.assertTrue(any(u["lemma"] == "犬" for u in unresolved))

    def test_build_links_keeps_unknown_target_linkable(self):
        lexemes = [
            Lexem(1, "dog", "dog", "en", "Noun", "A1", "oxford5000.json", "n"),
            Lexem(2, "犬", "犬", "ja", "Unknown", "N5", "n5.csv", None),
        ]
        pos_map = {lang: defaultdict(set) for lang in {"sv", "en", "fr", "es", "it", "ja", "de"}}
        candidates = {
            ("en", "dog"): [
                {
                    "target_lang": "ja",
                    "target_lemma": "犬",
                    "source_pos": None,
                    "target_uri_pos": None,
                    "target_exists": True,
                }
            ]
        }

        links, _ = build_links_and_unresolved(lexemes, pos_map, candidates)
        forward = [l for l in links if l["source_lexem_id"] == 1 and l["target_lexem_id"] == 2]
        self.assertEqual(len(forward), 1)

    def test_build_links_respects_explicit_source_edge_pos(self):
        lexemes = [
            Lexem(1, "abfahren", "abfahren", "de", "Unknown", "A1", "cefr_vocab.csv", None),
            Lexem(2, "fara", "fara", "sv", "Verb", "A1", "Swedish-Kelly_M3_CEFR.xls", "v"),
            Lexem(3, "fara", "fara", "sv", "Noun", "A2", "Swedish-Kelly_M3_CEFR.xls", "n"),
        ]
        pos_map = {lang: defaultdict(set) for lang in {"sv", "en", "fr", "es", "it", "ja", "de"}}
        candidates = {
            ("sv", "fara"): [
                {
                    "target_lang": "de",
                    "target_lemma": "abfahren",
                    "source_pos": "v",
                    "target_uri_pos": None,
                    "target_exists": True,
                }
            ],
            ("de", "abfahren"): [
                {
                    "target_lang": "sv",
                    "target_lemma": "fara",
                    "source_pos": "v",
                    "target_uri_pos": None,
                    "target_exists": True,
                }
            ]
        }

        links, _ = build_links_and_unresolved(lexemes, pos_map, candidates)
        forward = [l for l in links if l["source_lexem_id"] == 1 and l["target_lexem_id"] == 2]
        self.assertEqual(len(forward), 1)
        self.assertEqual(forward[0]["source_pos"], "Verb")

    def test_build_links_allows_non_core_pos_by_exact_label_match(self):
        lexemes = [
            Lexem(1, "and", "and", "en", "Conjunction", "A1", "oxford5000.json", None),
            Lexem(2, "och", "och", "sv", "Conjunction", "A1", "Swedish-Kelly_M3_CEFR.xls", None),
            Lexem(3, "och", "och", "sv", "Noun", "A2", "Swedish-Kelly_M3_CEFR.xls", "n"),
        ]
        pos_map = {lang: defaultdict(set) for lang in {"sv", "en", "fr", "es", "it", "ja", "de"}}
        candidates = {
            ("en", "and"): [
                {
                    "target_lang": "sv",
                    "target_lemma": "och",
                    "source_pos": None,
                    "target_uri_pos": None,
                    "target_exists": True,
                }
            ]
        }

        links, _ = build_links_and_unresolved(lexemes, pos_map, candidates)
        forward = [l for l in links if l["source_lexem_id"] == 1]
        self.assertEqual(len(forward), 1)
        self.assertEqual(forward[0]["target_lexem_id"], 2)


if __name__ == "__main__":
    unittest.main()
