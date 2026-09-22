#!/usr/bin/env python3
"""Calcula o percentual de tradução PT-BR a partir do CSV principal do jogo.

Regra:
- coluna 0: ID
- coluna 1: texto em inglês que será traduzido para PT-BR
- quando a coluna 1 já contém texto em português, a linha é considerada traduzida
"""

import argparse
import csv
import os
from pathlib import Path

PTBR_WORDS = (
    'conta', 'você', 'menu', 'salvar', 'jogar', 'jogo', 'continuar', 'iniciar', 'selecionar',
    'opções', 'configuração', 'português', 'brasil', 'código', 'todo', 'voltar', 'cancelar',
    'carregar', 'desligar', 'conectado', 'dispositivo', 'perfil', 'compartilhar', 'finalizar',
    'desempenho', 'tomada', 'tecla', 'botão', 'música', 'sala', 'página', 'desligar'
)

ACCENT_CHARS = set('áàâãéêíóôõúç')


def normalize(value):
    if value is None:
        return ''
    return str(value).strip().replace('\0', '')


def looks_ptbr(value):
    text = normalize(value)
    if not text or text in {'-', 'N/A', 'NA', 'null', 'none'}:
        return False

    lowered = text.lower()
    if any(ch in lowered for ch in ACCENT_CHARS):
        return True
    return any(word in lowered for word in PTBR_WORDS)


def calculate_progress(csv_path: Path):
    total = 0
    translated = 0

    if not csv_path.exists():
        return total, translated, 0.0, 'CSV principal não encontrado.'

    with csv_path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.reader(handle)
        for row in reader:
            if len(row) < 2:
                continue

            text_in_target_column = normalize(row[1])
            if not text_in_target_column:
                continue

            total += 1
            if looks_ptbr(text_in_target_column):
                translated += 1

    pct = 0.0 if total == 0 else (translated / total) * 100.0
    summary = (
        f'Entradas avaliadas: {total}\n'
        f'Entradas traduzidas: {translated}\n'
        f'Progresso estimado: {pct:.2f}%'
    )
    return total, translated, pct, summary


def write_github_output(summary: str, pct: float):
    output_path = os.environ.get('GITHUB_OUTPUT')
    if not output_path:
        return

    with open(output_path, 'a', encoding='utf-8') as handle:
        handle.write(f'percent={pct}\n')
        handle.write(f'raw_percent={pct}\n')
        handle.write('summary<<EOF\n')
        handle.write(summary)
        handle.write('\nEOF\n')


def main():
    parser = argparse.ArgumentParser(description='Calcula o percentual PT-BR a partir do CSV do jogo.')
    parser.add_argument('--csv', default='cache/localization/maingame.csv', help='Caminho do CSV principal.')
    parser.add_argument('--format', choices=['plain', 'github'], default='plain')
    args = parser.parse_args()

    csv_path = Path(args.csv)
    total, translated, pct, summary = calculate_progress(csv_path)

    if args.format == 'github':
        write_github_output(summary, pct)
        print(summary)
        print(f'percent={pct}')
    else:
        print(summary)


if __name__ == '__main__':
    main()
