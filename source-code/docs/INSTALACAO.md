<div align="center">

# Baixar o programa

### [⬇️ YouTubeDownloader-1.2.0-Setup.msi](../../YouTubeDownloader-1.2.0-Setup.msi)

*96 MB · Windows 10 ou 11 de 64 bits*

</div>

---

O instalador está nesta pasta, logo acima. Clique no nome dele e depois no botão
**Download**, no canto direito da página.

Ele também está na
[página de releases](https://github.com/victorhuggomed2006-ux/YoutubeDownloader/releases/latest),
que é onde ficam as versões anteriores.

## Como instalar

1. Baixe o arquivo
2. Dê dois cliques nele
3. Escolha se quer o atalho na Área de Trabalho
4. Conclua

Pronto. Não pede permissão de administrador e não exige instalar Python, FFmpeg
nem qualquer outra coisa — está tudo dentro do instalador.

## Onde o programa é instalado

Em `%LOCALAPPDATA%\Programs\YouTube Downloader`, a pasta que o Windows reserva
para programas de um único usuário. É o mesmo lugar em que Chrome, Discord e
Spotify se instalam.

Não é `C:\Program Files` por um motivo técnico: gravar ali exige privilégio de
administrador, sem exceção. Um instalador que não pede nada é, necessariamente,
um instalador que não escreve em Arquivos de Programas.

## Para desinstalar

**Configurações → Aplicativos → Aplicativos instalados**, procure por *YouTube
Downloader* e clique em Desinstalar. Nenhuma permissão especial é necessária.

Suas configurações e o histórico ficam em `%APPDATA%\YouTubeDownloader` e não
são apagados junto — remova essa pasta à mão se quiser limpar tudo.

## Sobre o aviso do Windows

O instalador ainda não tem assinatura digital, então o SmartScreen mostra
*"O Windows protegeu o seu computador"*. Clique em **Mais informações** e depois
em **Executar assim mesmo**.

Isso acontece com qualquer programa não assinado, e o certificado que remove o
aviso custa algumas centenas de dólares por ano. O código-fonte está aberto
neste repositório e pode ser compilado por você, se preferir não confiar no
binário. O plano para resolver isso está em [ASSINATURA.md](ASSINATURA.md).

---

## Documentação

- **[Página principal do projeto](../README.pt-BR.md)** — o que o programa faz, recursos, limitações
- **[Código-fonte](..)** — a implementação
- **[Como compilar](../README.pt-BR.md#compilando-o-projeto)** — gerar o instalador por conta própria
