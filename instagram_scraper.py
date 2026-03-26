"""
Scraper de potenciais clientes no Instagram.

Busca contas por hashtags relacionadas a dropshipping e lojas físicas,
filtrando por faixa de seguidores (padrão: 1.000 a 8.000).

Requer login no Instagram para evitar bloqueios por rate-limit.
"""
from __future__ import annotations

import time
import random
from dataclasses import dataclass
from typing import Iterator, List

import instaloader

# Hashtags relevantes para dropshipping e lojas físicas (PT-BR)
HASHTAGS_DROPSHIPPING = [
    "dropshipping",
    "dropshippingbrasil",
    "dropshippingbr",
    "dropshippingstore",
    "lojavirtual",
    "lojaonline",
    "ecommercebrasil",
    "ecommerce",
    "vendasonline",
]

HASHTAGS_LOJA_FISICA = [
    "lojafisica",
    "lojalocal",
    "comerciolocal",
    "pequenasempresas",
    "empreendedorismo",
    "lojinha",
    "varejo",
    "negociolocal",
    "comerciante",
]


@dataclass
class ContaInstagram:
    username: str = ""
    nome_completo: str = ""
    seguidores: int = 0
    seguindo: int = 0
    posts: int = 0
    bio: str = ""
    site: str = ""
    email_bio: str = ""
    telefone_bio: str = ""
    perfil_comercial: bool = False
    categoria: str = ""
    hashtag_origem: str = ""
    nicho: str = ""
    url_perfil: str = ""


def _extrair_email_bio(bio: str) -> str:
    import re
    m = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", bio)
    return m.group(0) if m else ""


def _extrair_telefone_bio(bio: str) -> str:
    import re
    m = re.search(r"(?:\+55\s?)?(?:\(?\d{2}\)?\s?)(?:9\s?)?\d{4}[-\s]?\d{4}", bio)
    return m.group(0) if m else ""


def _perfil_para_conta(perfil: instaloader.Profile, hashtag: str, nicho: str) -> ContaInstagram:
    bio = perfil.biography or ""
    return ContaInstagram(
        username=perfil.username,
        nome_completo=perfil.full_name or "",
        seguidores=perfil.followers,
        seguindo=perfil.followees,
        posts=perfil.mediacount,
        bio=bio[:200],
        site=perfil.external_url or "",
        email_bio=_extrair_email_bio(bio),
        telefone_bio=_extrair_telefone_bio(bio),
        perfil_comercial=perfil.is_business_account,
        categoria=perfil.business_category_name or "",
        hashtag_origem=hashtag,
        nicho=nicho,
        url_perfil=f"https://instagram.com/{perfil.username}",
    )


def _buscar_por_hashtag(
    loader: instaloader.Instaloader,
    hashtag: str,
    nicho: str,
    min_seguidores: int,
    max_seguidores: int,
    max_posts_analisar: int,
    usernames_vistos: set,
) -> Iterator[ContaInstagram]:
    """Itera sobre posts de uma hashtag e filtra perfis pela faixa de seguidores."""
    try:
        tag = instaloader.Hashtag.from_name(loader.context, hashtag)
        analisados = 0
        for post in tag.get_posts():
            if analisados >= max_posts_analisar:
                break
            username = post.owner_username
            if username in usernames_vistos:
                analisados += 1
                continue
            usernames_vistos.add(username)
            analisados += 1
            try:
                perfil = instaloader.Profile.from_username(loader.context, username)
                seguidores = perfil.followers
                if min_seguidores <= seguidores <= max_seguidores:
                    yield _perfil_para_conta(perfil, hashtag, nicho)
                # Pausa aleatória para evitar rate-limit
                time.sleep(random.uniform(1.5, 3.5))
            except Exception:
                continue
    except Exception:
        return


def buscar_instagram(
    nicho: str = "ambos",
    min_seguidores: int = 1000,
    max_seguidores: int = 8000,
    max_resultados: int = 30,
    max_posts_por_hashtag: int = 50,
    usuario_instagram: str = "",
    senha_instagram: str = "",
) -> List[ContaInstagram]:
    """
    Busca potenciais clientes no Instagram.

    Parâmetros
    ----------
    nicho               : "dropshipping", "loja_fisica" ou "ambos"
    min_seguidores      : mínimo de seguidores (padrão 1.000)
    max_seguidores      : máximo de seguidores (padrão 8.000)
    max_resultados      : total de contas a retornar
    max_posts_por_hashtag: quantos posts analisar por hashtag
    usuario_instagram   : login do Instagram (recomendado para evitar bloqueio)
    senha_instagram     : senha do Instagram
    """
    loader = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        quiet=True,
    )

    if usuario_instagram and senha_instagram:
        try:
            loader.login(usuario_instagram, senha_instagram)
        except Exception as e:
            raise RuntimeError(f"Falha no login do Instagram: {e}") from e

    if nicho == "dropshipping":
        hashtags = [(h, "dropshipping") for h in HASHTAGS_DROPSHIPPING]
    elif nicho == "loja_fisica":
        hashtags = [(h, "loja_fisica") for h in HASHTAGS_LOJA_FISICA]
    else:
        hashtags = [(h, "dropshipping") for h in HASHTAGS_DROPSHIPPING] + [
            (h, "loja_fisica") for h in HASHTAGS_LOJA_FISICA
        ]

    contas: List[ContaInstagram] = []
    usernames_vistos: set = set()

    for hashtag, nicho_tag in hashtags:
        if len(contas) >= max_resultados:
            break
        for conta in _buscar_por_hashtag(
            loader,
            hashtag,
            nicho_tag,
            min_seguidores,
            max_seguidores,
            max_posts_por_hashtag,
            usernames_vistos,
        ):
            contas.append(conta)
            if len(contas) >= max_resultados:
                break

    return contas
