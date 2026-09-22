#!/usr/bin/env python3
"""Calcula um percentual aproximado de tradução PT-BR em uma pasta."""

import argparse
import json
import os
from pathlib import Path

EXTENSIONS = {
    '.json', '.txt', '.ini', '.cfg', '.xml', '.csv', '.yaml', '.yml', '.lang', '.str', '.res'
}

PTBR_HINTS = (
    'pt-br', 'pt_br', 'ptbr', 'portugues', 'português', 'brazil', 'brasil', 'pt-brasil'
)


def is_candidate_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in EXTENSIONS


def is_ptbr_file(path: Path) -> bool:
    lowered = str(path).lower()
    return any(hint in lowered for hint in PTBR_HINTS)


def collect_metrics(root: Path):
    total = 0
    translated = 0
    seen = []

    for item in sorted(root.rglob('*')):
        if not is_candidate_file(item):
            continue
        total += 1
        seen.append(item)
        if is_ptbr_file(item):
            translated += 1

    return total, translated, seen


def build_summary(total: int, translated: int, pct: float) -> str:
    if total == 0:
        return 'Nenhum arquivo traduzível encontrado na pasta de origem.'
    return (
        f'Arquivos avaliados: {total}\n'
        f'Arquivos em PT-BR: {translated}\n'
        f'Progresso estimado: {pct:.2f}%'
    )


def write_github_output(summary: str, pct: float):
    output_path = os.environ.get('GITHUB_OUTPUT')
    if not output_path:
        return
    with open(output_path, 'a', encoding='utf-8') as f:
        f.write(f'percent={pct}\n')
        f.write(f'pct={pct}\n')
        f.write('summary<<EOF\n')
        f.write(summary)
        f.write('\nEOF\n')


def main():
    parser = argparse.ArgumentParser(description='Calcula percentual aproximado da tradução PT-BR.')
    parser.add_argument('--root', default='cache', help='Diretório que contém os arquivos de tradução.')
    parser.add_argument('--format', choices=['plain', 'json', 'github'], default='plain')
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f'Pasta não encontrada: {root}')
        raise SystemExit(1)

    total, translated, _ = collect_metrics(root)
    pct = 0.0 if total == 0 else (translated / total) * 100.0
    summary = build_summary(total, translated, pct)

    if args.format == 'json':
        print(json.dumps({
            'total': total,
            'translated': translated,
            'percent': round(pct, 2),
            'summary': summary,
        }, ensure_ascii=False, indent=2))
    elif args.format == 'github':
        write_github_output(summary, pct)
        print(summary)
        print(f'percent={pct}')
    else:
        print(summary)


if __name__ == '__main__':
    main()
