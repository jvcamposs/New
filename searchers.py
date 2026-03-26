"""
Módulo de busca de potenciais clientes via DuckDuckGo e web scraping.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import List

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS


@dataclass
class Lead:
    nome: str = ""
    tipo: str = ""          # B2B ou B2C
    descricao: str = ""
    site: str = ""
    email: str = ""
    telefone: str = ""
    localizacao: str = ""
    fonte: str = ""
    palavras_chave: str = ""


def _extrair_contatos(texto: str) -> tuple[str, str]:
    """Extrai email e telefone de um texto bruto."""
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}", texto)
    tel_match = re.search(r"(?:\+55\s?)?(?:\(?\d{2}\)?\s?)(?:9\s?)?\d{4}[-\s]?\d{4}", texto)
    email = email_match.group(0) if email_match else ""
    telefone = tel_match.group(0) if tel_match else ""
    return email, telefone


def _enriquecer_lead(lead: Lead, timeout: int = 6) -> Lead:
    """Tenta visitar o site do lead para coletar contatos."""
    if not lead.site:
        return lead
    try:
        resp = requests.get(lead.site, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(resp.text, "lxml")
        texto = soup.get_text(separator=" ", strip=True)
        email, telefone = _extrair_contatos(texto)
        if email and not lead.email:
            lead.email = email
        if telefone and not lead.telefone:
            lead.telefone = telefone
    except Exception:
        pass
    return lead


def buscar_b2b(
    keywords: str,
    localizacao: str = "",
    setor: str = "",
    max_resultados: int = 20,
    enriquecer: bool = True,
) -> List[Lead]:
    """
    Busca empresas (B2B) como potenciais clientes.

    Parâmetros
    ----------
    keywords      : produto/serviço que você oferece
    localizacao   : cidade ou estado alvo (ex: "São Paulo")
    setor         : setor/segmento alvo (ex: "tecnologia", "varejo")
    max_resultados: limite de leads retornados
    enriquecer    : se True, visita os sites para coletar contatos
    """
    partes = [keywords]
    if localizacao:
        partes.append(localizacao)
    if setor:
        partes.append(setor)
    partes += ["empresa", "contato", "site:br OR site:com.br"]
    query = " ".join(partes)

    leads: List[Lead] = []
    with DDGS() as ddgs:
        resultados = ddgs.text(query, max_results=max_resultados * 2)
        for r in resultados:
            if len(leads) >= max_resultados:
                break
            texto = f"{r.get('title', '')} {r.get('body', '')}"
            email, telefone = _extrair_contatos(texto)
            lead = Lead(
                nome=r.get("title", "").split(" - ")[0].strip(),
                tipo="B2B",
                descricao=r.get("body", "")[:200],
                site=r.get("href", ""),
                email=email,
                telefone=telefone,
                localizacao=localizacao,
                fonte="DuckDuckGo",
                palavras_chave=keywords,
            )
            leads.append(lead)

    if enriquecer:
        for lead in leads:
            _enriquecer_lead(lead)
            time.sleep(0.3)

    return leads


def buscar_b2c(
    keywords: str,
    localizacao: str = "",
    perfil: str = "",
    max_resultados: int = 20,
    enriquecer: bool = True,
) -> List[Lead]:
    """
    Busca consumidores/pessoas (B2C) como potenciais clientes.

    Parâmetros
    ----------
    keywords      : produto/serviço que você oferece
    localizacao   : cidade ou estado alvo
    perfil        : descrição do perfil do consumidor (ex: "jovens", "mães", "atletas")
    max_resultados: limite de leads retornados
    enriquecer    : se True, visita as páginas para coletar contatos
    """
    partes = [keywords]
    if localizacao:
        partes.append(localizacao)
    if perfil:
        partes.append(perfil)
    partes += ["comprar", "contratar", "serviço", "produto"]
    query = " ".join(partes)

    leads: List[Lead] = []
    with DDGS() as ddgs:
        resultados = ddgs.text(query, max_results=max_resultados * 2)
        for r in resultados:
            if len(leads) >= max_resultados:
                break
            texto = f"{r.get('title', '')} {r.get('body', '')}"
            email, telefone = _extrair_contatos(texto)
            lead = Lead(
                nome=r.get("title", "").split(" - ")[0].strip(),
                tipo="B2C",
                descricao=r.get("body", "")[:200],
                site=r.get("href", ""),
                email=email,
                telefone=telefone,
                localizacao=localizacao,
                fonte="DuckDuckGo",
                palavras_chave=keywords,
            )
            leads.append(lead)

    if enriquecer:
        for lead in leads:
            _enriquecer_lead(lead)
            time.sleep(0.3)

    return leads
