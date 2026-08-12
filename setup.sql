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
                     'Possessiv',
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
    semantik     INTEGER,
    /* attributkrav : ENDAST Adjektiv. Bitmask som HUVUDORDET måste uppfylla
       för att adjektivet ska få beskriva det. "glad" kräver ANIMAT, "röd"
       kräver KONKRET, "dyr" kräver ÖVERLÅTBAR, "öppen" kräver ÖPPNINGSBAR.
       NULL = adjektivet kan beskriva vad som helst (bra, ny, viktig).

       Ligger som kolumn och INTE i MönsterKrav, trots att det ser ut som
       samma sak. MönsterKrav beskriver argument ett ord STYR — de platser
       verbet öppnar. Det här är motsatt riktning: en begränsning av vad
       adjektivet får fästa på. Att trycka in det i MönsterKrav.slot hade
       krävt en attribut-roll som inte betyder samma sak som de andra åtta.
       Se paradigm/RESTRIKTIONER.md. */
    attributkrav INTEGER,
    /* tempuskrav : ENDAST Adverb. Vilka TIDSREFERENSER adverbet får stå i.
       Bitarna är tempus-bitarna ur _legend.yaml: Pres=2, Pret=4, Fut=64.
       NULL = adverbet passar alla tempus.

       OBS att matchningsregeln är en ANNAN än för semantik. `semantik` mot
       `tagg` är OCH — konceptet måste ha ALLA krävda egenskaper. Här är det
       medlemskap: meningens tidsreferens måste finnas BLAND de tillåtna.
       Samma bitmaskmekanism, två olika frågor. */
    tempuskrav   INTEGER
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
   ja_adjektiv_typ : ENDAST ja + ordklass Adjektiv. Japanska "adjektiv" är
                fyra grammatiskt olika typer med olika böjning/attribuering:
                  'i'        — i-adjektiv, böjs syntetiskt (安い → 安くない)
                  'na'       — na-adjektiv, attribueras med な (簡単な)
                  'no'       — substantiviskt, attribueras med の (灰色の)
                  'verbfras' — verbform/fras (疲れた, 開いている); böjs som
                               verb eller inte alls — hoppas över av
                               adjektiv-böjningspipelinen
                Taggas av ordbok/migrationer/ja_adjektiv_typ.sql efter import.
   hjälpverb  : ENDAST fr/de/it + ordklass Verb. Vilket hjälpverb som bildar
                sammansatt dåtid. Lagras ABSTRAKT, inte som lemma, eftersom
                valet är samma distinktion i alla tre språken och renderaren
                ändå slår upp hjälpverbets egna former:
                  'ha'   — de haben, fr avoir, it avere (majoriteten)
                  'vara' — de sein, fr être, it essere (rörelse, tillstånds-
                           förändring; alla franska och italienska reflexiver)
                  'båda' — verbet tar båda med olika betydelse, t.ex.
                           de "ist gefahren" (åkte) vs "hat gefahren" (körde),
                           it "è corso" vs "ha corso". Renderaren måste välja
                           på transitivitet, inte på lexemet.
                Taggas av ordbok/migrationer/hjälpverb.sql efter import.
   variant    : diskriminator när ETT koncept har FLERA lemman i samma språk.
                Utan den går de inte att skilja åt: poss_3sg_fem har både
                sv "hans" och sv "sin", och ingenting säger vilken som är den
                reflexiva. Värdet är en kort etikett vars betydelse är
                gemensam över språken där den används — se
                ordbok/migrationer/variant.sql för de använda etiketterna.
   ─────────────────────────────────────────────────────────────────────────── */
CREATE TABLE Lexem (
    id          INTEGER PRIMARY KEY,
    koncept_id  INTEGER NOT NULL REFERENCES Koncept(id) ON DELETE CASCADE,
    språk       TEXT    NOT NULL CHECK (språk IN ('sv', 'en', 'fr', 'de', 'es', 'it', 'ja')),
    lemma       TEXT    NOT NULL,
    genus       INTEGER,
    prenominal  INTEGER CHECK (prenominal IN (0, 1)),
    ja_adjektiv_typ TEXT CHECK (ja_adjektiv_typ IN ('i', 'na', 'no', 'verbfras')),
    hjälpverb   TEXT    CHECK (hjälpverb IN ('ha', 'vara', 'båda')),
    variant     TEXT
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

   kasus      : kasus som det styrande ordet kräver av slotten — bitmask
                enligt BITMASK.md §4 (1=Nom 2=Ack 4=Dat 8=Gen).
                Endast meningsfullt på språkspecifika mönster (Mönster.språk
                satt): de "helfen" + Dativ, "in" + Ack vid rörelse / Dat vid
                befintlighet. NULL på universella mönster och i språk utan
                kasus.
   preposition_koncept_id
              : preposition som realiserar slotten i det här språket.
                fr/es indirekt objekt kräver à/a → prep_till. NULL när
                slotten realiseras utan preposition.
                Också endast meningsfullt på språkspecifika mönster.

   Regel: HÖGST en av (tagg, koncept_id) per rad. Båda NULL är tillåtet och
   betyder "slotten krävs, men utan innehållsbegränsning" — nödvändigt för
   verb vars subjekt kan vara vad som helst (regna, kosta, finnas). Tidigare
   krävde villkoret exakt en av de två, vilket gjorde att sådana slots inte
   gick att uttrycka alls och därmed föll bort ur mönstret (rättat 2026-08-10,
   innan mönstertaggningen kördes).

   Kasus- och prepositionskolumnerna tillkom 2026-08-10 efter den vertikala
   skivan (paradigm/RENDERARE_KRAV.md §3.5, §3.8) — de lades till medan
   tabellen ännu var tom, så att mönstertaggningen inte behöver göras om.
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
    kasus      INTEGER,
    preposition_koncept_id INTEGER REFERENCES Koncept(id) ON DELETE SET NULL,
    CHECK (NOT (tagg IS NOT NULL AND koncept_id IS NOT NULL))  -- högst en av de två
);

CREATE INDEX idx_monsterkrav_monster ON MönsterKrav(mönster_id);


PRAGMA user_version = 1;

COMMIT;
