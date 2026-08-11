"""
sugerir_curso_ids.py

Lê todos os arquivos em produtos/, tenta casar cada um com um curso do
sqldw_STG_CURSO_SITE.json por similaridade de nome, e gera um CSV de revisão
com os candidatos + pontuação de confiança.

NÃO grava nada nos arquivos .md — isso é intencional. Depois de você revisar
e corrigir o CSV (coluna 'id_crm_confirmado'), rode aplicar_curso_ids.py
para de fato atualizar o frontmatter.

Uso:
    python sugerir_curso_ids.py caminho/para/sqldw_STG_CURSO_SITE.json

Gera: revisao_curso_ids.csv
"""

import sys
import csv
import glob
import json
import unicodedata
import difflib
import frontmatter

PASTA_PRODUTOS = "produtos"
TOP_N_CANDIDATOS = 3


def normalizar(texto: str) -> str:
    """minúsculo, sem acento, sem pontuação leve — para comparação justa."""
    if not texto:
        return ""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return sem_acento.lower().strip()


def titulo_do_arquivo(post) -> str:
    primeira_linha = post.content.strip().split("\n")[0]
    return primeira_linha.lstrip("# ").strip()


def carregar_cursos_locais(base_path: str = PASTA_PRODUTOS) -> list[dict]:
    cursos = []
    for path in sorted(glob.glob(f"{base_path}/*.md")):
        post = frontmatter.load(path)
        slug = post.get("curso")
        if not slug or slug == "todos":
            continue
        cursos.append({
            "path": path,
            "slug": slug,
            "titulo": titulo_do_arquivo(post),
            "curso_id_atual": post.get("curso_id"),
        })
    return cursos


def carregar_cursos_json(caminho_json: str) -> list[dict]:
    with open(caminho_json, encoding="utf-8") as f:
        data = json.load(f)
    # normalmente só interessam cursos ativos (status == 1), mas mantemos
    # todos e deixamos o humano decidir na revisão
    return data


def encontrar_candidatos(titulo_local: str, cursos_json: list[dict], top_n: int = TOP_N_CANDIDATOS) -> list[tuple]:
    titulo_norm = normalizar(titulo_local)
    pontuados = []
    for curso in cursos_json:
        nome_norm = normalizar(curso.get("nome") or "")
        if not nome_norm:
            continue
        score = difflib.SequenceMatcher(None, titulo_norm, nome_norm).ratio()
        pontuados.append((score, curso))
    pontuados.sort(key=lambda x: -x[0])
    return pontuados[:top_n]


def main():
    if len(sys.argv) < 2:
        print("Uso: python sugerir_curso_ids.py caminho/para/sqldw_STG_CURSO_SITE.json")
        sys.exit(1)

    caminho_json = sys.argv[1]
    cursos_locais = carregar_cursos_locais()
    cursos_json = carregar_cursos_json(caminho_json)

    print(f"{len(cursos_locais)} arquivos encontrados em {PASTA_PRODUTOS}/")
    print(f"{len(cursos_json)} cursos carregados do JSON\n")

    linhas_csv = []

    for curso_local in cursos_locais:
        candidatos = encontrar_candidatos(curso_local["titulo"], cursos_json)

        linha = {
            "arquivo": curso_local["path"],
            "slug_local": curso_local["slug"],
            "titulo_local": curso_local["titulo"],
            "curso_id_atual": curso_local["curso_id_atual"] or "",
        }

        for i, (score, cand) in enumerate(candidatos, start=1):
            linha[f"candidato_{i}_nome"] = cand.get("nome", "")
            linha[f"candidato_{i}_id_crm"] = cand.get("id_crm", "")
            linha[f"candidato_{i}_slug"] = cand.get("slug", "")
            linha[f"candidato_{i}_score"] = round(score, 3)

        # heurística simples de confiança: só marca como "alta" se o melhor
        # candidato tiver score bem mais alto que o segundo colocado
        if candidatos:
            melhor_score = candidatos[0][0]
            segundo_score = candidatos[1][0] if len(candidatos) > 1 else 0
            if melhor_score >= 0.85 and (melhor_score - segundo_score) >= 0.1:
                linha["confianca"] = "alta"
                linha["id_crm_sugerido"] = candidatos[0][1].get("id_crm", "")
            elif melhor_score >= 0.6:
                linha["confianca"] = "media - revisar"
                linha["id_crm_sugerido"] = candidatos[0][1].get("id_crm", "")
            else:
                linha["confianca"] = "baixa - buscar manualmente"
                linha["id_crm_sugerido"] = ""
        else:
            linha["confianca"] = "sem candidato"
            linha["id_crm_sugerido"] = ""

        # coluna para você preencher/confirmar manualmente na revisão
        linha["id_crm_confirmado"] = linha["id_crm_sugerido"] if linha["confianca"] == "alta" else ""

        linhas_csv.append(linha)

        print(f"[{linha['confianca']:20s}] {curso_local['slug']:55s} -> "
              f"id_crm sugerido: {linha['id_crm_sugerido']}")

    # monta o cabeçalho dinamicamente (cobre o número de candidatos configurado)
    campos_base = ["arquivo", "slug_local", "titulo_local", "curso_id_atual",
                   "confianca", "id_crm_sugerido", "id_crm_confirmado"]
    campos_candidatos = []
    for i in range(1, TOP_N_CANDIDATOS + 1):
        campos_candidatos += [f"candidato_{i}_nome", f"candidato_{i}_id_crm",
                               f"candidato_{i}_slug", f"candidato_{i}_score"]
    campos = campos_base + campos_candidatos

    with open("revisao_curso_ids.csv", "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas_csv)

    print(f"\nGerado: revisao_curso_ids.csv ({len(linhas_csv)} linhas)")
    print("Abra no Excel/Google Sheets, confira as colunas 'confianca' e")
    print("'candidato_N_*', e preencha 'id_crm_confirmado' para cada linha")
    print("antes de rodar aplicar_curso_ids.py.")


if __name__ == "__main__":
    main()