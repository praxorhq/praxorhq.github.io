#!/usr/bin/env python3
"""Стартовый замер поставки изменений по истории git.

Считает то, что можно честно посчитать по git без CI и системы инцидентов:
частоту релизов, lead time от коммита до релиза, размер изменений,
долю откатов (revert) и, для релизов по тегам, долю релизов, за которыми
быстро последовал следующий (грубая замена доли неудачных изменений).

Только стандартная библиотека Python 3.8+. Ничего не отправляет в сеть.

Примеры:
    python3 git_delivery_metrics.py --repo path/to/repo
    python3 git_delivery_metrics.py --repo . --days 90 --releases tags --tag-pattern 'v*'
    python3 git_delivery_metrics.py --repo . --releases merges --format csv > baseline.csv

Описание и ограничения: https://praxor.ru/ai-pilot-templates/
"""

import argparse
import csv
import fnmatch
import json
import subprocess
import sys
import time
from datetime import datetime, timezone

DEFAULT_EXCLUDE = [
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb",
    "poetry.lock", "uv.lock", "Pipfile.lock", "go.sum", "Cargo.lock",
    "composer.lock", "Gemfile.lock", "gradle.lockfile",
]


def git(repo, *args):
    res = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {res.stderr.strip()}")
    return res.stdout


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    if n == 0:
        return None
    mid = n // 2
    return xs[mid] if n % 2 else (xs[mid - 1] + xs[mid]) / 2


