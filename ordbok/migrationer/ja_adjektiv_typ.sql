/* ── ja_adjektiv_typ — typklassificering av japanska adjektivlexem ──────────
   Bakgrund: GRANSKNING_LEXEM_2026-07-09.md §C4. Japanska "adjektiv" i basen
   är fyra grammatiskt olika typer; böjningspipelinen får bara köra
   ja/adjektiv.yaml-paradigmet på typ 'i' (och 'na' för analytiska celler).

   KÖRS EFTER VARJE `ordbok import` (importen bygger om databasen från CSV
   och tappar taggningen):

       sqlite3 sprak.db < ordbok/migrationer/ja_adjektiv_typ.sql

   Klassificeringen matchar på lemma — typen är en egenskap hos ordet
   självt, så samma lemma i flera koncept (高い, 面白い, 普通) får samma typ.

   Gränsfall, medvetna val:
     予想外  → na  (予想外な är etablerat)
     人気    → no  (人気な är substandard; 人気の/人気がある)
     公式/公共/無料 → no (attribueras normalt med の)
     空っぽ/いっぱい → no (substantiviska)
     いい    → i   (suppletiv böjning på 良: よくない/よかった — hanteras
                    av LLM vid generering, inte här)
   ─────────────────────────────────────────────────────────────────────────── */

-- i-adjektiv: böjs syntetiskt (〜くない, 〜かった)
UPDATE Lexem SET ja_adjektiv_typ = 'i'
WHERE språk = 'ja'
  AND koncept_id IN (SELECT id FROM Koncept WHERE ordklass = 'Adjektiv')
  AND lemma IN (
    'いい', 'つまらない', '丸い', '冷たい', '危ない', '古い', '大きい', '太い',
    '嬉しい', '安い', '寂しい', '小さい', '広い', '弱い', '強い', '怖い',
    '恥ずかしい', '悪い', '悲しい', '新しい', '暖かい', '柔らかい', '正しい',
    '汚い', '涼しい', '深い', '熱い', '白い', '短い', '硬い', '細い', '美しい',
    '若い', '茶色い', '薄い', '誇らしい', '賢い', '赤い', '軽い', '速い',
    '遅い', '醜い', '重い', '鋭い', '長い', '難しい', '青い', '面白い',
    '高い', '黄色い', '黒い', '優しい'
  );

-- na-adjektiv: attribueras med な, prediceras med だ/です
UPDATE Lexem SET ja_adjektiv_typ = 'na'
WHERE språk = 'ja'
  AND koncept_id IN (SELECT id FROM Koncept WHERE ordklass = 'Adjektiv')
  AND lemma IN (
    'きれい', 'ばか', 'プライベート', '不可能', '健康', '勇敢', '勤勉',
    '大切', '好奇心旺盛', '安全', '必要', '怠惰', '意地悪', '普通', '正直',
    '特別', '穏やか', '簡単', '可能', '予想外'
  );

-- no-typ: substantiviska, attribueras med の
UPDATE Lexem SET ja_adjektiv_typ = 'no'
WHERE språk = 'ja'
  AND koncept_id IN (SELECT id FROM Koncept WHERE ordklass = 'Adjektiv')
  AND lemma IN (
    'いっぱい', 'オレンジ', 'ピンク', '人気', '半分', '全体', '公共', '公式',
    '灰色', '無料', '病気', '空っぽ', '紫', '緑'
  );

-- verbfras: verbformer/fraser — böjs som verb eller inte alls;
-- hoppas över av adjektiv-böjningspipelinen
UPDATE Lexem SET ja_adjektiv_typ = 'verbfras'
WHERE språk = 'ja'
  AND koncept_id IN (SELECT id FROM Koncept WHERE ordklass = 'Adjektiv')
  AND lemma IN (
    'お腹が空いた', 'がっかりした', 'ストレスを感じた', '似ている', '乾いた',
    '壊れた', '喉が渇いた', '怒った', '恋している', '死んでいる', '満足した',
    '準備できた', '濡れた', '生きている', '疲れた', '緊張した', '興味ある',
    '違う', '閉まっている', '開いている', '間違った', '驚いた'
  );

-- Kontroll: ska ge 0 rader. Icke-tomt resultat = otaggade ja-adjektiv.
SELECT 'OTAGGAD: ' || l.lemma
FROM Lexem l
JOIN Koncept k ON k.id = l.koncept_id
WHERE l.språk = 'ja' AND k.ordklass = 'Adjektiv' AND l.ja_adjektiv_typ IS NULL;
