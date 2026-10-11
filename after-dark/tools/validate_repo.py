#!/usr/bin/env python3
"""Статическая проверка репозитория AFTER DARK.

Запускается локально и в GitHub Actions. Проверяет:
  * формат VERSION (семантическое версионирование) и совпадение с __version__;
  * синтаксис всех Python-файлов;
  * корректность всех XML-файлов тюнинга;
  * корректность JSON-строк и совпадение ключей en_us / ru;
  * наличие обязательных документов;
  * отсутствие игровых ресурсов и архивов в репозитории.

Финальная проверка работы мода ВЫПОЛНЯЕТСЯ ТОЛЬКО В ИГРЕ (см. docs/COMPATIBILITY.md).
Скрипт не запускает игру и не заменяет игровое тестирование.
"""

from __future__ import annotations

import ast
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
REQUIRED_FILES = [
    "README.md", "CHANGELOG.md", "CONTRIBUTING.md", "VERSION", ".gitignore",
    "docs/ARCHITECTURE.md", "docs/GAMEPLAY_SYSTEMS.md", "docs/COMPATIBILITY.md",
    "docs/ROADMAP.md", "tuning/strings/en_us.json", "tuning/strings/ru.json",
]
FORBIDDEN_SUFFIXES = (".package", ".ts4script", ".zip", ".rar", ".7z")
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", ".venv-tests"}


def _files(suffix: str) -> list[Path]:
    return sorted(
        p for p in ROOT.rglob(f"*{suffix}")
        if not (SKIP_DIRS & set(p.relative_to(ROOT).parts))
    )


def check_version(errors: list[str]) -> None:
    version_file = ROOT / "VERSION"
    if not version_file.exists():
        errors.append("Нет файла VERSION.")
        return
    version = version_file.read_text(encoding="utf-8").strip()
    if not SEMVER.match(version):
        errors.append(f"VERSION должен быть в формате X.Y.Z, сейчас: {version!r}.")
    sys.path.insert(0, str(ROOT / "src"))
    try:
        from after_dark import __version__
    except ImportError as exc:
        errors.append(f"Не удалось импортировать пакет after_dark: {exc}")
        return
    if __version__ != version:
        errors.append(f"__version__ ({__version__}) не совпадает с VERSION ({version}).")


def check_python(errors: list[str]) -> int:
    files = _files(".py")
    for path in files:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            errors.append(f"Ошибка синтаксиса: {path.relative_to(ROOT)}: {exc}")
    return len(files)


def check_xml(errors: list[str]) -> int:
    files = _files(".xml")
    for path in files:
        try:
            ET.parse(path)
        except ET.ParseError as exc:
            errors.append(f"Некорректный XML: {path.relative_to(ROOT)}: {exc}")
    return len(files)


def check_strings(errors: list[str]) -> int:
    locales = {}
    for name in ("en_us", "ru"):
        path = ROOT / "tuning" / "strings" / f"{name}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"Некорректный JSON строк {path.name}: {exc}")
            return 0
        locales[name] = {k for k in data if not k.startswith("_")}
    missing = locales["en_us"] ^ locales["ru"]
    for key in sorted(missing):
        errors.append(f"Строка {key!r} есть не во всех языках.")
    return len(locales["en_us"])


def check_required(errors: list[str]) -> None:
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            errors.append(f"Отсутствует обязательный файл: {rel}")


def check_forbidden(errors: list[str]) -> None:
    for path in ROOT.rglob("*"):
        if path.is_file() and not (SKIP_DIRS & set(path.relative_to(ROOT).parts)):
            if path.suffix.lower() in FORBIDDEN_SUFFIXES:
                errors.append(f"Игровой ресурс/архив не должен храниться в git: {path.relative_to(ROOT)}")


def main() -> int:
    errors: list[str] = []
    check_required(errors)
    check_version(errors)
    py_count = check_python(errors)
    xml_count = check_xml(errors)
    str_count = check_strings(errors)
    check_forbidden(errors)

    if errors:
        print("ПРОВЕРКА НЕ ПРОЙДЕНА:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print(f"OK: python={py_count}, xml={xml_count}, строк={str_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
