import gzip
import json

TARGETS = {
    "/c/en/drink/v",
    "/c/en/sleep/v",
    "/c/en/run/v",
    "/c/en/walk/v",
    "/c/en/jump/v",
    "/c/en/play/v",
    "/c/en/work/v",
    "/c/en/rest/v",
    "/c/en/talk/v",
    "/c/en/listen/v",
    "/c/en/read/v",
    "/c/en/write/v",
    "/c/en/think/v",
    "/c/en/learn/v",
    "/c/en/teach/v",
    "/c/en/build/v",
    "/c/en/break/v",
    "/c/en/open/v",
    "/c/en/close/v",
    "/c/en/start/v",
    "/c/en/stop/v",
    "/c/en/move/v",
    "/c/en/turn/v",
    "/c/en/drive/v",
    "/c/en/fly/v",
    "/c/en/swim/v",
    "/c/en/cook/v",
    "/c/en/bake/v",
    "/c/en/wash/v",
    "/c/en/clean/v",
    "/c/en/cut/v",
    "/c/en/draw/v",
    "/c/en/paint/v",
    "/c/en/watch/v",
    "/c/en/call/v",
    "/c/en/answer/v",
    "/c/en/change/v",
    "/c/en/light/n",
    "/c/en/sound/n",
    "/c/en/water/n",
    "/c/en/fire/n",
    "/c/en/love/n",
    "/c/en/hate/n",
    "/c/en/hope/n",
    "/c/en/fear/n",
    "/c/en/mind/n",
    "/c/en/face/n",
    "/c/en/hand/n",
    "/c/en/back/n",
    "/c/en/right/n",
}

LANGUAGES = {"sv", "de", "fr", "ja"}
CONCEPTNET_PATH = "ordbok/conceptnet-assertions-5.7.0.csv.gz"
OUTPUT_VALIDATED = "ordbok/mina_ord.json"
OUTPUT_FLAGGED = "ordbok/mina_ord_flagged.json"


def get_base_uri(uri):
    parts = uri.split("/")
    return "/".join(parts[:4]) if len(parts) >= 4 else uri


def get_uri_pos(uri):
    parts = uri.split("/")
    for part in reversed(parts[4:]):
        if part in {"n", "v", "a", "r"}:
            return part
    return None


def build_lookup(targets):
    lookup = {}
    for target_uri in targets:
        lookup.setdefault(get_base_uri(target_uri), set()).add(target_uri)
    return lookup


def resolve_target_candidates(node_uri, lookup):
    if node_uri in TARGETS:
        return [node_uri]

    candidates = list(lookup.get(get_base_uri(node_uri), []))
    if not candidates:
        return []

    node_pos = get_uri_pos(node_uri)
    if not node_pos:
        return candidates

    filtered = [target_uri for target_uri in candidates if target_uri.split("/")[-1] == node_pos]
    return filtered if filtered else candidates


def init_nested_targets(targets, languages):
    return {target_uri: {lang: [] for lang in languages} for target_uri in targets}


def collect_raw_data():
    pos_map = {lang: {} for lang in LANGUAGES}  # pos_map['sv']['dryck'] = {'n'}
    raw_results = init_nested_targets(TARGETS, LANGUAGES)
    lookup = build_lookup(TARGETS)

    print("Steg 1: Bygger ordklass-facit och letar synonymer...")

    with gzip.open(CONCEPTNET_PATH, "rt", encoding="utf-8") as file:
        for count, line in enumerate(file):
            if count % 1_000_000 == 0:
                print(f"Rad {count}...")

            parts = line.split()
            if len(parts) < 4:
                continue

            rel = parts[1]
            p2, p3 = parts[2], parts[3]

            if rel == "/r/PartOfSpeech":
                node_parts = p2.split("/")
                if len(node_parts) > 3 and node_parts[2] in LANGUAGES:
                    lang = node_parts[2]
                    word = node_parts[3].replace("_", " ")
                    pos = p3.split("/")[-1]
                    pos_map[lang].setdefault(word, set()).add(pos)
                continue

            if rel != "/r/Synonym":
                continue

            for source_node, other_node in ((p2, p3), (p3, p2)):
                candidate_targets = resolve_target_candidates(source_node, lookup)
                if not candidate_targets:
                    continue

                other_parts = other_node.split("/")
                if len(other_parts) <= 3 or other_parts[2] not in LANGUAGES:
                    continue

                lang = other_parts[2]
                word_label = other_parts[3].replace("_", " ")
                source_pos = get_uri_pos(source_node)

                for match_target in candidate_targets:
                    raw_results[match_target][lang].append(
                        {
                            "word": word_label,
                            "uri": other_node,
                            "source_pos": source_pos,
                        }
                    )

    return pos_map, raw_results


