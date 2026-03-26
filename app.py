from flask import Flask, render_template, request, send_file, redirect, url_for, flash, jsonify, abort
from flask_compress import Compress
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import tempfile
import shutil
import os
import json
import threading
import logging
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse
from yt_dlp import YoutubeDL, DownloadError
from collections import deque
import imageio_ffmpeg


class DownloadCancelledError(Exception):
    pass

# Load .env
load_dotenv()

# ─── App Setup ───
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB for POST body
app.config['WTF_CSRF_TIME_LIMIT'] = None  # CSRF tokens won't expire
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# ─── Compression ───
Compress(app)

# ─── Security: CSRF ───
csrf = CSRFProtect(app)

# ─── Security: Rate Limiting ───
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["60 per minute"],
    storage_uri="memory://",
)

# ─── Constants ───
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE_MB', 1200)) * 1024 * 1024
ALLOWED_FORMATS = {'mp4', 'mp3'}
ALLOWED_QUALITIES = {'best', '1080p', '720p', '480p', '360p'}
DOWNLOAD_STATS = deque(maxlen=50)
STATS_FILE = os.path.join('/tmp', 'stats.json')
DOWNLOAD_ACTIVE = {}  # Track active downloads for cancellation
DOWNLOAD_PROGRESS = {} # Track real-time progress

DOWN_DIR = os.path.join('/tmp', 'yt_downloads')
os.makedirs(DOWN_DIR, exist_ok=True)

try:
    FFMPEG_EXE = os.getenv('FFMPEG_PATH') or imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    FFMPEG_EXE = 'ffmpeg'  # fallback para ffmpeg no PATH

# ─── Logging ───
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
try:
    log_file = os.path.join('/tmp', 'download.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except Exception:
    pass
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Load stats from JSON on startup
def load_stats():
    global DOWNLOAD_STATS
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                DOWNLOAD_STATS = deque(data[-50:], maxlen=50)
                logger.info(f'Carregados {len(DOWNLOAD_STATS)} registros de stats')
        except Exception as e:
            logger.error(f'Erro ao carregar stats: {e}')

def save_stats():
    try:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(DOWNLOAD_STATS), f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f'Erro ao salvar stats: {e}')

load_stats()


# ─── Security Headers ───
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    return response


# ─── Background cleanup ───
def cleanup_old_tempdirs():
    while True:
        try:
            now = time.time()
            for d in os.listdir(DOWN_DIR):
                path = os.path.join(DOWN_DIR, d)
                if os.path.isdir(path):
                    if now - os.path.getmtime(path) > 3600:
                        shutil.rmtree(path, ignore_errors=True)
                        logger.info(f'Limpeza: removido diretório temporário {path}')
        except Exception as e:
            logger.error(f'Erro na limpeza: {e}')
        time.sleep(3600)

# Apenas inicia thread de limpeza fora de ambiente serverless
if os.getenv('VERCEL') is None:
    threading.Thread(target=cleanup_old_tempdirs, daemon=True).start()


# ─── Helpers ───
def validate_youtube_url(url):
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    if parsed.scheme not in ('http', 'https'):
        return False
    host = (parsed.hostname or '').lower()
    return host.endswith('youtube.com') or host.endswith('youtu.be') or host.endswith('youtube-nocookie.com')

def can_access_stats(req):
    token = req.args.get('token')
    admin_token = os.getenv('ADMIN_TOKEN', '').strip()
    is_local = req.remote_addr in ('127.0.0.1', '::1')
    is_admin = bool(admin_token) and token == admin_token
    return is_local or is_admin


def format_duration(seconds):
    if not seconds:
        return None
    total = int(seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h:
        return f'{h:02d}:{m:02d}:{s:02d}'
    return f'{m:02d}:{s:02d}'


def get_ydl_common_opts():
    """Opções comuns para yt-dlp com headers para contornar verificação de bot"""
    return {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        },
        'socket_timeout': 30,
        'retries': 3,
    }


# ─── Routes ───
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/download/cancel', methods=['POST'])
@csrf.exempt
def cancel_download():
    """Endpoint para cancelar download em andamento"""
    ip = request.remote_addr
    if ip in DOWNLOAD_ACTIVE:
        DOWNLOAD_ACTIVE[ip] = True
        logger.info(f'Download cancelado pelo cliente: {ip}')
        return jsonify({'status': 'cancelled'}), 200
    return jsonify({'status': 'no_active_download'}), 204


