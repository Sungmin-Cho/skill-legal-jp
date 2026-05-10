#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path


DEFAULT_REPO = os.environ.get(
    "LEGAL_JP_DATA_SET_PATH", str(Path(__file__).resolve().parents[4] / "data_set")
)


def load_json(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def stream_json_array(path):
    if not path.exists():
        return

    decoder = json.JSONDecoder()
    buffer = ""
    in_array = False
    with path.open("r", encoding="utf-8") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk and not buffer:
                break
            buffer += chunk

            while True:
                stripped = buffer.lstrip()
                if stripped != buffer:
                    buffer = stripped
                if not buffer:
                    break
                if not in_array:
                    if buffer[0] != "[":
                        raise ValueError(f"{path} is not a JSON array")
                    buffer = buffer[1:]
                    in_array = True
                    continue
                buffer = buffer.lstrip()
                if not buffer:
                    break
                if buffer[0] == "]":
                    return
                if buffer[0] == ",":
                    buffer = buffer[1:]
                    continue
                try:
                    item, idx = decoder.raw_decode(buffer)
                except json.JSONDecodeError:
                    if not chunk:
                        raise
                    break
                yield item
                buffer = buffer[idx:]
            if not chunk:
                break


def iter_json_records(path):
    if path.name == "ryakusyou.json":
        for item in stream_json_array(path):
            yield item if isinstance(item, dict) else {"raw": item}
        return

    data = load_json(path)
    if isinstance(data, list):
        for item in data:
            yield item if isinstance(item, dict) else {"raw": item}
    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                children = value
            else:
                children = [value]
            for child in children:
                if isinstance(child, dict):
                    item = dict(child)
                else:
                    item = {"raw": child}
                item["container_key"] = key
                yield item


def append_limited(results, result, limit):
    if limit <= 0:
        return False
    if len(results) >= limit:
        return False
    results.append(result)
    return len(results) < limit


def normalized(value):
    return "".join(str(value or "").casefold().split())


def json_contains(entry, query):
    haystack = json.dumps(entry, ensure_ascii=False, sort_keys=True).casefold()
    return str(query).casefold() in haystack


def law_name(entry):
    return (
        entry.get("name")
        or entry.get("law_name")
        or entry.get("formal")
        or entry.get("title")
    )


def law_entry(entry, source_file, status, matches=None):
    name = law_name(entry)
    return {
        "name": name,
        "num": entry.get("num") or entry.get("container_key"),
        "id": entry.get("id"),
        "date": entry.get("date"),
        "source_file": source_file,
        "status": status,
        "patch": entry.get("patch"),
        "matches": matches or [],
        "container_key": entry.get("container_key"),
        "abbs": entry.get("abbs"),
        "ryakusyou_lst": entry.get("ryakusyou_lst"),
        "data": entry.get("data"),
        "article": entry.get("article"),
        "chapter": entry.get("chapter"),
        "raw": entry,
    }


def search_law_names(repo, query, include_repealed=False, exact=False, limit=20):
    sources = [("law/list.json", "active")]
    if include_repealed:
        sources.append(("law/repeal_list.json", "repealed"))

    limit = max(limit, 0)
    query_norm = normalized(query)
    results = []
    for source_file, status in sources:
        remaining = limit - len(results)
        if remaining <= 0:
            break
        exact_matches = []
        partial_matches = []
        for entry in iter_json_records(repo / source_file):
            name = law_name(entry)
            name_norm = normalized(name)
            if name_norm == query_norm:
                if len(exact_matches) < remaining:
                    exact_matches.append(law_entry(entry, source_file, status, ["name:exact"]))
            elif (
                not exact
                and query_norm in name_norm
                and len(partial_matches) < remaining
            ):
                partial_matches.append(law_entry(entry, source_file, status, ["name:partial"]))
        results.extend(exact_matches)
        remaining = limit - len(results)
        if remaining > 0:
            results.extend(partial_matches[:remaining])
    return results


def search_json_sources(repo, query, source_files, status="metadata", limit=20):
    limit = max(limit, 0)
    results = []
    if limit == 0:
        return results
    for source_file in source_files:
        for entry in iter_json_records(repo / source_file):
            if json_contains(entry, query):
                should_continue = append_limited(
                    results,
                    law_entry(entry, source_file, status, ["json:contains"]),
                    limit,
                )
                if not should_continue:
                    return results
    return results


def build_parser():
    parser = argparse.ArgumentParser(description="Search legal-jp law metadata")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--name")
    group.add_argument("--exact")
    group.add_argument("--abbr")
    group.add_argument("--yomikae")
    parser.add_argument("--include-repealed", action="store_true")
    parser.add_argument("--limit", type=int, default=20)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    repo = Path(args.repo)
    if not (repo / "law").is_dir():
        print(f"error: law directory not found: {repo / 'law'}", file=sys.stderr)
        print("[]")
        return

    if args.name is not None:
        results = search_law_names(
            repo, args.name, args.include_repealed, exact=False, limit=args.limit
        )
    elif args.exact is not None:
        results = search_law_names(
            repo, args.exact, args.include_repealed, exact=True, limit=args.limit
        )
    elif args.abbr is not None:
        results = search_json_sources(
            repo,
            args.abbr,
            ["law/egov_abb.json", "law/law_abb.json", "law/ryakusyou.json"],
            limit=args.limit,
        )
    else:
        results = search_json_sources(repo, args.yomikae, ["law/yomikae.json"], limit=args.limit)

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