def classify_candidate(target_pos, target_evidence, source_evidence):
    if target_evidence:
        has_match = target_pos in target_evidence
        has_contradiction = any(pos != target_pos for pos in target_evidence)
        scope = "target"
    elif source_evidence:
        has_match = target_pos in source_evidence
        has_contradiction = False if has_match else any(pos != target_pos for pos in source_evidence)
        scope = "source"
    else:
        has_match = False
        has_contradiction = False
        scope = "none"

    if has_match and not has_contradiction:
        return "validated"
    if has_match and has_contradiction and scope == "target":
        return "mixed_conflict"
    if has_contradiction:
        return "contradiction_only"
    return "unknown"


def aggregate_candidates(words, lang, pos_map):
    aggregated = {}
    for item in words:
        word = item["word"]
        source_pos = item.get("source_pos")
        target_uri_pos = get_uri_pos(item["uri"])
        lexicon_pos_set = pos_map[lang].get(word, set())

        if word not in aggregated:
            aggregated[word] = {
                "word": word,
                "source_pos_set": set(),
                "target_uri_pos_set": set(),
                "lexicon_pos_set": set(),
            }

        if source_pos:
            aggregated[word]["source_pos_set"].add(source_pos)
        if target_uri_pos:
            aggregated[word]["target_uri_pos_set"].add(target_uri_pos)
        aggregated[word]["lexicon_pos_set"].update(lexicon_pos_set)

    return aggregated


def filter_candidates(pos_map, raw_results):
    print("Steg 2: Filtrerar bort felaktiga ordklasser...")

    final_results = init_nested_targets(TARGETS, LANGUAGES)
    flagged_results = init_nested_targets(TARGETS, LANGUAGES)

    for target_uri, langs in raw_results.items():
        target_pos = target_uri.split("/")[-1]

        for lang, words in langs.items():
            aggregated = aggregate_candidates(words, lang, pos_map)
            candidates = []

            for word, data in aggregated.items():
                target_evidence = set(data["target_uri_pos_set"]) | set(data["lexicon_pos_set"])
                source_evidence = set(data["source_pos_set"])
                status = classify_candidate(target_pos, target_evidence, source_evidence)

                candidates.append(
                    {
                        "word": word,
                        "status": status,
                        "source_pos": sorted(data["source_pos_set"]),
                        "target_uri_pos": sorted(data["target_uri_pos_set"]),
                        "lexicon_pos": sorted(data["lexicon_pos_set"]),
                    }
                )

            validated = [c for c in candidates if c["status"] == "validated"]
            mixed = [c for c in candidates if c["status"] == "mixed_conflict"]
            non_contradict = [c for c in candidates if c["status"] in {"unknown", "mixed_conflict"}]

            if validated:
                for candidate in validated:
                    final_results[target_uri][lang].append(
                        {
                            "word": candidate["word"],
                            "pos": target_pos,
                        }
                    )
            else:
                if len(non_contradict) == 1 and non_contradict[0]["status"] == "unknown":
                    final_results[target_uri][lang].append(
                        {
                            "word": non_contradict[0]["word"],
                            "pos": target_pos,
                        }
                    )
                elif len(non_contradict) > 1 and all(c["status"] == "unknown" for c in non_contradict):
                    for candidate in non_contradict:
                        flagged_results[target_uri][lang].append(
                            {
                                "word": candidate["word"],
                                "target_pos": target_pos,
                                "reason": "unknown_multi_candidate",
                                "source_pos": candidate["source_pos"],
                                "target_uri_pos": candidate["target_uri_pos"],
                                "lexicon_pos": candidate["lexicon_pos"],
                            }
                        )

            for candidate in mixed:
                flagged_results[target_uri][lang].append(
                    {
                        "word": candidate["word"],
                        "target_pos": target_pos,
                        "reason": "mixed_evidence",
                        "source_pos": candidate["source_pos"],
                        "target_uri_pos": candidate["target_uri_pos"],
                        "lexicon_pos": candidate["lexicon_pos"],
                    }
                )

    return final_results, flagged_results


def write_outputs(final_results, flagged_results):
    with open(OUTPUT_VALIDATED, "w", encoding="utf-8") as outfile:
        json.dump(final_results, outfile, ensure_ascii=False, indent=4)

    with open(OUTPUT_FLAGGED, "w", encoding="utf-8") as outfile:
        json.dump(flagged_results, outfile, ensure_ascii=False, indent=4)


def main():
    pos_map, raw_results = collect_raw_data()
    final_results, flagged_results = filter_candidates(pos_map, raw_results)
    write_outputs(final_results, flagged_results)
    print("Klart! Validerade träffar skrevs till mina_ord.json och osäkra till mina_ord_flagged.json.")


if __name__ == "__main__":
    main()
