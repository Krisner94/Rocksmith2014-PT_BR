# Rocksmith 2014 PT-BR

Projeto de tradução e empacotamento da base de arquivos do Rocksmith 2014 para português do Brasil.

## Visão geral

Este repositório contém a estrutura de arquivos do jogo em formato de diretório e um script para empacotar essa pasta em um arquivo PSARC compatível com o Rocksmith 2014.

A ideia principal é manter a tradução em um diretório de trabalho, gerar o pacote final e publicar uma release automaticamente em GitHub Actions.

## Estrutura do projeto

```text
Rocksmith2014-PT_BR/
├── .github/
│   └── workflows/
│       └── release.yml
├── cache/
│   ├── behaviors/
│   ├── flatmodels/
│   ├── gfxassets/
│   ├── localization/
│   ├── sltsv1_aggregategraph.nt
│   └── sparkactionmap.actionmap
├── psarc.py
├── cache.psarc
├── scripts/
│   └── ptbr_translation_progress.py
├── README.md
└── ABOUT.md
```

## Como funciona

1. Os arquivos originais do jogo ficam em `cache/`.
2. A pasta `cache/` é empacotada pelo script `psarc.py`.
3. O resultado final é o arquivo `cache.psarc`.
4. O GitHub Actions gera uma release com esse arquivo automaticamente em cada build.

## Requisitos

- Python 3.11+
- Biblioteca `pycryptodome`
- Biblioteca `docopt`

Instale com:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install pycryptodome docopt
```

## Gerar o PSARC localmente

No diretório raiz do projeto, execute:

```bash
python3 ./psarc.py pack ./cache
```

Isso gera o arquivo:

```bash
cache.psarc
```

## GitHub Actions

A workflow em `.github/workflows/release.yml`:

- valida a pasta `cache/`
- executa o empacotamento do PSARC
- publica uma release com o arquivo `cache.psarc`
- usa uma tag no formato `YYYYMMDD-HHMMSS-hash`

## Objetivo da tradução

O objetivo deste projeto é localizar e adaptar textos do Rocksmith 2014 para o português do Brasil, mantendo a estrutura original do jogo e gerando um pacote pronto para uso.

## Instalação no Rocksmith 2014

O arquivo final gerado deve ser colocado na pasta de instalação do jogo e substituir o arquivo original do PSARC.

Local típico em Windows:

```text
C:\Program Files (x86)\Steam\steamapps\common\Rocksmith2014\cache.psarc
```

Se a sua instalação estiver em outra pasta, basta localizar a pasta do jogo e substituir o arquivo `cache.psarc` que estiver no diretório principal do jogo.

Exemplo:

```text
...\Steam\steamapps\common\Rocksmith2014\cache.psarc
```

Importante: o arquivo gerado precisa substituir o original no diretório raiz do jogo, e não a pasta `cache/` dentro do projeto.

## Licença

Este projeto é destinado ao uso educacional e de modificação para tradução de arquivos do jogo Rocksmith 2014.