@app.route('/api/preview', methods=['GET'])
@csrf.exempt
@limiter.limit("20 per minute")
def preview_video_info():
    url = request.args.get('url', '').strip()
    if not url or not validate_youtube_url(url):
        return jsonify({'error': 'URL inválida'}), 400

    opts = get_ydl_common_opts()
    opts['skip_download'] = True

    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return jsonify({
            'title': info.get('title') or 'Sem título',
            'thumbnail': info.get('thumbnail') or '',
            'duration': info.get('duration') or 0,
            'duration_label': format_duration(info.get('duration')),
            'uploader': info.get('uploader') or 'Canal desconhecido',
        })
    except DownloadError:
        return jsonify({'error': 'Não foi possível carregar os dados do vídeo'}), 422


@app.route('/stats', methods=['GET'])
def stats():
    if not can_access_stats(request):
        abort(403)
    return render_template('stats.html', stats=list(DOWNLOAD_STATS))


@app.route('/stats/json', methods=['GET'])
@csrf.exempt
def stats_json():
    if not can_access_stats(request):
        abort(403)
    return jsonify(list(DOWNLOAD_STATS))


@app.route('/offline.html', methods=['GET'])
def offline():
    return render_template('offline.html')

@app.route('/api/progress', methods=['GET'])
@csrf.exempt
def get_progress():
    """Retorna a porcentagem atual de um download"""
    dl_id = request.args.get('id')
    data = DOWNLOAD_PROGRESS.get(dl_id, {'status': 'waiting', 'percent': 0})
    return jsonify(data)

