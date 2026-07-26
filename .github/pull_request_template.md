<!--
Write in English or Portuguese — both work.
Escreva em inglês ou português, tanto faz.
-->

## What changed and why / O que mudou e por quê

<!--
The "why" matters more than the "what" — the diff already shows what changed.
O "porquê" importa mais que o "o quê" — o diff já mostra o que mudou.
-->

## How was it verified / Como foi verificado

<!--
Tests, manual steps, the video you tried it on.
Testes, passos manuais, o vídeo em que você testou.
-->

## Checklist

- [ ] `pytest` passes / passa
- [ ] `ruff check .` and `ruff format --check .` pass / passam
- [ ] New user-facing strings are wrapped in `tr()` and the `.ts` was updated
      (`packaging/build_translations.ps1`) / Strings novas visíveis ao usuário
      estão em `tr()` e o `.ts` foi atualizado
- [ ] Business logic went into `core/` (no Qt imports there) / Lógica de negócio
      foi para `core/` (sem importar Qt lá)
- [ ] `CHANGELOG.md` updated, if the change is user-visible / atualizado, se a
      mudança é visível para quem usa
