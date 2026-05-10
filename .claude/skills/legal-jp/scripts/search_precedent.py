#!/usr/bin/env python3
import argparse
import json
import os
import sys
import unicodedata
from pathlib import Path


DEFAULT_REPO = os.environ.get(
    "LEGAL_JP_DATA_SET_PATH", str(Path(__file__).resolve().parents[4] / "data_set")
)
HEAVY_DETAIL_FIELDS = {"contents", "content", "本文", "full_text"}
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
        return None
    except json.JSONDecodeError as exc:
        raise DataFileError(f"error: invalid JSON in {path}: {exc}") from exc
    except PermissionError as exc:
        raise DataFileError(f"error: unreadable JSON file: {path}: {exc}") from exc


def text_value(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def contains(value, query):
    return str(query).casefold() in text_value(value).casefold()


def normalize_case_number(value):
    normalized = unicodedata.normalize("NFKC", text_value(value)).casefold()
    for token in (" ", "\t", "\n", "\r", "年", "第", "号"):
        normalized = normalized.replace(token, "")
    return normalized


def case_number_contains(value, query):
    return normalize_case_number(query) in normalize_case_number(value)


def raw_value_for(entry, *keys):
    for key in keys:
        if key in entry and entry[key] is not None:
            return entry[key]
    return None


def rel_json_path(repo, path):
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def ensure_within(base, candidate):
    base_resolved = base.resolve()
    candidate_resolved = candidate.resolve()
    try:
        candidate_resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise DataFileError(
            f"error: precedent detail path escapes dataset directory: {candidate}"
        ) from exc
    return candidate_resolved


def build_lawsuit_index(ddir):
    index = {}
    for path in sorted(ddir.glob("*.json")):
        if path.name == "list.json":
            continue
        safe_path = ensure_within(ddir, path)
        lawsuit_id = path.stem.rsplit("_", 1)[-1]
        index.setdefault(lawsuit_id, []).append(safe_path)
    return index


def detail_matches_entry(path, entry):
    detail = load_json(path, required=True)
    if not isinstance(detail, dict):
        return False

    comparisons = [
        (raw_value_for(entry, "case_number"), raw_value_for(detail, "case_number")),
        (raw_value_for(entry, "court", "court_name"), raw_value_for(detail, "court", "court_name")),
        (raw_value_for(entry, "trial_type"), raw_value_for(detail, "trial_type")),
    ]
    for expected, actual in comparisons:
        if expected is not None and actual is not None and str(expected) != str(actual):
            return False
    return True


def explicit_json_path(ddir, entry):
    for key in ("json_path", "file_path", "path", "filename", "source_file"):
        value = raw_value_for(entry, key)
        if not value:
            continue
        path = Path(str(value))
        if path.is_absolute():
            raise DataFileError(f"error: absolute precedent detail path is not allowed: {path}")
        candidates = []
        candidates.extend([ddir / path, ddir.parent / path])
        if "precedent/" in str(value):
            parts = Path(str(value)).parts
            try:
                precedent_idx = parts.index("precedent")
                candidates.append(ddir.parents[1] / Path(*parts[precedent_idx:]))
            except (ValueError, IndexError):
                pass
        for candidate in candidates:
            if candidate.is_file():
                return ensure_within(ddir, candidate)
    return None


def discover_json_path(ddir, entry, lawsuit_index):
    explicit = explicit_json_path(ddir, entry)
    if explicit is not None:
        return explicit

    lawsuit_id = raw_value_for(entry, "lawsuit_id")
    if lawsuit_id is None:
        return None
    candidates = lawsuit_index.get(str(lawsuit_id), [])
    if not candidates:
        return None
    if len(candidates) == 1:
        return ensure_within(ddir, candidates[0])

    trial_type = raw_value_for(entry, "trial_type")
    if trial_type is not None:
        token = f"_{trial_type}_"
        trial_matches = [path for path in candidates if token in path.stem]
        if len(trial_matches) == 1:
            return ensure_within(ddir, trial_matches[0])
        if trial_matches:
            candidates = trial_matches

    detail_matches = [path for path in candidates if detail_matches_entry(path, entry)]
    if len(detail_matches) == 1:
        return ensure_within(ddir, detail_matches[0])
    if len(candidates) == 1:
        return ensure_within(ddir, candidates[0])
    return None


def light_raw(entry):
    return {key: value for key, value in entry.items() if key not in HEAVY_DETAIL_FIELDS}


def detail_content(entry):
    for key in HEAVY_DETAIL_FIELDS:
        value = raw_value_for(entry, key)
        if value is not None:
            return text_value(value)
    return ""


def make_snippet(content, keyword, radius=40):
    folded = content.casefold()
    needle = str(keyword).casefold()
    pos = folded.find(needle)
    if pos < 0:
        return ""
    start = max(0, pos - radius)
    end = min(len(content), pos + len(str(keyword)) + radius)
    prefix = "..." if start else ""
    suffix = "..." if end < len(content) else ""
    return f"{prefix}{content[start:end]}{suffix}"


def merged_entry(entry):
    detail = entry.get("_detail")
    if isinstance(detail, dict):
        merged = dict(detail)
        merged.update(entry.get("_metadata", {}))
    else:
        merged = dict(entry.get("_metadata", entry))
    return merged


def entry_from_detail(repo, ddir, path, decade):
    path = ensure_within(ddir, path)
    detail = load_json(path, required=True)
    if not isinstance(detail, dict):
        return None
    return {
        "_metadata": light_raw(detail),
        "_detail": detail,
        "_detail_path": path,
        "_source_file": rel_json_path(repo, path),
        "_decade": decade,
    }


def decade_dirs(repo, decade=None):
    precedent_dir = repo / "precedent"
    if decade:
        decade = str(decade)
        if not decade.isdigit() or len(decade) != 4:
            raise DataFileError(f"error: invalid precedent decade: {decade}")
        ddir = ensure_within(precedent_dir, precedent_dir / decade)
        if not ddir.is_dir():
            raise DataFileError(f"error: precedent decade directory not found: {ddir}")
        return [ddir]
    dirs = []
    for path in sorted(precedent_dir.iterdir()):
        if not path.is_dir():
            continue
        if not path.name.isdigit() or len(path.name) != 4:
            raise DataFileError(f"error: invalid precedent decade directory: {path}")
        dirs.append(ensure_within(precedent_dir, path))
    return dirs


def iter_metadata_entries(repo, decade=None, load_details=True):
    for ddir in decade_dirs(repo, decade):
        lawsuit_index = build_lawsuit_index(ddir)
        seen_paths = set()
        rows = load_json(ddir / "list.json", required=True)
        if isinstance(rows, dict):
            rows = rows.get("items") or rows.get("data") or rows.get("results") or []
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                detail_path = discover_json_path(ddir, row, lawsuit_index)
                detail = load_json(detail_path, required=True) if detail_path and load_details else None
                if detail_path:
                    seen_paths.add(detail_path.resolve())
                yield {
                    "_metadata": light_raw(row),
                    "_detail": detail if isinstance(detail, dict) else None,
                    "_detail_path": detail_path,
                    "_source_file": rel_json_path(repo, ddir / "list.json"),
                    "_decade": ddir.name,
                }

        for path in sorted(ddir.glob("*.json")):
            if path.name == "list.json" or path.resolve() in seen_paths:
                continue
            entry = entry_from_detail(repo, ddir, path, ddir.name)
            if entry is not None:
                yield entry


def metadata_entries(repo, decade=None):
    return list(iter_metadata_entries(repo, decade))


def with_loaded_detail(entry):
    if entry.get("_detail") is None and entry.get("_detail_path"):
        entry = dict(entry)
        detail = load_json(entry["_detail_path"], required=True)
        entry["_detail"] = detail if isinstance(detail, dict) else None
    return entry


def format_entry(repo, entry, content=False, snippet_keyword=None):
    merged = merged_entry(entry)
    detail_path = entry.get("_detail_path")
    result = {
        "title": raw_value_for(merged, "case_name", "title", "name"),
        "case_number": raw_value_for(merged, "case_number"),
        "court": raw_value_for(merged, "court", "court_name"),
        "date": raw_value_for(merged, "date"),
        "decade": entry.get("_decade"),
        "source_file": entry.get("_source_file"),
        "json_path": rel_json_path(repo, detail_path) if detail_path else None,
        "raw": light_raw(merged),
    }

    full_content = detail_content(merged)
    if content:
        result["content"] = full_content
    if snippet_keyword is not None:
        result["snippet"] = make_snippet(full_content, snippet_keyword)
    return result


def court_matches(entry, court):
    if court is None:
        return True
    merged = merged_entry(entry)
    return any(
        contains(value, court)
        for value in (
            raw_value_for(merged, "court", "court_name"),
            raw_value_for(merged, "trial_type"),
        )
    )


def metadata_search(repo, field, query, court=None, decade=None, content=False, snippet=False, limit=20):
    results = []
    limit = max(limit, 0)
    if limit == 0:
        return results

    load_details = field != "case_number"
    for entry in iter_metadata_entries(repo, decade, load_details=load_details):
        merged = merged_entry(entry)
        if field == "title":
            values = [raw_value_for(merged, "case_name", "title", "name")]
        elif field == "case_number":
            values = [
                raw_value_for(merged, "case_number"),
                raw_value_for(merged, "lawsuit_id"),
                entry.get("_source_file"),
            ]
            detail_path = entry.get("_detail_path")
            if detail_path:
                values.append(rel_json_path(repo, detail_path))
        else:
            values = []

        if field == "case_number":
            matched = any(case_number_contains(value, query) for value in values)
        else:
            matched = any(contains(value, query) for value in values)
        if matched:
            entry = with_loaded_detail(entry)
        if matched and court_matches(entry, court):
            results.append(format_entry(repo, entry, content=content, snippet_keyword=query if snippet else None))
            if len(results) >= limit:
                return results
    return results


def text_search(repo, query, court=None, decade=None, content=False, snippet=False, limit=20):
    results = []
    limit = max(limit, 0)
    if limit == 0:
        return results

    for entry in iter_metadata_entries(repo, decade):
        merged = merged_entry(entry)
        if not contains(detail_content(merged), query):
            continue
        if not court_matches(entry, court):
            continue
        results.append(format_entry(repo, entry, content=content, snippet_keyword=query if snippet else None))
        if len(results) >= limit:
            return results
    return results


def build_parser():
    parser = argparse.ArgumentParser(description="Search legal-jp precedent metadata and detail JSON")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--title")
    group.add_argument("--case-number")
    group.add_argument("--text")
    parser.add_argument("--court")
    parser.add_argument("--decade")
    parser.add_argument("--content", action="store_true")
    parser.add_argument("--snippet", action="store_true")
    parser.add_argument("--limit", type=int, default=20)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    repo = Path(args.repo)
    if not (repo / "precedent").is_dir():
        print(f"error: precedent directory not found: {repo / 'precedent'}", file=sys.stderr)
        print("[]")
        return EXIT_DATA_ERROR

    try:
        if args.title is not None:
            results = metadata_search(
                repo,
                "title",
                args.title,
                court=args.court,
                decade=args.decade,
                content=args.content,
                snippet=args.snippet,
                limit=args.limit,
            )
        elif args.case_number is not None:
            results = metadata_search(
                repo,
                "case_number",
                args.case_number,
                court=args.court,
                decade=args.decade,
                content=args.content,
                snippet=args.snippet,
                limit=args.limit,
            )
        else:
            results = text_search(
                repo,
                args.text,
                court=args.court,
                decade=args.decade,
                content=args.content,
                snippet=args.snippet,
                limit=args.limit,
            )
    except DataFileError as exc:
        print(str(exc), file=sys.stderr)
        print("[]")
        return EXIT_DATA_ERROR

    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