@app.route('/download', methods=['POST'])
@limiter.limit("3 per minute")
def download():
    url = request.form.get('url', '').strip()
    fmt = request.form.get('format', 'mp4')
    quality = request.form.get('quality', 'best')

    # ─── Input validation ───
    if fmt not in ALLOWED_FORMATS:
        fmt = 'mp4'
    if quality not in ALLOWED_QUALITIES:
        quality = 'best'

    if not url:
        flash('Por favor informe a URL do YouTube.')
        return redirect(url_for('index'))

    if not validate_youtube_url(url):
        flash('URL inválida. Insira um link válido do YouTube.')
        return redirect(url_for('index'))

    tmpdir = tempfile.mkdtemp(dir=DOWN_DIR, prefix='ydl_')

    if fmt == 'mp3':
        ydl_opts = get_ydl_common_opts()
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
            'ffmpeg_location': FFMPEG_EXE,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        })
        wanted = ['.mp3']
    else:
        quality_map = {
            'best':  'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '1080p': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best',
            '720p':  'bestvideo[ext=mp4][height<=720]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]/best',
            '480p':  'bestvideo[ext=mp4][height<=480]+bestaudio[ext=m4a]/best[ext=mp4][height<=480]/best',
            '360p':  'bestvideo[ext=mp4][height<=360]+bestaudio[ext=m4a]/best[ext=mp4][height<=360]/best',
        }
        fmt_string = quality_map.get(quality, quality_map['best'])

        ydl_opts = get_ydl_common_opts()
        ydl_opts.update({
            'format': fmt_string,
            'merge_output_format': 'mp4',
            'outtmpl': os.path.join(tmpdir, '%(title)s.%(ext)s'),
            'ffmpeg_location': FFMPEG_EXE,
        })
        wanted = ['.mp4']

    try:
        client_id = request.form.get('download_id') or request.remote_addr or 'unknown'
        DOWNLOAD_ACTIVE[client_id] = False
        DOWNLOAD_PROGRESS[client_id] = {'status': 'starting', 'percent': 0}

        def ensure_not_cancelled():
            if DOWNLOAD_ACTIVE.get(client_id):
                raise DownloadCancelledError('Download cancelado pelo usuário.')

        # O gancho que lê os dados reais do yt-dlp
        def hook(d):
            ensure_not_cancelled()
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percent = (downloaded / total) * 100
                    DOWNLOAD_PROGRESS[client_id] = {'status': 'downloading', 'percent': percent}
            elif d['status'] == 'finished':
                DOWNLOAD_PROGRESS[client_id] = {'status': 'processing', 'percent': 100}

        ydl_opts['progress_hooks'] = [hook]
        
        with YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except DownloadError as e:
                err_msg = str(e).lower()
                if 'private' in err_msg or 'not available' in err_msg:
                    raise ValueError('Vídeo é privado, restrito ou foi removido.')
                elif 'age' in err_msg:
                    raise ValueError('Vídeo requer verificação de idade.')
                else:
                    raise ValueError(f'Erro ao obter informações: {str(e)[:100]}')
            except Exception as e:
                logger.exception(f'Falha ao extrair info de {url}')
                raise ValueError('Erro ao extrair informações do vídeo')

            size = 0
            try:
                size = info.get('filesize') or info.get('filesize_approx') or 0
            except Exception:
                size = 0
            
            if size and size > MAX_FILE_SIZE:
                raise ValueError(f"Arquivo muito grande ({size//(1024*1024)}MB). Máximo: {MAX_FILE_SIZE//(1024*1024)}MB")

            logger.info(f'Iniciando download: {fmt} {quality} - {size//1024}KB')
            ensure_not_cancelled()
            ydl.download([url])

            created_files = []
            for root, _, files in os.walk(tmpdir):
                for f in files:
                    created_files.append(os.path.join(root, f))
            
            logger.info(f'Arquivos gerados: {len(created_files)}: {", ".join([os.path.basename(f) for f in created_files])}')
            if not created_files:
                raise RuntimeError('yt-dlp não gerou arquivos')

        record = {
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'url': url[:100],
            'format': fmt,
            'quality': quality,
            'status': 'success',
            'size_bytes': size,
            'client_ip': request.remote_addr,
        }
        DOWNLOAD_STATS.appendleft(record)
        save_stats()
        logger.info(f'✓ Download bem-sucedido: {fmt} {quality} ({size//(1024*1024)}MB) de {request.remote_addr}')

    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        error_msg = str(e)
        if isinstance(e, DownloadCancelledError):
            flash('Download cancelado com sucesso.')
        else:
            flash(f'❌ Erro: {error_msg}')
        record = {
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'url': url[:100],
            'format': fmt,
            'quality': quality,
            'status': 'cancelled' if isinstance(e, DownloadCancelledError) else 'error',
            'error': error_msg[:200],
            'client_ip': request.remote_addr,
        }
        DOWNLOAD_STATS.appendleft(record)
        save_stats()
        logger.error(f'✗ Download falhou: {error_msg[:150]} - {request.remote_addr}')
        return redirect(url_for('index'))
    finally:
        DOWNLOAD_ACTIVE.pop(client_id, None)
        DOWNLOAD_PROGRESS.pop(client_id, None)

    # --- Nível 1: Captura Cirúrgica ---
    # Como tmpdir é exclusivo desta requisição, pegamos o único arquivo de mídia que sobrou.
    out_file = None
    
    if os.path.exists(tmpdir):
        for file in os.listdir(tmpdir):
            if file.endswith(('.mp4', '.mp3', '.mkv', '.webm', '.m4a')):
                out_file = os.path.join(tmpdir, file)
                break

    if not out_file:
        arquivos_restantes = os.listdir(tmpdir) if os.path.exists(tmpdir) else []
        logger.error(f'Arquivo de saída não encontrado em {tmpdir}. Sobrou: {arquivos_restantes}')
        shutil.rmtree(tmpdir, ignore_errors=True)
        flash('Não foi possível encontrar o arquivo gerado. Tente novamente.')
        return redirect(url_for('index'))

    # --- Nível 2: Sanitização do Nome do Arquivo ---
    raw_filename = os.path.basename(out_file)
    # Remove caracteres que quebram o download no Windows/Navegadores: \ / : * ? " < > |
    safe_filename = re.sub(r'[\\/*?:"<>|]', "", raw_filename)
    # Remove espaços múltiplos
    safe_filename = re.sub(r'\s+', " ", safe_filename).strip()

    return send_file(out_file, as_attachment=True, download_name=safe_filename)


# ─── Error handlers ───
@app.errorhandler(429)
def ratelimit_handler(e):
    flash('⏱️ Muitas requisições. Aguarde um momento antes de tentar novamente.')
    return redirect(url_for('index'))

@app.errorhandler(403)
def forbidden_handler(e):
    flash('Acesso negado para este recurso.')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_handler(e):
    return redirect(url_for('index'))


if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    app.run(debug=DEBUG, host=host, port=port)
