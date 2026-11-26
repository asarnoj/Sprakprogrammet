/* ════════════════════════════════════════════════════════════════════════════
   Språkprogrammet — databasschema
   Version: 1
   Skapad:  2026-04-11
   Källa:   docs/BITMASK.md  (auktoritativ specifikation för alla numeriska koder)

   Språk som stöds: sv · en · fr · de · es · it · ja
   Filosofi: Former-tabellen är ett universellt grammatikrum. Varje språks
   renderer frågar bara de dimensioner det språket använder — övriga är NULL.
   ════════════════════════════════════════════════════════════════════════════ */

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

BEGIN;


/* ── Koncept ──────────────────────────────────────────────────────────────────
   Språkoberoende begrepp. En rad = en semantisk enhet.

   nyckel    : CSV-nyckel, t.ex. 'gen_skydda', 'fam_mamma', 'färg_röd'
               Stabil identifierare — ändras aldrig efter import.
   ordklass  : grammatisk kategori (se CHECK-lista)
   källa     : ursprung för konceptet — driver runtime-logik kring vilka
               ord som visas och vem som får ändra. Inga CHECK-värden ännu;
               formatet för community/användarbidrag är inte beslutat.
               Aktuella värden: 'bas_kärna', 'grundord', 'manuell'.

   valens    : bitmask — se BITMASK.md §8
               1=Intransitiv  2=Transitiv  4=Ditransitiv  8=Reflexiv  16=Kopula
   personlighet : bitmask — se BITMASK.md §9
               1=Personlig  2=Opersonlig
   gradbarhet : adjektiv — 'Gradbar' / 'Icke gradbar'
   person    : pronomen — grammatisk person  1=Första  2=Andra  3=Tredje
   numerus   : pronomen — grammatiskt numerus  1=Singular  2=Plural
   räknebar  : substantiv — 1=räknebar (default)  0=oräknebar/masssubstantiv
   semantik  : bitmask — se BITMASK.md §11
               1=Animat  2=Konkret  4=Abstrakt  8=Ätbar  16=Plats  32=Mänsklig
               64=Rörelse  128=Riktning  256=Händelse  512=Tid
               1024=Instrument  2048=Kommunikat
   ─────────────────────────────────────────────────────────────────────────── */
CREATE TABLE Koncept (
    id           INTEGER PRIMARY KEY,
    nyckel       TEXT    NOT NULL UNIQUE,
    ordklass     TEXT    NOT NULL CHECK (ordklass IN (
                     'Substantiv',
                     'Verb',
                     'Adjektiv',
                     'Adverb',
                     'Pronomen',
                     'Preposition',
                     'Konjunktion',
                     'Subjunktion',
                     'Interjektion',
                     'Räkneord',
                     'Frågepronomen',
                     'Frågadverb',
                     'Interrogativdeterminant',
                     'Negationsadverb',
                     'Demonstrativ',
                     'Relativpronomen',
                     'Artikel',
                     'Kvantifikator'
                 )),
    källa        TEXT    NOT NULL,
    valens       INTEGER,
    personlighet INTEGER,
    gradbarhet   TEXT    CHECK (gradbarhet IN ('Gradbar', 'Icke gradbar')),
    person       INTEGER CHECK (person  IN (1, 2, 3)),
    numerus      INTEGER CHECK (numerus IN (1, 2)),
    räknebar     INTEGER CHECK (räknebar IN (0, 1)),
    semantik     INTEGER
);

CREATE INDEX idx_koncept_ordklass ON Koncept(ordklass);
CREATE INDEX idx_koncept_källa    ON Koncept(källa);


/* ── Lexem ────────────────────────────────────────────────────────────────────
   Ett lexem per språk per koncept. Innehåller språkspecifika egenskaper.

   språk      : se CHECK — alla 7 målspråk
   lemma      : uppslagsform per KONVENTIONER.md
                verb=infinitiv, substantiv=nom.sg, adjektiv=mask.pos.sg / m.sg
   genus      : språkspecifik genuskod — se BITMASK.md §5
                sv: 1=Utrum  2=Neutrum
                fr/es/it: 1=Maskulin  2=Feminin
                de: 1=Maskulin  2=Feminin  3=Neutrum
                en/ja: NULL (genus saknas)
   prenominal : adjektiv — 1=före substantiv (default/NULL)  0=efter substantiv
   ─────────────────────────────────────────────────────────────────────────── */
CREATE TABLE Lexem (
    id          INTEGER PRIMARY KEY,
    koncept_id  INTEGER NOT NULL REFERENCES Koncept(id) ON DELETE CASCADE,
    språk       TEXT    NOT NULL CHECK (språk IN ('sv', 'en', 'fr', 'de', 'es', 'it', 'ja')),
    lemma       TEXT    NOT NULL,
    genus       INTEGER,
    prenominal  INTEGER CHECK (prenominal IN (0, 1))
    /* Ingen UNIQUE på (koncept_id, språk): ett koncept kan ha flera
       lemman per språk när språket har genuint distinkta former för
       samma begrepp (t.ex. ja: 私/僕, es: ser/estar, de: dann/damals).
       Renderaren väljer rätt variant utifrån kontext. */
);

