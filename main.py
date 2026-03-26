#!/usr/bin/env python3
"""
find-customers — CLI para encontrar potenciais clientes (B2B e B2C).

Uso rápido:
  python main.py b2b   -k "software de gestão" -l "São Paulo" -n 20
  python main.py b2c   -k "academia crossfit"  -l "Curitiba"  -n 20
  python main.py ambos -k "consultoria financeira"            -n 30
"""
import sys

import click
from rich.console import Console
from rich.table import Table

from exporters import exportar_csv, exportar_json
from searchers import Lead, buscar_b2b, buscar_b2c

console = Console()


def _exibir_tabela(leads: list[Lead], titulo: str) -> None:
    table = Table(title=titulo, show_lines=True)
    table.add_column("#", style="dim", width=4)
    table.add_column("Nome", style="bold cyan", max_width=35)
    table.add_column("Tipo", style="magenta", width=5)
    table.add_column("Email", style="green", max_width=30)
    table.add_column("Telefone", style="yellow", width=16)
    table.add_column("Localização", max_width=18)
    table.add_column("Site", style="blue", max_width=40)

    for i, lead in enumerate(leads, 1):
        table.add_row(
            str(i),
            lead.nome[:35],
            lead.tipo,
            lead.email or "—",
            lead.telefone or "—",
            lead.localizacao or "—",
            lead.site[:40] if lead.site else "—",
        )
    console.print(table)


def _salvar(leads: list[Lead], saida: str, formato: str) -> None:
    if formato == "csv":
        exportar_csv(leads, saida)
    else:
        exportar_json(leads, saida)
    console.print(f"\n[bold green]✓[/] {len(leads)} leads salvos em [bold]{saida}[/]")


# ---------------------------------------------------------------------------
# Opções comuns reutilizáveis
# ---------------------------------------------------------------------------
_opts_comuns = [
    click.option("--keywords", "-k", required=True, help="Palavras-chave do produto/serviço"),
    click.option("--localizacao", "-l", default="", help='Cidade ou estado alvo (ex: "São Paulo")'),
    click.option("--max-resultados", "-n", default=20, show_default=True, help="Limite de leads"),
    click.option(
        "--saida", "-o", default="leads.csv", show_default=True, help="Arquivo de saída"
    ),
    click.option(
        "--formato",
        "-f",
        type=click.Choice(["csv", "json"]),
        default="csv",
        show_default=True,
        help="Formato do arquivo de saída",
    ),
    click.option(
        "--enriquecer/--sem-enriquecer",
        default=True,
        show_default=True,
        help="Visitar sites para coletar emails e telefones",
    ),
]


def _add_opts(opts):
    """Decorador para adicionar opções comuns a um comando."""
    def decorator(func):
        for opt in reversed(opts):
            func = opt(func)
        return func
    return decorator


# ---------------------------------------------------------------------------
# Grupo principal
# ---------------------------------------------------------------------------
@click.group()
def cli():
    """
    \b
    find-customers — Encontre potenciais clientes B2B e B2C.

    Exemplos:
      python main.py b2b   -k "ERP para indústria"   -l "Belo Horizonte"
      python main.py b2c   -k "personal trainer"     -l "Rio de Janeiro"
      python main.py ambos -k "software de marketing" -n 40
    """


# ---------------------------------------------------------------------------
# Comando: b2b
# ---------------------------------------------------------------------------
@cli.command()
@_add_opts(_opts_comuns)
@click.option("--setor", "-s", default="", help='Setor alvo (ex: "varejo", "saúde")')
def b2b(keywords, localizacao, max_resultados, saida, formato, enriquecer, setor):
    """Busca empresas (B2B) como potenciais clientes."""
    console.print(f"\n[bold]Buscando leads B2B:[/] {keywords}", highlight=False)
    with console.status("Pesquisando..."):
        leads = buscar_b2b(
            keywords=keywords,
            localizacao=localizacao,
            setor=setor,
            max_resultados=max_resultados,
            enriquecer=enriquecer,
        )

    if not leads:
        console.print("[yellow]Nenhum lead encontrado. Tente palavras-chave diferentes.[/]")
        sys.exit(0)

    _exibir_tabela(leads, f"Leads B2B — {keywords}")
    _salvar(leads, saida, formato)


# ---------------------------------------------------------------------------
# Comando: b2c
# ---------------------------------------------------------------------------
@cli.command()
@_add_opts(_opts_comuns)
@click.option("--perfil", "-p", default="", help='Perfil do consumidor (ex: "jovens", "mães")')
def b2c(keywords, localizacao, max_resultados, saida, formato, enriquecer, perfil):
    """Busca consumidores (B2C) como potenciais clientes."""
    console.print(f"\n[bold]Buscando leads B2C:[/] {keywords}", highlight=False)
    with console.status("Pesquisando..."):
        leads = buscar_b2c(
            keywords=keywords,
            localizacao=localizacao,
            perfil=perfil,
            max_resultados=max_resultados,
            enriquecer=enriquecer,
        )

    if not leads:
        console.print("[yellow]Nenhum lead encontrado. Tente palavras-chave diferentes.[/]")
        sys.exit(0)

    _exibir_tabela(leads, f"Leads B2C — {keywords}")
    _salvar(leads, saida, formato)


# ---------------------------------------------------------------------------
# Comando: ambos
# ---------------------------------------------------------------------------
@cli.command()
@_add_opts(_opts_comuns)
@click.option("--setor", "-s", default="", help="Setor alvo para B2B")
@click.option("--perfil", "-p", default="", help="Perfil do consumidor para B2C")
def ambos(keywords, localizacao, max_resultados, saida, formato, enriquecer, setor, perfil):
    """Busca tanto empresas (B2B) quanto consumidores (B2C)."""
    metade = max_resultados // 2

    console.print(f"\n[bold]Buscando leads B2B + B2C:[/] {keywords}", highlight=False)

    with console.status("Pesquisando B2B..."):
        leads_b2b = buscar_b2b(keywords, localizacao, setor, metade, enriquecer)

    with console.status("Pesquisando B2C..."):
        leads_b2c = buscar_b2c(keywords, localizacao, perfil, metade, enriquecer)

    todos = leads_b2b + leads_b2c

    if not todos:
        console.print("[yellow]Nenhum lead encontrado. Tente palavras-chave diferentes.[/]")
        sys.exit(0)

    _exibir_tabela(todos, f"Leads B2B + B2C — {keywords}")
    _salvar(todos, saida, formato)


if __name__ == "__main__":
    cli()
