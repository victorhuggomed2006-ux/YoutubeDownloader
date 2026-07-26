"""Testes da atualização do yt-dlp.

Este é o módulo mais sensível do projeto: ele baixa um pacote da internet e o
coloca no ``sys.path``, de onde o código será importado e executado. Os testes
aqui existem sobretudo para garantir que as defesas continuem no lugar.
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path

import pytest

from ytdownloader.core import paths, updater


@pytest.fixture(autouse=True)
def pasta_isolada(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Mantém a pasta real do usuário fora dos testes."""
    destino = tmp_path / "runtime"
    destino.mkdir()
    monkeypatch.setattr(paths, "runtime_dir", lambda: destino)
    return destino


def _wheel(arquivos: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        for nome, conteudo in arquivos.items():
            z.writestr(nome, conteudo)
    return buffer.getvalue()


def _wheel_valido() -> bytes:
    return _wheel(
        {
            "yt_dlp/__init__.py": "__version__ = '2030.1.1'\n",
            "yt_dlp/version.py": "__version__ = '2030.1.1'\n",
        }
    )


class _RespostaFalsa:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def iter_content(self, chunk_size: int = 8192):
        for i in range(0, len(self._payload), chunk_size):
            yield self._payload[i : i + chunk_size]


def _fingir_download(monkeypatch: pytest.MonkeyPatch, payload: bytes) -> None:
    import requests

    monkeypatch.setattr(requests, "get", lambda *a, **k: _RespostaFalsa(payload))


# ── Comparação de versões ────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("2026.7.4", (2026, 7, 4)),
        ("2026.07.04", (2026, 7, 4)),
        ("1.0", (1, 0)),
        ("", (0,)),
        ("nao-e-versao", (0,)),
    ],
)
def test_interpreta_versoes(texto: str, esperado: tuple) -> None:
    assert updater.parse_version(texto) == esperado


def test_ordem_das_versoes_e_numerica_nao_alfabetica() -> None:
    """Comparado como texto, "2026.10.1" viria antes de "2026.9.1"."""
    assert updater.parse_version("2026.10.1") > updater.parse_version("2026.9.1")
    assert updater.parse_version("2027.1.1") > updater.parse_version("2026.12.31")


# ── Instalação ───────────────────────────────────────────────────────────


def test_instala_e_deixa_o_pacote_utilizavel(
    monkeypatch: pytest.MonkeyPatch, pasta_isolada: Path
) -> None:
    payload = _wheel_valido()
    _fingir_download(monkeypatch, payload)
    digest = hashlib.sha256(payload).hexdigest()

    destino = updater.install("2030.1.1", "https://exemplo/pacote.whl", digest)

    assert destino.is_dir()
    assert (destino / "yt_dlp" / "__init__.py").is_file()
    assert destino.parent == pasta_isolada


