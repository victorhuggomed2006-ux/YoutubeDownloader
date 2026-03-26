# YouTube Downloader

Aplicação web para baixar vídeos e áudios do YouTube. Interface simples, funcional e responsiva.

## Funcionalidades

- Baixa vídeos em várias qualidades (360p até 4K)
- Extrai áudio em MP3 (192kbps)
- Tema claro/escuro automático
- Valida URLs do YouTube em tempo real
- Proteção contra CSRF e rate limiting
- Dashboard com estatísticas de downloads
- Funciona offline com PWA
- Cancelamento de download
- Logging estruturado com histórico em JSON

## Começando

### Pré-requisitos

- Python 3.8+
- FFmpeg (para converter para MP3)

### Instalação

Clonar ou extrair o projeto:

```bash
cd "Youtube Download"
```

Criar um ambiente virtual (recomendado):

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # macOS/Linux
```

Instalar as dependências:

```bash
pip install -r requirements.txt
```

### Configuração

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

Edite `.env` se precisar customizar:

```env
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=False
PORT=5000
MAX_FILE_SIZE_MB=1200
ADMIN_TOKEN=seu-token-admin
```

### Executar

```bash
python app.py
```

Abra http://localhost:5000 no navegador.

## Como usar

1. Cole a URL do YouTube no campo
   - A validação acontece enquanto você digita
   - As informações do vídeo carregam automaticamente

2. Escolha o formato
   - MP4 (vídeo)
   - MP3 (áudio)

3. Para vídeo, selecione a qualidade
   - Máxima
   - 1080p
   - 720p
   - 480p
   - 360p

4. Inicie o download
   - Clique no botão ou pressione Enter
   - Acompanhe o progresso
   - Pode cancelar a qualquer momento

## Statisticas

Acesse o histórico de downloads em:

http://localhost:5000/stats

Ou com token para produção:

http://localhost:5000/stats?token=seu-admin-token

Mostra informações sobre cada download: status, formato, URL, tamanho e data.

## Configuração

### Variáveis de ambiente

| Variável | Padrão | O que faz |
|----------|--------|----------|
| SECRET_KEY | dev-key | Chave para segurança (mude em produção) |
| DEBUG | False | Modo debug |
| HOST | 0.0.0.0 | Endereço para bind |
| PORT | 5000 | Porta do servidor |
| MAX_FILE_SIZE_MB | 1200 | Tamanho máximo em MB |
| ADMIN_TOKEN | - | Token para acessar stats em produção |
| FFMPEG_PATH | auto | Caminho customizado para FFmpeg |

### Rate limiting

Por padrão está limitado a 3 downloads por minuto e 60 requisições por minuto no geral.

Para mudar, edite em `app.py`:

```python
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["60 per minute"],  # Alterar aqui
)
```

## Segurança

- CSRF protection (flask-wtf)
- Rate limiting
- Security headers padronizados
- Validação de URL no cliente e servidor
- Limite de tamanho de arquivo
- Limpeza automática de arquivos temporários

## Logs

Os downloads são registrados em `download.log`:

```
[2026-03-24 14:30:25] INFO - download:185 - Download bem-sucedido: mp4 720p (245MB) de 192.168.1.100
[2026-03-24 14:35:10] ERROR - download:220 - Erro no download: Vídeo privado
```

## Histórico

Os downloads são salvos em `stats.json` com timestamp, URL, formato, qualidade, status, tamanho e IP.

## PWA e offline

- Manifesto PWA em `/static/manifest.json`
- Service Worker com cache
- Página offline em `/offline.html`

## Observações

- FFmpeg é necessário para converter para MP3. Se não estiver instalado, o app tenta usar o M4A
- Respeite os termos de serviço do YouTube
- Playlists estão desabilitadas por padrão
- Para atualizar o yt-dlp, use: `pip install --upgrade yt-dlp`

## Problemas comuns

### FFmpeg não encontrado

Instale FFmpeg:

Windows (Chocolatey):
```powershell
choco install ffmpeg
```

macOS (Homebrew):
```bash
brew install ffmpeg
```

Linux (Ubuntu/Debian):
```bash
sudo apt-get install ffmpeg
```

### Vídeo não faz download

- Pode ser privado ou restrito
- Pode estar bloqueado por região
- Pode exigir verificação de idade
- Tente outra URL

## IMPORTANTE: Limitação de Servidor

### YouTube bloqueia downloads de servidores

YouTube detecta e bloqueia automaticamente requisições de IPs datacenter (como Vercel, Heroku, etc.) com desafios "Faça login para confirmar que você não é um robô".

**Solução implementada:**
- ✅ **Previews funcionam** no Vercel (usando cache + Invidious)
- ⏩ **Downloads redirecionam** para Invidious (proxy seguro do YouTube)
- ✅ **Funciona 100% localmente** sem nenhuma limitação

### Modo Vercel (Online)

O app detecta se está rodando no Vercel e:
1. **Previews** - Carrega imagens/info via Invidious
2. **Downloads** - Redireciona para https://inv.nadeko.net (proxy seguro)

Você pode usar o app remotamente, mas os downloads abrem em Invidious (que permite download direto).

### Para usar sem limitações (Recomendado)

Execute localmente em sua máquina:

```bash
git clone https://github.com/victorhuggomed2006-ux/YoutubeDownloader
cd YoutubeDownloader
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py
```

Depois acesse: **http://localhost:5000**

Downloads funcionam normalmente, sem redirecionamentos.

### Por que YouTube bloqueia?

YouTube implementa proteção anti-bot que:
1. Detecta requisições de IPs datacenter
2. Solicita verificação humana
3. Bloqueia automaticamente tools de download

Isso é uma limitação do YouTube, não do nosso app. Mesmo soluções profissionais (como yt-dlp, youtube-dl) têm este problema em servidores.

## Planos futuros

- Suporte a playlists
- Download paralelo de múltiplos vídeos
- Interface para processar vídeos locais
- Autenticação para o dashboard
- Histórico local no navegador
- Dark mode persistente

---

Projeto educacional, feito em Flask e JavaScript vanilla.
