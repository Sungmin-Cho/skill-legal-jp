#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path


DEFAULT_REPO = os.environ.get(
    "LEGAL_JP_DATA_SET_PATH", str(Path(__file__).resolve().parents[4] / "data_set")
)
EXIT_DATA_ERROR = 2


class DataFileError(Exception):
    pass


def load_json(path, required=False):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        if required:
            raise DataFileError(f"error: JSON file not found: {path}") from exc
        return []
    except json.JSONDecodeError as exc:
        raise DataFileError(f"error: invalid JSON in {path}: {exc}") from exc
    except PermissionError as exc:
        raise DataFileError(f"error: unreadable JSON file: {path}: {exc}") from exc


def stream_json_array(path, required=False):
    if not path.exists():
        if required:
            raise DataFileError(f"error: JSON file not found: {path}")
        return

    decoder = json.JSONDecoder()
    buffer = ""
    started = False
    expect_value = True
    seen_value = False
    eof = False
    try:
        handle = path.open("r", encoding="utf-8")
    except PermissionError as exc:
        raise DataFileError(f"error: unreadable JSON file: {path}: {exc}") from exc

    with handle:
        while True:
            if not eof and len(buffer) < 65536:
                chunk = handle.read(65536)
                if chunk:
                    buffer += chunk
                else:
                    eof = True

            buffer = buffer.lstrip()
            if not started:
                if not buffer:
                    if eof:
                        raise DataFileError(f"error: expected top-level JSON array: {path}")
                    continue
                if buffer[0] != "[":
                    raise DataFileError(f"error: expected top-level JSON array: {path}")
                buffer = buffer[1:]
                started = True
                continue

            if not buffer:
                if eof:
                    raise DataFileError(f"error: unterminated JSON array: {path}")
                continue
            if buffer[0] == "]":
                if expect_value and seen_value:
                    raise DataFileError(f"error: trailing comma in JSON array: {path}")
                trailing = buffer[1:]
                if trailing.strip():
                    raise DataFileError(f"error: trailing data after JSON array in {path}")
                while True:
                    chunk = handle.read(65536)
                    if not chunk:
                        return
                    if chunk.strip():
                        raise DataFileError(f"error: trailing data after JSON array in {path}")
            if buffer[0] == ",":
                if expect_value:
                    raise DataFileError(f"error: unexpected comma in JSON array: {path}")
                buffer = buffer[1:]
                expect_value = True
                continue
            if not expect_value:
                raise DataFileError(f"error: expected comma or end of JSON array: {path}")
            try:
                item, idx = decoder.raw_decode(buffer)
            except json.JSONDecodeError as exc:
                if eof:
                    raise DataFileError(f"error: invalid JSON in {path}: {exc}") from exc
                chunk = handle.read(65536)
                if chunk:
                    buffer += chunk
                    continue
                eof = True
                continue
            yield item
            buffer = buffer[idx:]
            expect_value = False
            seen_value = True


def iter_json_records(path, required=False):
    if path.name == "ryakusyou.json":
        for item in stream_json_array(path, required=required):
            yield item if isinstance(item, dict) else {"raw": item}
        return

    data = load_json(path, required=required)
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


def require_nonempty_query(value, label):
    if not normalized(value):
        raise DataFileError(f"error: empty {label} query")
    return value


def json_contains(entry, query):
    haystack = json.dumps(entry, ensure_ascii=False, sort_keys=True).casefold()
    return str(query).casefold() in haystack


def field_values(entry, *keys):
    values = []
    for key in keys:
        value = entry.get(key)
        if value is None:
            continue
        if isinstance(value, list):
            values.extend(item for item in value if item is not None)
        else:
            values.append(value)
    return values


def abbr_values(entry):
    values = field_values(entry, "abbs", "name", "law_name", "formal", "title")
    for item in entry.get("ryakusyou_lst") or []:
        if isinstance(item, dict):
            values.extend(field_values(item, "ryakusyou", "seishiki", "name", "abb"))
    return values


def match_rank(values, query):
    query_norm = normalized(query)
    normalized_values = [normalized(value) for value in values if value is not None]
    if any(value == query_norm for value in normalized_values):
        return "exact"
    if any(query_norm in value for value in normalized_values):
        return "partial"
    return None


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


def law_catalog(repo):
    by_num = {}
    by_name = {}
    for source_file, status, required in (
        ("law/list.json", "active", True),
        ("law/repeal_list.json", "repealed", False),
    ):
        for entry in iter_json_records(repo / source_file, required=required):
            catalog_entry = (entry, source_file, status)
            num = entry.get("num")
            if num is not None:
                by_num.setdefault(str(num), catalog_entry)
            name = law_name(entry)
            if name is not None:
                by_name.setdefault(normalized(name), catalog_entry)
    return by_num, by_name


def entry_with_abbr_source(catalog_entry, source_file, source_entry, match_label):
    law, law_source, status = catalog_entry
    result = law_entry(law, law_source, status, [match_label, f"abbr_source:{source_file}"])
    result["abbr_source_file"] = source_file
    result["abbr_raw"] = source_entry
    return result