def test_recusa_pacote_com_soma_de_verificacao_errada(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sem esta checagem, qualquer coisa devolvida pela rede seria importada."""
    _fingir_download(monkeypatch, _wheel_valido())

    with pytest.raises(RuntimeError, match="integridade"):
        updater.install("2030.1.1", "https://exemplo/pacote.whl", "0" * 64)


def test_recusa_pacote_que_escapa_da_pasta_de_destino(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Zip Slip: um arquivo com '..' no caminho sobrescreveria arquivos fora da
    pasta de destino — inclusive o próprio executável do aplicativo."""
    malicioso = _wheel(
        {
            "yt_dlp/__init__.py": "",
            "../../../evil.py": "print('invasao')",
        }
    )
    _fingir_download(monkeypatch, malicioso)

    with pytest.raises(RuntimeError, match="caminhos inválidos"):
        updater.install("2030.1.1", "https://exemplo/pacote.whl", "")

    assert not (tmp_path.parent / "evil.py").exists()


def test_recusa_pacote_sem_o_ytdlp_dentro(monkeypatch: pytest.MonkeyPatch) -> None:
    _fingir_download(monkeypatch, _wheel({"outra_coisa/__init__.py": ""}))

    with pytest.raises(RuntimeError, match="não contém o yt-dlp"):
        updater.install("2030.1.1", "https://exemplo/pacote.whl", "")


def test_recusa_pacote_grande_demais(monkeypatch: pytest.MonkeyPatch) -> None:
    """Um servidor comprometido não deve conseguir encher o disco do usuário."""
    _fingir_download(monkeypatch, b"x" * (updater.MAX_WHEEL_BYTES + 1024))

    with pytest.raises(RuntimeError, match="maior que o esperado"):
        updater.install("2030.1.1", "https://exemplo/pacote.whl", "")


def test_instalacao_falha_nao_deixa_restos(
    monkeypatch: pytest.MonkeyPatch, pasta_isolada: Path
) -> None:
    _fingir_download(monkeypatch, _wheel({"nada/__init__.py": ""}))

    with pytest.raises(RuntimeError):
        updater.install("2030.1.1", "https://exemplo/pacote.whl", "")

    assert list(pasta_isolada.iterdir()) == []


# ── Ativação ─────────────────────────────────────────────────────────────


def test_sem_nada_instalado_usa_a_versao_embutida() -> None:
    assert updater.activate() is None


def test_nao_troca_o_motor_com_o_ytdlp_ja_importado(
    monkeypatch: pytest.MonkeyPatch, pasta_isolada: Path
) -> None:
    """Trocar o sys.path depois do import não teria efeito e daria a falsa
    impressão de que a atualização entrou em uso."""
    import sys

    (pasta_isolada / "yt_dlp-2030.1.1" / "yt_dlp").mkdir(parents=True)
    (pasta_isolada / "yt_dlp-2030.1.1" / "yt_dlp" / "__init__.py").write_text("")

    monkeypatch.setitem(sys.modules, "yt_dlp", object())
    assert updater.activate() is None


def test_escolhe_sempre_a_versao_mais_nova(
    monkeypatch: pytest.MonkeyPatch, pasta_isolada: Path
) -> None:
    import sys

    for versao in ("2026.1.1", "2026.10.1", "2026.9.1"):
        pasta = pasta_isolada / f"yt_dlp-{versao}" / "yt_dlp"
        pasta.mkdir(parents=True)
        (pasta / "__init__.py").write_text("")

    monkeypatch.delitem(sys.modules, "yt_dlp", raising=False)
    caminho_original = list(sys.path)
    try:
        assert updater.activate() == "2026.10.1"
        assert str(pasta_isolada / "yt_dlp-2026.10.1") == sys.path[0]
    finally:
        sys.path[:] = caminho_original


def test_ignora_pasta_sem_o_pacote_dentro(
    monkeypatch: pytest.MonkeyPatch, pasta_isolada: Path
) -> None:
    """Uma instalação interrompida deixa a pasta pela metade; ela não pode ser
    escolhida no lugar da versão embutida, que funciona."""
    import sys

    (pasta_isolada / "yt_dlp-2030.1.1").mkdir()  # sem o subdiretório yt_dlp
    monkeypatch.delitem(sys.modules, "yt_dlp", raising=False)

    caminho_original = list(sys.path)
    try:
        assert updater.activate() is None
    finally:
        sys.path[:] = caminho_original


# ── Consulta ao repositório ──────────────────────────────────────────────


def test_versao_disponivel_compara_com_a_em_uso(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(updater, "current_version", lambda: "2026.1.1")
    monkeypatch.setattr(
        updater, "latest_version", lambda: ("2026.7.4", "https://exemplo/p.whl", "abc")
    )
    assert updater.update_available() == "2026.7.4"

    monkeypatch.setattr(updater, "current_version", lambda: "2026.7.4")
    assert updater.update_available() is None


def test_repositorio_inacessivel_nao_derruba_o_aplicativo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import requests

    def explode(*a, **k):
        raise requests.ConnectionError("sem rede")

    monkeypatch.setattr(requests, "get", explode)
    assert updater.latest_version() is None
    assert updater.update_available() is None


def test_recusa_versao_com_formato_estranho(monkeypatch: pytest.MonkeyPatch) -> None:
    """Só aceitamos versões numéricas; qualquer outra coisa vinda da API é
    tratada como resposta inválida."""
    import requests

    class Resposta:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict:
            return {
                "info": {"version": "1.0.0-beta; rm -rf /"},
                "urls": [
                    {"packagetype": "bdist_wheel", "filename": "x-py3-none-any.whl", "url": "u"}
                ],
            }

    monkeypatch.setattr(requests, "get", lambda *a, **k: Resposta())
    assert updater.latest_version() is None
