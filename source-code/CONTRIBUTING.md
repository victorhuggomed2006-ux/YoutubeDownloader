# Contributing

*[Versão em português abaixo](#contribuindo)*

Contributions are welcome — bug reports, translations, features, or just telling
us a site does not work.

## Getting set up

```powershell
git clone https://github.com/victorhuggomed2006-ux/YoutubeDownloader
cd YoutubeDownloader

python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt

powershell -ExecutionPolicy Bypass -File packaging\fetch_ffmpeg.ps1
python packaging\make_icon.py
powershell -ExecutionPolicy Bypass -File packaging\build_translations.ps1

cd source-code
python -m ytdownloader
```

## Before opening a pull request

```powershell
pytest
ruff check .
ruff format --check .
```

CI runs the same three commands, so a green local run usually means a green PR.

## How the code is organised

The project draws a hard line between business rules and interface:

- **`source-code/ytdownloader/core/`** — imports nothing from Qt. All download logic,
  validation, formats and persistence live here, and are testable without
  opening a window.
- **`source-code/ytdownloader/gui/`** — interface only. It talks to the core through
  callbacks and Qt signals.

Please keep that line. It is what lets the test suite verify real behaviour
without a display, and what keeps the core reusable.

## Conventions

**Language.** Code, comments and docstrings are written in Portuguese, matching
the rest of the project. User-facing strings are also written in Portuguese —
they are the translation keys — and English is provided as a translation. If you
are more comfortable writing in English, do it and say so in the PR; we would
rather have your contribution than a perfect linguistic match.

**Error messages** are written for people who do not program. Translate yt-dlp's
raw output in `core/errors.py` instead of passing it through.

**New user-facing strings** must be wrapped in `self.tr(...)`. After adding
them, run `packaging\build_translations.ps1` and fill in the English in
`source-code/ytdownloader/resources/i18n/ytdownloader_en.ts` — with Qt Linguist
(`pyside6-linguist`) or any text editor.

Messages that originate in `core/` cannot call `tr()` — the core has no Qt. Add
them to `_declarar_mensagens_do_nucleo` in `gui/i18n.py` so the extraction tool
finds them.

**Long-running work** never runs on the UI thread. Use the workers in
`gui/workers.py`.

**New download options** go through `core/formats.py`, not straight into the
yt-dlp dictionary.

## Adding a language

1. Copy `source-code/ytdownloader/resources/i18n/ytdownloader_en.ts` to
   `ytdownloader_<code>.ts` (for example `ytdownloader_es.ts`)
2. Add the code to `IDIOMAS` in `source-code/ytdownloader/gui/i18n.py`
3. Run `packaging\build_translations.ps1`
4. Translate the entries and run the script again

Watch out for plural forms: `%n` messages need every form your language uses,
which may be more than two.

## Reporting a problem

Open an issue with:

- what you were doing and what happened
- the version from the About window
- the relevant part of `%APPDATA%\YouTubeDownloader\ytdownloader.log`
- the video link, if it is specific to one video

For security issues, do not open a public issue — see [SECURITY.md](SECURITY.md).

## Licence

By contributing, you agree your contribution is distributed under the project's
[MIT licence](LICENSE).

---

# Contribuindo

Contribuições são bem-vindas — relatos de problema, traduções, funcionalidades,
ou simplesmente avisar que um site não funciona.

## Preparando o ambiente

```powershell
git clone https://github.com/victorhuggomed2006-ux/YoutubeDownloader
cd YoutubeDownloader

python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt

powershell -ExecutionPolicy Bypass -File packaging\fetch_ffmpeg.ps1
python packaging\make_icon.py
powershell -ExecutionPolicy Bypass -File packaging\build_translations.ps1

cd source-code
python -m ytdownloader
```

## Antes de abrir um pull request

```powershell
pytest
ruff check .
ruff format --check .
```

A CI roda os mesmos três comandos, então um resultado verde localmente costuma
significar um PR verde.

## Como o código é organizado

O projeto traça uma linha rígida entre regra de negócio e interface:

- **`source-code/ytdownloader/core/`** — não importa nada do Qt. Toda a lógica de
  download, validação, formatos e persistência mora aqui, e é testável sem abrir
  janela.
- **`source-code/ytdownloader/gui/`** — só interface. Conversa com o núcleo por
  callbacks e sinais do Qt.

Mantenha essa linha. É o que permite à suíte de testes verificar comportamento
real sem display, e o que mantém o núcleo reaproveitável.

## Convenções

**Idioma.** Código, comentários e docstrings são escritos em português, como o
resto do projeto. As strings visíveis ao usuário também são escritas em
português — elas são as chaves de tradução — e o inglês vem como tradução. Se
você se sente mais confortável escrevendo em inglês, escreva e avise no PR:
preferimos sua contribuição a uma combinação linguística perfeita.

**Mensagens de erro** são escritas para quem não programa. Traduza a saída crua
do yt-dlp em `core/errors.py` em vez de repassá-la.

**Strings novas visíveis ao usuário** devem estar dentro de `self.tr(...)`.
Depois de adicioná-las, rode `packaging\build_translations.ps1` e preencha o
inglês em `source-code/ytdownloader/resources/i18n/ytdownloader_en.ts` — com o Qt
Linguist (`pyside6-linguist`) ou qualquer editor de texto.

Mensagens que nascem em `core/` não podem chamar `tr()` — o núcleo não tem Qt.
Adicione-as a `_declarar_mensagens_do_nucleo`, em `gui/i18n.py`, para que a
ferramenta de extração as encontre.

**Trabalho demorado** nunca roda na thread da interface. Use os workers de
`gui/workers.py`.

**Opções novas de download** passam por `core/formats.py`, não direto no
dicionário do yt-dlp.

## Adicionando um idioma

1. Copie `source-code/ytdownloader/resources/i18n/ytdownloader_en.ts` para
   `ytdownloader_<código>.ts` (por exemplo, `ytdownloader_es.ts`)
2. Adicione o código a `IDIOMAS`, em `source-code/ytdownloader/gui/i18n.py`
3. Rode `packaging\build_translations.ps1`
4. Traduza as entradas e rode o script de novo

Atenção às formas de plural: mensagens com `%n` precisam de todas as formas que
seu idioma usa, que podem ser mais de duas.

## Relatando um problema

Abra uma issue com:

- o que você estava fazendo e o que aconteceu
- a versão mostrada na janela Sobre
- o trecho relevante de `%APPDATA%\YouTubeDownloader\ytdownloader.log`
- o link do vídeo, se o problema for específico de um vídeo

Para questões de segurança, não abra issue pública — veja [SECURITY.md](SECURITY.md).

## Licença

Ao contribuir, você concorda que sua contribuição será distribuída sob a
[licença MIT](LICENSE) do projeto.