def abbr_usage_entry(source_entry, source_file, match_label):
    return {
        "name": None,
        "num": source_entry.get("num") or source_entry.get("container_key"),
        "id": None,
        "date": None,
        "source_file": source_file,
        "status": "abbreviation_usage",
        "patch": None,
        "matches": [match_label, f"abbr_source:{source_file}"],
        "container_key": source_entry.get("container_key"),
        "abbs": source_entry.get("abbs"),
        "ryakusyou_lst": source_entry.get("ryakusyou_lst"),
        "data": None,
        "article": source_entry.get("article"),
        "chapter": source_entry.get("chapter"),
        "raw": source_entry,
        "abbr_source_file": source_file,
        "abbr_raw": source_entry,
    }


def resolve_abbr_entry(entry, source_file, by_num, by_name, match_label):
    num = entry.get("num") or entry.get("container_key")
    if num is not None and str(num) in by_num:
        return entry_with_abbr_source(by_num[str(num)], source_file, entry, match_label)

    for value in field_values(entry, "law_name", "formal", "title"):
        catalog_entry = by_name.get(normalized(value))
        if catalog_entry is not None:
            return entry_with_abbr_source(catalog_entry, source_file, entry, match_label)
    return None


def matching_ryakusyou_targets(entry, query, by_name):
    for item in entry.get("ryakusyou_lst") or []:
        if not isinstance(item, dict):
            continue
        values = field_values(item, "ryakusyou", "abb", "name")
        rank = match_rank(values, query)
        if not rank:
            continue
        formal_name = item.get("seishiki")
        catalog_entry = by_name.get(normalized(formal_name))
        source_entry = dict(entry)
        source_entry["ryakusyou_lst"] = [item]
        yield rank, source_entry, catalog_entry


def search_law_names(repo, query, include_repealed=False, exact=False, limit=20):
    sources = [("law/list.json", "active")]
    if include_repealed:
        sources.append(("law/repeal_list.json", "repealed"))

    limit = max(limit, 0)
    query_norm = normalized(query)
    exact_results = []
    partial_results = []
    for source_file, status in sources:
        for entry in iter_json_records(repo / source_file, required=True):
            name = law_name(entry)
            name_norm = normalized(name)
            if name_norm == query_norm:
                if len(exact_results) < limit:
                    exact_results.append(law_entry(entry, source_file, status, ["name:exact"]))
            elif not exact and query_norm in name_norm and len(partial_results) < limit:
                partial_results.append(law_entry(entry, source_file, status, ["name:partial"]))
    return (exact_results + partial_results)[:limit]


def search_json_sources(repo, query, source_files, status="metadata", limit=20, required=False):
    limit = max(limit, 0)
    results = []
    if limit == 0:
        return results
    for source_file in source_files:
        for entry in iter_json_records(repo / source_file, required=required):
            if json_contains(entry, query):
                should_continue = append_limited(
                    results,
                    law_entry(entry, source_file, status, ["json:contains"]),
                    limit,
                )
                if not should_continue:
                    return results
    return results


def search_abbreviations(repo, query, limit=20):
    limit = max(limit, 0)
    if limit == 0:
        return []

    exact_results = search_law_names(repo, query, include_repealed=False, exact=True, limit=limit)
    partial_results = []
    seen = {result.get("num") for result in exact_results}
    by_num, by_name = law_catalog(repo)
    source_files = ["law/egov_abb.json", "law/law_abb.json", "law/ryakusyou.json"]
    for source_file in source_files:
        for entry in iter_json_records(repo / source_file, required=True):
            if source_file == "law/ryakusyou.json":
                matches = matching_ryakusyou_targets(entry, query, by_name)
            else:
                rank = match_rank(abbr_values(entry), query)
                resolved = resolve_abbr_entry(entry, source_file, by_num, by_name, f"abbr:{rank}") if rank else None
                matches = [(rank, entry, None)] if resolved is not None else []

            for rank, source_entry, catalog_entry in matches:
                if source_file == "law/ryakusyou.json" and catalog_entry is None:
                    result = abbr_usage_entry(source_entry, source_file, f"abbr:{rank}")
                elif catalog_entry is None:
                    result = resolve_abbr_entry(source_entry, source_file, by_num, by_name, f"abbr:{rank}")
                else:
                    result = entry_with_abbr_source(catalog_entry, source_file, source_entry, f"abbr:{rank}")
                if result is None or result.get("num") in seen:
                    continue
                seen.add(result.get("num"))
                if rank == "exact" and len(exact_results) < limit:
                    exact_results.append(result)
                elif rank == "partial" and len(partial_results) < limit:
                    partial_results.append(result)
    return (exact_results + partial_results)[:limit]


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
        return EXIT_DATA_ERROR

    try:
        if args.name is not None:
            require_nonempty_query(args.name, "name")
            results = search_law_names(
                repo, args.name, args.include_repealed, exact=False, limit=args.limit
            )
        elif args.exact is not None:
            require_nonempty_query(args.exact, "exact")
            results = search_law_names(
                repo, args.exact, args.include_repealed, exact=True, limit=args.limit
            )
        elif args.abbr is not None:
            require_nonempty_query(args.abbr, "abbreviation")
            results = search_abbreviations(repo, args.abbr, limit=args.limit)
        else:
            require_nonempty_query(args.yomikae, "yomikae")
            results = search_json_sources(
                repo, args.yomikae, ["law/yomikae.json"], limit=args.limit, required=True
            )
    except DataFileError as exc:
        print(str(exc), file=sys.stderr)
        print("[]")
        return EXIT_DATA_ERROR

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
