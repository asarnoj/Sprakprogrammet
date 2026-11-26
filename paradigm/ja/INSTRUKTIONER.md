# Böjningsinstruktioner — japanska (ja)

> Injiceras i LLM-prompten av `ordbok generera`: sektionen **Allmänt** plus
> sektionen för aktuell ordklass.

## Allmänt

- Skriv formerna i normal japansk ortografi: kanji + okurigana precis som
  lemmat (話す → 話して — byt aldrig kanji mot kana eller tvärtom).
- する-sammansättningar (勉強する, 旅行する, 結婚する): böj する-delen
  (勉強して, 勉強した, 勉強しない …) med substantivdelen oförändrad.
- Suffixlemman och bundna konstruktioner (たい, なければならない, てもいい):
  dessa böjs inte här — alla celler utom grundformen = "".
- Lämna "" endast när formen inte existerar.

## Verb

10 celler: jisho (辞書形), masu (ます形), te (て形), ta (た形), nai (ない形),
vol (意志形), imp (命令形), pot (可能形), kond (ば-form), ukemi (受身形,
diates=Passiv).

- **Bestäm verbtyp först:**
  - Godan (五段): 話す, 書く, 飲む, 買う, 待つ, 死ぬ, 遊ぶ, 泳ぐ, 帰る (obs:
    vissa -eru/-iru är godan: 帰る, 入る, 走る, 知る, 切る)
  - Ichidan (一段): 食べる, 見る, 起きる, 寝る, 開ける
  - Oregelbundna: する (します/して/した/しない/しよう/しろ/できる/すれば/される),
    来る (きます/きて/きた/こない/こよう/こい/こられる/くれば/こられる)
- **て/た-form för godan** (samma ljudväxling båda): -う/-つ/-る → って/った
  (買って, 待って, 帰って); -む/-ぬ/-ぶ → んで/んだ (飲んで, 死んで, 遊んで);
  -く → いて (書いて) MEN 行く → 行って; -ぐ → いで (泳いで); -す → して
  (話して). Ichidan: stryk る, + て/た (食べて, 食べた).
- **nai:** godan a-rad + ない (話さない; 買う → 買わない — w-serien!);
  ichidan 食べない; ある → ない (suppletivt).
- **masu:** godan i-rad + ます (話します); ichidan 食べます.
- **vol:** godan o-rad + う (話そう); ichidan よう (食べよう).
- **imp:** godan e-rad (話せ); ichidan ろ (食べろ). Sällsynt i tal — fyll
  i ändå.
- **pot:** godan e-rad + る (話せる); ichidan られる (食べられる — INTE
  ら-struket れる); する → できる.
- **kond (ば):** e-rad + ば (話せば, 食べれば, あれば).
- **ukemi:** godan a-rad + れる (話される); ichidan られる (食べられる —
  identisk med pot för ichidan: fyll båda cellerna med samma form).
- **Defekta/särskilda:** ある: nai=ない, imp/vol/pot/ukemi = "".
  いる (existera, animat): imp/ukemi = "". できる: pot = "" (är redan
  potentialis), ukemi = "".

## Adjektiv

5 celler: jisho, ta, nai, ku, kereba. Lexemen är typmärkta i databasen
(`ja_adjektiv_typ`); pipelinen skickar bara typ **i** och **na**.

- **i-adjektiv:** jisho=安い, ta=安かった, nai=安くない, ku=安く (adverbial),
  kereba=安ければ. いい böjs på 良: jisho=いい, ta=良かった, nai=良くない,
  ku=良く, kereba=良ければ. かっこいい likadant (かっこ良かった).
- **na-adjektiv** (きれい, 簡単, 健康 …): jisho=lemmat oförändrat,
  ta=〜だった (簡単だった), nai=〜ではない (簡単ではない), ku=〜に
  (adverbial: 簡単に), kereba=〜なら (簡単なら).

## Substantiv

1 cell: jisho = lemmat oförändrat (japanska substantiv böjs inte; numerus
och kasus uttrycks med partiklar av renderaren).

## Pronomen

1 cell: jisho = lemmat oförändrat (私, 君, 彼 …; kasus via partiklar).

## Frågepronomen

1 cell: jisho = lemmat oförändrat (誰, 何, どこ …).
