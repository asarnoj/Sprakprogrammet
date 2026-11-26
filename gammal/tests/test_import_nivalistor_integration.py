import sqlite3
import unittest
from pathlib import Path

from ordbok import import_nivalistor


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "ordbok" / "lexem_niva.db"


class TestImportNivalistorIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import_nivalistor.main()
        cls.con = sqlite3.connect(DB_PATH)

    @classmethod
    def tearDownClass(cls):
        cls.con.close()

    def test_database_created(self):
        self.assertTrue(DB_PATH.exists())

    def test_required_columns_non_null(self):
        q = """
            SELECT COUNT(*) FROM lexem_niva
            WHERE lemma IS NULL OR lemma = ''
               OR language IS NULL OR language = ''
               OR pos IS NULL OR pos = ''
               OR level IS NULL OR level = ''
               OR source IS NULL OR source = ''
        """
        count = self.con.execute(q).fetchone()[0]
        self.assertEqual(count, 0)

    def test_all_languages_present(self):
        langs = {r[0] for r in self.con.execute("SELECT DISTINCT language FROM lexem_niva")}
        self.assertEqual(langs, {"sv", "en", "fr", "es", "it", "ja", "de"})

    def test_level_domain(self):
        allowed = {"A1", "A2", "B1", "B2", "C1", "C2", "N5", "N4", "N3", "N2", "N1"}
        levels = {r[0] for r in self.con.execute("SELECT DISTINCT level FROM lexem_niva")}
        self.assertTrue(levels.issubset(allowed))
        self.assertGreater(len(levels), 0)

    def test_no_duplicate_key(self):
        q = """
            SELECT COUNT(*) FROM (
                SELECT language, lemma, pos, COUNT(*) c
                FROM lexem_niva
                GROUP BY language, lemma, pos
                HAVING c > 1
            )
        """
        dup_groups = self.con.execute(q).fetchone()[0]
        self.assertEqual(dup_groups, 0)

    def test_each_language_has_data(self):
        rows = self.con.execute(
            "SELECT language, COUNT(*) FROM lexem_niva GROUP BY language"
        ).fetchall()
        for _, c in rows:
            self.assertGreater(c, 0)

    def test_reasonable_unknown_pos_bounds(self):
        # Vi accepterar okända ordklasser där källan saknar POS (särskilt japanska),
        # men bevakar att det inte skenar.
        counts = dict(
            self.con.execute(
                """
                SELECT language, COUNT(*)
                FROM lexem_niva
                WHERE pos = 'Unknown'
                GROUP BY language
                """
            ).fetchall()
        )
        self.assertLessEqual(counts.get("sv", 0), 200)
        self.assertLessEqual(counts.get("en", 0), 50)
        self.assertLessEqual(counts.get("fr", 0), 50)
        self.assertLessEqual(counts.get("es", 0), 200)
        self.assertLessEqual(counts.get("it", 0), 200)
        self.assertLessEqual(counts.get("ja", 0), 6000)
        self.assertLessEqual(counts.get("de", 0), 4000)


if __name__ == "__main__":
    unittest.main()
