import unittest

from ordbok.import_nivalistor import (
    LexemRad,
    deduplicera,
    infer_japanese_pos,
    infer_spanish_level,
    map_pos_common,
    normalisera_cefr,
    normalisera_jlpt,
    normalisera_lemma,
)


class TestImportNivalistorUnit(unittest.TestCase):
    def test_normalisera_lemma(self):
        self.assertEqual(normalisera_lemma("  a_b   c "), "a b c")

    def test_normalisera_cefr(self):
        self.assertEqual(normalisera_cefr("b2"), "B2")
        self.assertIsNone(normalisera_cefr("X9"))

    def test_normalisera_jlpt(self):
        self.assertEqual(normalisera_jlpt("jlpt_n4"), "N4")
        self.assertEqual(normalisera_jlpt("JLPT_3"), "N3")
        self.assertIsNone(normalisera_jlpt("cefr-a1"))

    def test_map_pos_common(self):
        self.assertEqual(map_pos_common("noun"), "Noun")
        self.assertEqual(map_pos_common("VER"), "Verb")
        self.assertEqual(map_pos_common("NCF"), "Noun")
        self.assertEqual(map_pos_common("AO0"), "Adjective")
        self.assertEqual(map_pos_common("prep"), "Preposition")
        self.assertEqual(map_pos_common("particle"), "Particle")
        self.assertEqual(map_pos_common("subj"), "Conjunction")
        self.assertEqual(map_pos_common("particip"), "Adjective")
        self.assertEqual(map_pos_common("PT0"), "Pronoun")

    def test_infer_spanish_level_dominant_peak(self):
        row = {
            "level_freq@a1": "100",
            "level_freq@a2": "0",
            "level_freq@b1": "0",
            "level_freq@b2": "0",
            "level_freq@c1": "0",
        }
        self.assertEqual(infer_spanish_level(row), "A1")

    def test_infer_spanish_level_weighted(self):
        row = {
            "level_freq@a1": "1",
            "level_freq@a2": "2",
            "level_freq@b1": "3",
            "level_freq@b2": "4",
            "level_freq@c1": "5",
        }
        self.assertEqual(infer_spanish_level(row), "B2")

    def test_infer_japanese_pos(self):
        self.assertEqual(infer_japanese_pos("食べる", "to eat"), "Verb")
        self.assertEqual(infer_japanese_pos("安心する", "to feel relieved"), "Verb")
        self.assertEqual(infer_japanese_pos("新しい", "new"), "Adjective")
        self.assertEqual(infer_japanese_pos("学校", "school"), "Unknown")

    def test_deduplicera_keep_lowest_level(self):
        rows = [
            LexemRad("walk", "en", "Verb", "B2", "x"),
            LexemRad("walk", "en", "Verb", "A2", "y"),
            LexemRad("歩く", "ja", "Verb", "N3", "x"),
            LexemRad("歩く", "ja", "Verb", "N5", "y"),
        ]
        out = deduplicera(rows)
        result = {(r.lemma, r.språk, r.ordklass): r.nivå for r in out}
        self.assertEqual(result[("walk", "en", "Verb")], "A2")
        self.assertEqual(result[("歩く", "ja", "Verb")], "N5")


if __name__ == "__main__":
    unittest.main()
