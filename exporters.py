"""
Exportação de leads para CSV e JSON.
"""
from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import List

from searchers import Lead


def exportar_csv(leads: List[Lead], caminho: str) -> None:
    """Salva a lista de leads em um arquivo CSV."""
    if not leads:
        return

    path = Path(caminho)
    path.parent.mkdir(parents=True, exist_ok=True)

    campos = list(asdict(leads[0]).keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for lead in leads:
            writer.writerow(asdict(lead))


def exportar_json(leads: List[Lead], caminho: str) -> None:
    """Salva a lista de leads em um arquivo JSON."""
    if not leads:
        return

    path = Path(caminho)
    path.parent.mkdir(parents=True, exist_ok=True)

    dados = [asdict(lead) for lead in leads]
    with path.open("w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
