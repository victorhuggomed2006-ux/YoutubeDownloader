"""Testes de persistência de configurações e histórico."""

from __future__ import annotations

import json
from pathlib import Path

from ytdownloader.core.formats import MediaKind
from ytdownloader.core.history import HistoryStore
from ytdownloader.core.models import (
    DownloadRequest,
    DownloadTask,
    HistoryEntry,
    TaskStatus,
)
from ytdownloader.core.settings import Settings, SettingsStore

# ── Configurações ────────────────────────────────────────────────────────


def test_usa_padroes_quando_nao_ha_arquivo(tmp_path: Path) -> None:
    store = SettingsStore(path=tmp_path / "settings.json")
    assert store.settings.theme == "dark"
    assert store.settings.video_quality == "1080p"


def test_grava_e_recarrega(tmp_path: Path) -> None:
    caminho = tmp_path / "settings.json"
    store = SettingsStore(path=caminho)
    store.update(theme="light", video_quality="720p")

    recarregado = SettingsStore(path=caminho)
    assert recarregado.settings.theme == "light"
    assert recarregado.settings.video_quality == "720p"


def test_ignora_campos_desconhecidos(tmp_path: Path) -> None:
    """Um arquivo de versão futura não pode derrubar o aplicativo."""
    caminho = tmp_path / "settings.json"
    caminho.write_text(json.dumps({"theme": "light", "opcao_que_nao_existe": 42}), encoding="utf-8")
    store = SettingsStore(path=caminho)
    assert store.settings.theme == "light"


def test_arquivo_corrompido_cai_nos_padroes(tmp_path: Path) -> None:
    caminho = tmp_path / "settings.json"
    caminho.write_text("{isso não é json", encoding="utf-8")
    assert SettingsStore(path=caminho).settings.theme == "dark"


def test_pasta_de_destino_tem_valor_util_quando_vazia() -> None:
    assert Settings().resolved_output_dir().name


def test_reset_volta_aos_padroes(tmp_path: Path) -> None:
    store = SettingsStore(path=tmp_path / "settings.json")
    store.update(theme="light")
    store.reset()
    assert store.settings.theme == "dark"


# ── Histórico ────────────────────────────────────────────────────────────


def _entrada(titulo: str = "Vídeo de teste") -> HistoryEntry:
    return HistoryEntry(
        title=titulo,
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        kind="video",
        quality="1080p",
        container="mp4",
        status="completed",
        size_bytes=1024,
    )


def test_historico_guarda_do_mais_novo_para_o_mais_antigo(tmp_path: Path) -> None:
    store = HistoryStore(path=tmp_path / "history.json")
    store.add(_entrada("primeiro"))
    store.add(_entrada("segundo"))

    titulos = [e.title for e in store.entries()]
    assert titulos == ["segundo", "primeiro"]


def test_historico_persiste_entre_sessoes(tmp_path: Path) -> None:
    caminho = tmp_path / "history.json"
    HistoryStore(path=caminho).add(_entrada("gravado"))
    assert [e.title for e in HistoryStore(path=caminho).entries()] == ["gravado"]


def test_historico_respeita_o_limite(tmp_path: Path) -> None:
    store = HistoryStore(path=tmp_path / "history.json", max_entries=3)
    for i in range(10):
        store.add(_entrada(f"item {i}"))

    entradas = store.entries()
    assert len(entradas) == 3
    assert entradas[0].title == "item 9"


def test_historico_limpa(tmp_path: Path) -> None:
    store = HistoryStore(path=tmp_path / "history.json")
    store.add(_entrada())
    store.clear()
    assert store.entries() == []


def test_historico_ignora_arquivo_invalido(tmp_path: Path) -> None:
    caminho = tmp_path / "history.json"
    caminho.write_text('{"não": "é uma lista"}', encoding="utf-8")
    assert HistoryStore(path=caminho).entries() == []


def test_entrada_a_partir_de_tarefa_concluida(tmp_path: Path) -> None:
    arquivo = tmp_path / "video.mp4"
    arquivo.write_bytes(b"x" * 2048)

    task = DownloadTask(
        request=DownloadRequest(
            url="https://youtu.be/dQw4w9WgXcQ",
            kind=MediaKind.VIDEO,
            quality="720p",
            container="mp4",
            output_dir=tmp_path,
        ),
        status=TaskStatus.COMPLETED,
        output_file=arquivo,
    )

    entrada = HistoryEntry.from_task(task)
    assert entrada.status == "completed"
    assert entrada.size_bytes == 2048
    assert entrada.file_path == str(arquivo)


def test_entrada_ida_e_volta_em_dicionario() -> None:
    original = _entrada()
    assert HistoryEntry.from_dict(original.to_dict()) == original
