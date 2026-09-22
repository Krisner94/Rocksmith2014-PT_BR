# Sobre

Rocksmith 2014 PT-BR é um projeto comunitário de localização focado em traduzir os arquivos do jogo do inglês para o português do Brasil, preservando a estrutura original e a compatibilidade com o jogo.

## Objetivo do projeto

O projeto tem como objetivo:

- traduzir os textos do jogo para o português do Brasil;
- manter a estrutura original dos arquivos do Rocksmith 2014 compatível com o jogo;
- automatizar a criação e publicação de builds via GitHub Actions;
- gerar um pacote PSARC final pronto para uso e distribuição.

## Fluxo de trabalho

O projeto usa um fluxo simples:

1. Os arquivos do jogo ficam organizados dentro da pasta `cache/`.
2. O script `psarc.py` empacota esses arquivos em um arquivo PSARC.
3. O GitHub Actions gera uma release com o arquivo final `cache.psarc`.

## Ferramentas utilizadas

- Python 3
- pycryptodome
- docopt
- GitHub Actions

## Escopo

Este repositório foi criado para trabalho de localização, empacotamento e automação de release dos arquivos do Rocksmith 2014.

## Instalação e substituição

O pacote gerado deve ser colocado na pasta de instalação do Rocksmith 2014 e substituir o arquivo PSARC original que estiver nesse local.

Caminho típico no Windows:

```text
C:\Program Files (x86)\Steam\steamapps\common\Rocksmith2014\cache.psarc
```

Se o jogo estiver instalado em outra pasta, basta localizar a pasta raiz do Rocksmith 2014 e substituir o arquivo `cache.psarc` existente ali.

Esse é o arquivo final usado pelo jogo, e deve ser copiado para o diretório de instalação do jogo, em vez da pasta de origem usada neste repositório.