CREATE INDEX idx_lexem_koncept ON Lexem(koncept_id);
CREATE INDEX idx_lexem_sprak   ON Lexem(språk);
CREATE INDEX idx_lexem_lemma   ON Lexem(lemma);


/* ── Former ───────────────────────────────────────────────────────────────────
   En rad = en böjd form kopplad till ett språkspecifikt lexem.
   Morfologiska axlar sätts bara när de är relevanta för formen och språket.
   Alla kombinationer av axlar som ger samma skrivna form samlas i en rad
   via bitmask-OR (se BITMASK.md för detaljer).

   numerus  : 1=Singular  2=Plural                          — se §2
   species  : 1=Obestämd  2=Bestämd  3=Blandad (de)         — se §3
   kasus    : bitflagga: 1=Nom  2=Ack  4=Dat  8=Gen          — se §4
   genus    : 1=Utrum/Mask  2=Neutrum/Fem  3=Neutr(de)/Alla  — se §5
   tempus   : bitflagga — se §1 (bitar 1–2048, inkl. japanska former)
   grad     : 1=Positiv  2=Komparativ  3=Superlativ          — se §6
   person   : 1=Första  2=Andra  3=Tredje                    — se §7
   diates   : 1=Aktiv  2=Passiv                              — se §7.5
              Synthetisk passiv (sv -s, ja -(r)areru). Deponensverb
              (hoppas, finnas) lagras med diates=Passiv och markeras
              separat på lexem-nivå. Analytiska språk har diates=NULL.
   ─────────────────────────────────────────────────────────────────────────── */
CREATE TABLE Former (
    id       INTEGER PRIMARY KEY,
    lexem_id INTEGER NOT NULL REFERENCES Lexem(id) ON DELETE CASCADE,
    form     TEXT    NOT NULL,
    numerus  INTEGER,
    species  INTEGER,
    kasus    INTEGER,
    genus    INTEGER,
    tempus   INTEGER,
    grad     INTEGER CHECK (grad IN (1, 2, 3)),
    person   INTEGER CHECK (person IN (1, 2, 3)),
    diates   INTEGER CHECK (diates IN (1, 2))
);

/* Sammansatta index optimerade för de vanligaste renderar-frågorna. */
CREATE INDEX idx_former_subst  ON Former(lexem_id, numerus, species, kasus);
CREATE INDEX idx_former_verb   ON Former(lexem_id, tempus,  person,  numerus);
CREATE INDEX idx_former_adj    ON Former(lexem_id, grad,    genus,   numerus, species);


/* ── Mönster ──────────────────────────────────────────────────────────────────
   Ett semantiskt användningsmönster kopplat till ett styrande ord
   (typiskt verb, men kan vara adjektiv eller preposition).

   språk = NULL  →  mönstret gäller alla språk
   språk = 'sv'  →  språkspecifikt mönster (t.ex. partikelverb)
   ─────────────────────────────────────────────────────────────────────────── */
CREATE TABLE Mönster (
    id         INTEGER PRIMARY KEY,
    koncept_id INTEGER NOT NULL REFERENCES Koncept(id) ON DELETE CASCADE,
    språk      TEXT    CHECK (språk IN ('sv', 'en', 'fr', 'de', 'es', 'it', 'ja'))
);

CREATE INDEX idx_monster_koncept ON Mönster(koncept_id);


/* ── MönsterKrav ──────────────────────────────────────────────────────────────
   Varje rad = ett krav på en slot i ett mönster.

   slot       : grammatisk position
                'subjekt' | 'objekt' | 'io' | 'predikativ' | 'komplement'
                | 'adverbial' | 'preposition' | 'kommunikat'
   tagg       : semantisk bitmask mot Koncept.semantik  (NULL = inget semantiskt krav)
   koncept_id : krav på exakt detta koncept             (NULL = semantiskt krav)
   frastyp    : vilken syntaktisk fras som accepteras — se BITMASK.md §10
                1=Nominalfras  2=Adjektivfras  4=Prepositionsfras
                8=Adverbfras  16=Infinitivfras  32=Bisatsfras

   Regel: exakt en av (tagg, koncept_id) ska vara satt per rad.
   ─────────────────────────────────────────────────────────────────────────── */
CREATE TABLE MönsterKrav (
    id         INTEGER PRIMARY KEY,
    mönster_id INTEGER NOT NULL REFERENCES Mönster(id)  ON DELETE CASCADE,
    koncept_id INTEGER         REFERENCES Koncept(id)   ON DELETE CASCADE,
    slot       TEXT    NOT NULL CHECK (slot IN (
                   'subjekt', 'objekt', 'io', 'predikativ',
                   'komplement', 'adverbial', 'preposition', 'kommunikat'
               )),
    tagg       INTEGER,
    frastyp    INTEGER,
    CHECK ((tagg IS NOT NULL) != (koncept_id IS NOT NULL))   -- exakt en av de två
);

CREATE INDEX idx_monsterkrav_monster ON MönsterKrav(mönster_id);


PRAGMA user_version = 1;

COMMIT;