def percentile(xs, p):
    """Перцентиль методом ближайшего ранга."""
    xs = sorted(xs)
    if not xs:
        return None
    k = max(0, min(len(xs) - 1, -(-p * len(xs) // 100) - 1))
    return xs[int(k)]


def first_parent_commits(repo, branch, since, until):
    """Коммиты основной ветки за период: (sha, время коммита, число родителей, тема)."""
    out = git(repo, "log", branch, "--first-parent", "--format=%H%x1f%ct%x1f%P%x1f%s",
              f"--since={since}", f"--until={until}")
    rows = []
    for line in out.splitlines():
        sha, ct, parents, subject = line.split("\x1f", 3)
        rows.append({"sha": sha, "time": int(ct), "parents": len(parents.split()), "subject": subject})
    rows.reverse()
    return rows


def change_size(repo, sha, parents, exclude):
    """Строки добавлено + удалено относительно первого родителя, без lock-файлов и бинарных файлов."""
    if parents == 0:
        return None
    out = git(repo, "diff", "--numstat", "--no-renames", f"{sha}^1", sha)
    lines, files = 0, 0
    for row in out.splitlines():
        added, deleted, path = row.split("\t", 2)
        name = path.rsplit("/", 1)[-1]
        if added == "-" or any(fnmatch.fnmatch(name, pat) for pat in exclude):
            continue
        lines += int(added) + int(deleted)
        files += 1
    return lines, files


def is_revert(repo, sha, subject):
    if subject.startswith('Revert "'):
        return True
    body = git(repo, "log", "-1", "--format=%b", sha)
    return "This reverts commit" in body


def tag_releases(repo, branch, pattern, since, until):
    out = git(repo, "for-each-ref", "refs/tags",
              "--format=%(refname:short)%1f%(creatordate:unix)%1f%(objectname)%1f%(*objectname)")
    tags = []
    for line in out.splitlines():
        name, ts, obj, peeled = line.split("\x1f")
        if not fnmatch.fnmatch(name, pattern):
            continue
        commit = peeled or obj
        if git(repo, "cat-file", "-t", commit).strip() != "commit":
            continue
        ok = subprocess.run(["git", "-C", repo, "merge-base", "--is-ancestor", commit, branch]).returncode == 0
        if ok:
            tags.append({"name": name, "time": int(ts), "commit": commit})
    tags.sort(key=lambda t: t["time"])
    in_period = [t for t in tags if since <= t["time"] <= until]
    result = []
    for t in in_period:
        prev = [p for p in tags if p["time"] < t["time"]]
        rng = f"{prev[-1]['commit']}..{t['commit']}" if prev else t["commit"]
        # У первого тега в истории нет предыдущего: берём только коммиты, созданные внутри периода.
        result.append({"name": t["name"], "time": t["time"], "range": rng, "floor": None if prev else since})
    return result


def merge_releases(fp):
    return [{"name": c["sha"][:10], "time": c["time"], "range": f"{c['sha']}^1..{c['sha']}^2", "floor": None}
            for c in fp if c["parents"] > 1]


def lead_times(repo, releases):
    """Часы от создания каждого коммита (author date) до релиза, в который он попал."""
    hours = []
    for r in releases:
        out = git(repo, "log", "--no-merges", "--format=%at", r["range"])
        for at in out.split():
            at = int(at)
            if r.get("floor") is not None and at < r["floor"]:
                continue
            hours.append(max(0, r["time"] - at) / 3600)
    return hours


def fmt_hours(h):
    if h is None:
        return "—"
    if h < 48:
        return f"{h:.1f} ч"
    return f"{h / 24:.1f} дн"


def main():
    ap = argparse.ArgumentParser(description="Стартовый замер поставки изменений по истории git.")
    ap.add_argument("--repo", default=".", help="путь к репозиторию (по умолчанию текущий каталог)")
    ap.add_argument("--branch", default="HEAD", help="основная ветка (по умолчанию HEAD)")
    ap.add_argument("--days", type=int, default=90, help="длина периода в днях (по умолчанию 90)")
    ap.add_argument("--end", help="конец периода, ГГГГ-ММ-ДД (по умолчанию сейчас)")
    ap.add_argument("--releases", choices=["auto", "tags", "merges", "commits"], default="auto",
                    help="что считать релизом: теги, merge-коммиты в основную ветку или каждый коммит основной ветки")
    ap.add_argument("--tag-pattern", default="*", help="маска тегов-релизов, например 'v*'")
    ap.add_argument("--hotfix-hours", type=float, default=24,
                    help="окно для «быстрого следующего релиза», часов (только для тегов)")
    ap.add_argument("--exclude", action="append", default=None,
                    help="маска файлов, которые не учитывать в размере изменений (можно повторять)")
    ap.add_argument("--format", choices=["text", "json", "csv"], default="text")
    a = ap.parse_args()

    try:
        git(a.repo, "rev-parse", "--git-dir")
    except RuntimeError as e:
        sys.exit(f"Не похоже на git-репозиторий: {e}")
    if git(a.repo, "rev-parse", "--is-shallow-repository").strip() == "true":
        print("Внимание: репозиторий склонирован не полностью (shallow). Сделайте git fetch --unshallow.",
              file=sys.stderr)

    until = int(datetime.strptime(a.end, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()) + 86399 \
        if a.end else int(time.time())
    since = until - a.days * 86400
    exclude = DEFAULT_EXCLUDE + (a.exclude or [])

    fp = first_parent_commits(a.repo, a.branch, since, until)
    mode = a.releases
    if mode == "auto":
        if tag_releases(a.repo, a.branch, a.tag_pattern, since, until):
            mode = "tags"
        elif any(c["parents"] > 1 for c in fp):
            mode = "merges"
        else:
            mode = "commits"

    if mode == "tags":
        releases = tag_releases(a.repo, a.branch, a.tag_pattern, since, until)
    elif mode == "merges":
        releases = merge_releases(fp)
    else:
        releases = [{"name": c["sha"][:10], "time": c["time"], "range": None} for c in fp]

    weeks = a.days / 7
    lt = lead_times(a.repo, releases) if mode in ("tags", "merges") else []

    sizes, file_counts, reverts = [], [], 0
    for c in fp:
        s = change_size(a.repo, c["sha"], c["parents"], exclude)
        if s:
            sizes.append(s[0])
            file_counts.append(s[1])
        if is_revert(a.repo, c["sha"], c["subject"]):
            reverts += 1

    quick = None
    if mode == "tags" and len(releases) > 1:
        gaps = [(b["time"] - x["time"]) / 3600 for x, b in zip(releases, releases[1:])]
        quick = sum(1 for g in gaps if g <= a.hotfix_hours) / len(gaps)

    gaps_days = [(b["time"] - x["time"]) / 86400 for x, b in zip(releases, releases[1:])]
    mode_names = {"tags": "теги", "merges": "merge-коммиты в основную ветку", "commits": "коммиты основной ветки"}

    metrics = [
        ("period", "Период", f"{datetime.fromtimestamp(since, timezone.utc):%Y-%m-%d} — "
                             f"{datetime.fromtimestamp(until, timezone.utc):%Y-%m-%d} ({a.days} дн)"),
        ("release_source", "Что считается релизом", mode_names[mode]),
        ("releases", "Релизов за период", len(releases)),
        ("releases_per_week", "Релизов в неделю", round(len(releases) / weeks, 2) if weeks else None),
        ("days_between_releases_median", "Дней между релизами, медиана",
         round(median(gaps_days), 1) if gaps_days else None),
        ("lead_time_hours_median", "Lead time, медиана", round(median(lt), 1) if lt else None),
        ("lead_time_hours_p85", "Lead time, 85-й перцентиль", round(percentile(lt, 85), 1) if lt else None),
        ("lead_time_commits", "Коммитов в расчёте lead time", len(lt)),
        ("changes", "Изменений в основной ветке", len(fp)),
        ("change_size_lines_median", "Размер изменения, строк, медиана", median(sizes)),
        ("change_size_lines_p85", "Размер изменения, строк, 85-й перцентиль", percentile(sizes, 85)),
        ("change_size_files_median", "Файлов в изменении, медиана", median(file_counts)),
        ("revert_share", "Доля откатов (revert)", round(reverts / len(fp), 3) if fp else None),
        ("quick_next_release_share", f"Доля релизов со следующим релизом в течение {a.hotfix_hours:g} ч",
         round(quick, 3) if quick is not None else None),
    ]

    if a.format == "json":
        print(json.dumps({k: v for k, _, v in metrics}, ensure_ascii=False, indent=2))
    elif a.format == "csv":
        w = csv.writer(sys.stdout)
        w.writerow(["metric", "name", "value"])
        for k, name, v in metrics:
            w.writerow([k, name, "" if v is None else v])
    else:
        for k, name, v in metrics:
            if k.startswith("lead_time_hours"):
                v = fmt_hours(v)
            elif k.endswith("_share") and v is not None:
                v = f"{v * 100:.1f}%"
            elif isinstance(v, float) and v.is_integer():
                v = int(v)
            print(f"{name:<52} {'—' if v is None else v}")
        if mode == "commits":
            print("\nLead time не считается: релизы не отмечены тегами и нет merge-коммитов. "
                  "Укажите теги через --releases tags или возьмите lead time из CI.", file=sys.stderr)


if __name__ == "__main__":
    main()
