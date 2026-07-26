# Código-fonte

A implementação do YouTube Downloader. Tudo aqui é Python.

```
ytdownloader/
├── core/     regras de negócio — não importa nada do Qt
├── gui/      interface em PySide6
└── app.py    inicialização
```

## A divisão entre core e gui

`core/` não conhece a interface. Não importa PySide6, não sabe que existe uma
janela, e funciona igual se um dia for chamado por uma linha de comando ou por
outra interface gráfica.

Isso não é purismo arquitetural: é o que permite rodar os 142 testes sem abrir
uma única janela, e é por isso que a suíte roda em segundos dentro da
integração contínua.

A regra prática para quem for mexer: se o código precisa saber que existe um
botão, ele pertence a `gui/`. Se resolve o que fazer com um vídeo, pertence a
`core/`.

## O que cada módulo faz

**`core/downloader.py`** — a camada sobre o yt-dlp. Monta as opções, acompanha
o progresso e descobre onde o arquivo final foi parar. É o único lugar que
conversa com o yt-dlp diretamente.

**`core/formats.py`** — o catálogo de qualidades e os seletores de formato. Toda
opção nova de download passa por aqui, nunca direto no dicionário do yt-dlp.

**`core/urls.py`** — valida e normaliza o endereço colado. Aceita qualquer
`http`/`https`, com tratamento próprio para o YouTube, e recusa esquemas como
`file://` e `javascript:`.

**`core/errors.py`** — traduz a saída crua do yt-dlp para mensagens que fazem
sentido para quem não programa. "Sign in to confirm you're not a bot" vira uma
frase que explica o problema e o que fazer.

**`core/updater.py`** — baixa novas versões do yt-dlp do PyPI e as coloca no
`sys.path`. É o único componente que executa código obtido em tempo de execução,
e por isso concentra as verificações de segurança: SHA-256, recusa de caminhos
que escapem da pasta de destino e limite de tamanho.

**`core/ffmpeg.py`**, **`core/jsruntime.py`** — localizam os binários externos:
o FFmpeg embutido no instalador e o interpretador JavaScript, se houver algum.

**`core/settings.py`**, **`core/history.py`**, **`core/paths.py`** — preferências,
histórico e os diretórios que o aplicativo usa.

**`gui/main_window.py`** — a janela. Junta os componentes e coordena a fila.

**`gui/workers.py`** — todo trabalho demorado passa por aqui. Nada que demore
roda na thread da interface; o resultado volta por sinais do Qt.

**`gui/i18n.py`** — a tradução. As strings do código são escritas em português e
servem de chave; o inglês vem de um catálogo em `resources/i18n`.

**`gui/theme.py`** — os temas claro e escuro, em folha de estilo do Qt.

## Rodando a partir daqui

```powershell
$env:PYTHONPATH = "codigo-fonte"
python -m ytdownloader
```

O passo a passo completo, com dependências e ferramentas, está no
[README do projeto](../README.pt-BR.md#desenvolvimento).
