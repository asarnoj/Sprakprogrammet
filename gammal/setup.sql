PRAGMA foreign_keys=ON;

BEGIN;

/* ── Koncept ──────────────────────────────────────────────────────────────
   Språkoberoende begrepp. Binder ihop samma ord över olika språk.
   namn  = engelsk identifierare (t.ex. "eat", "ball", "he")
   ordklass = grammatisk kategori, används som identifierare i Python-koden
──────────────────────────────────────────────────────────────────────── */
CREATE TABLE IF NOT EXISTS Koncept (
    id       INTEGER PRIMARY KEY,
    namn     TEXT    NOT NULL,
    ordklass TEXT    NOT NULL CHECK (ordklass IN (
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
        'Negationsadverb'
    )),
    valens        INTEGER,   /* bitmask: 1=Intransitiv 2=Transitiv 4=Ditransitiv 8=Reflexiv 16=Kopula */
    personlighet  INTEGER,   /* bitmask: 1=Personlig 2=Opersonlig */
    gradbarhet    TEXT    CHECK (gradbarhet IN ('Gradbar','Icke gradbar')),
    person        INTEGER,   /* pronomen: grammatisk person 1=Första 2=Andra 3=Tredje */
    numerus       INTEGER,   /* pronomen: grammatiskt numerus 1=Singular 2=Plural */
    räknebar      INTEGER    /* 1=räknebar (default/NULL), 0=oräknebar/masssubstantiv */
);

CREATE INDEX IF NOT EXISTS idx_koncept_ordklass ON Koncept(ordklass);


/* ── Lexem ────────────────────────────────────────────────────────────────
   Ett lexem per språk per koncept. Innehåller språkspecifika egenskaper.
   genus = fri text, tolkas i sitt språks kontext
         (sv: Utrum/Neutrum  |  fr: Maskulin/Feminin  |  ...)

   valens       : bitmask  1=Intransitiv, 2=Transitiv, 4=Ditransitiv, 8=Reflexiv
   personlighet : bitmask  1=Personlig, 2=Opersonlig
──────────────────────────────────────────────────────────────────────── */
CREATE TABLE IF NOT EXISTS Lexem (
    id            INTEGER PRIMARY KEY,
    koncept_id    INTEGER NOT NULL,
    språk         TEXT    NOT NULL CHECK (språk IN ('sv', 'fr')),
    lemma         TEXT    NOT NULL,
    genus         INTEGER,   /* språkspecifik genuskod — sv: 1=Utrum 2=Neutrum | fr: 1=Maskulin 2=Feminin | de: 1=Maskulin 2=Feminin 3=Neutrum */
    prenominal    INTEGER,   /* 1=adjektivet placeras före substantivet, 0=efter (NULL tolkas som 1) */
    FOREIGN KEY (koncept_id) REFERENCES Koncept(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_lexem_lemma   ON Lexem(lemma);
CREATE INDEX IF NOT EXISTS idx_lexem_spraak  ON Lexem(språk);
CREATE INDEX IF NOT EXISTS idx_lexem_koncept ON Lexem(koncept_id);


/* ── Former ───────────────────────────────────────────────────────────────
   En rad = en böjd form kopplad till ett språkspecifikt lexem.
   Morfologiska axlar fylls bara när de är relevanta för just den formen.

   numerus : 1=Singular, 2=Plural
   species : 1=Obestämd, 2=Bestämd          (ej tillämplig i t.ex. fr)
   kasus   : bitflagga  1=Nominativ, 2=Ackusativ, 4=Dativ, 8=Genitiv
   genus   : språkspecifik int — sv: 1=Utrum 2=Neutrum | fr: 1=Maskulin 2=Feminin | NULL=alla genus
──────────────────────────────────────────────────────────────────────── */
CREATE TABLE IF NOT EXISTS Former (
    id        INTEGER PRIMARY KEY,
    lexem_id  INTEGER NOT NULL,
    form      TEXT    NOT NULL,
    numerus   INTEGER,
    species   INTEGER,
    kasus     INTEGER,
    genus     INTEGER,
    tempus    INTEGER,   /* bitmask: 1=Infinitiv 2=Presens 4=Preteritum 8=Supinum 16=Imperativ 32=Preteritum perfekt 64=Futurum */
    grad      INTEGER,   /* 1=Positiv 2=Komparativ 3=Superlativ */
    person    INTEGER, /* 1=Första, 2=Andra, 3=Tredje – relevant för språk med personböjning (t.ex. fr) */
    FOREIGN KEY (lexem_id) REFERENCES Lexem(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_former_substantiv ON Former(lexem_id, numerus, species);
CREATE INDEX IF NOT EXISTS idx_former_verb       ON Former(lexem_id, tempus, person, numerus);
CREATE INDEX IF NOT EXISTS idx_former_adjektiv   ON Former(lexem_id, grad, genus, numerus, species);

/* ── Semantik på Koncept ──────────────────────────────────────────────
   Bitmask: 1=Animat 2=Konkret 4=Abstrakt 8=Ätbar 16=Plats 32=Mänsklig
   Flera taggar kombineras med | (t.ex. hund = Animat|Konkret = 3).
   OBS: semantik läggs till via ALTER TABLE för att inte
   ändra existerande INSERT-satser.
──────────────────────────────────────────────────────────────────────── */
ALTER TABLE Koncept ADD COLUMN semantik INTEGER;


/* ── Mönster ─────────────────────────────────────────────────────────
   Ett semantiskt användningsmönster kopplat till ett styrande ord
   (verb, adjektiv, preposition).
   språk = NULL betyder att mönstret gäller alla språk.
──────────────────────────────────────────────────────────────────────── */
CREATE TABLE IF NOT EXISTS Mönster (
    id          INTEGER PRIMARY KEY,
    koncept_id  INTEGER NOT NULL,
    språk       TEXT,
    FOREIGN KEY (koncept_id) REFERENCES Koncept(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_mönster_koncept ON Mönster(koncept_id);


/* ── MönsterKrav ─────────────────────────────────────────────────────
   Varje rad = ett krav inom ett mönster.
   slot   = vilken grammatisk position kravet gäller
            ('subjekt', 'objekt', 'io', 'preposition', 'komplement')
   tagg   = bitmask-krav mot Koncept.semantik  (NULL om lexikalt krav)
   koncept_id = krav på ett specifikt koncept   (NULL om semantiskt krav)
   Exakt en av tagg/koncept_id ska vara satt per rad.
──────────────────────────────────────────────────────────────────────── */
CREATE TABLE IF NOT EXISTS MönsterKrav (
    id          INTEGER PRIMARY KEY,
    mönster_id  INTEGER NOT NULL,
    slot        TEXT    NOT NULL,
    tagg        INTEGER,
    koncept_id  INTEGER,
    frastyp     INTEGER,   /* bitmask: 1=Nominalfras 2=Adjektivfras 4=Prepositionsfras 8=Adverbfras 16=Infinitivfras 32=Bisatsfras */
    FOREIGN KEY (mönster_id) REFERENCES Mönster(id) ON DELETE CASCADE,
    FOREIGN KEY (koncept_id) REFERENCES Koncept(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_mönsterkrav_mönster ON MönsterKrav(mönster_id);


PRAGMA user_version=14;

COMMIT;
