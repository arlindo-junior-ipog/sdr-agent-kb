"""
preencher_mercado_trabalho.py

Para cada arquivo em produtos/ que já tem curso_id (id_crm) preenchido no
frontmatter, busca o registro correspondente no sqldw_STG_CURSO_SITE.json
e insere uma seção "## Mercado de Trabalho e Áreas de Atuação" no final do
arquivo, usando os campos mercado_de_trabalho e atuacao do JSON (HTML limpo).

Idempotente: se o arquivo já tiver essa seção, pula (não duplica).
Arquivos sem curso_id são pulados e listados no final, para você decidir
se quer casar manualmente (via sugerir_curso_ids.py) antes de rodar de novo.

Uso:
    python preencher_mercado_trabalho.py caminho/para/sqldw_STG_CURSO_SITE.json
"""

import sys
import glob
import json
import re
import html
import frontmatter

PASTA_PRODUTOS = "produtos"
MARCADOR_SECAO = "## Mercado de Trabalho e Áreas de Atuação"


def limpar_html(texto: str) -> str:
    if not texto:
        return ""
    # remove tags HTML
    sem_tags = re.sub(r"<[^>]+>", " ", texto)
    # decodifica entidades (&amp;, &nbsp;, etc.)
    decodificado = html.unescape(sem_tags)
    # normaliza espaços e quebras de linha excessivas
    normalizado = re.sub(r"[ \t]+", " ", decodificado)
    normalizado = re.sub(r"\n\s*\n+", "\n\n", normalizado)
    return normalizado.strip()


def carregar_json_por_id_crm(caminho_json: str) -> dict:
    with open(caminho_json, encoding="utf-8") as f:
        data = json.load(f)
    return {c["id_crm"]: c for c in data if c.get("id_crm")}


def main():
    if len(sys.argv) < 2:
        print("Uso: python preencher_mercado_trabalho.py caminho/para/sqldw_STG_CURSO_SITE.json")
        sys.exit(1)

    caminho_json = sys.argv[1]
    cursos_por_id_crm = carregar_json_por_id_crm(caminho_json)

    atualizados = []
    ja_tinha_secao = []
    sem_curso_id = []
    sem_match_no_json = []

    for path in sorted(glob.glob(f"{PASTA_PRODUTOS}/*.md")):
        post = frontmatter.load(path)
        curso_id = post.get("curso_id")

        if not curso_id:
            sem_curso_id.append(path)
            continue

        if MARCADOR_SECAO in post.content:
            ja_tinha_secao.append(path)
            continue

        curso_json = cursos_por_id_crm.get(int(curso_id))
        if not curso_json:
            sem_match_no_json.append(path)
            continue

        mercado = limpar_html(curso_json.get("mercado_de_trabalho"))
        atuacao = limpar_html(curso_json.get("atuacao"))

        if not mercado and not atuacao:
            sem_match_no_json.append(path)
            continue

        secao = f"\n\n{MARCADOR_SECAO}\n\n"
        if mercado:
            secao += f"{mercado}\n\n"
        if atuacao:
            secao += f"**Áreas de atuação:** {atuacao}\n"

        post.content = post.content.rstrip() + secao

        with open(path, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        atualizados.append(path)
        print(f"✓ {path}")

    print(f"\n{len(atualizados)} arquivo(s) atualizado(s).")
    if ja_tinha_secao:
        print(f"{len(ja_tinha_secao)} já tinham a seção (pulados): {', '.join(ja_tinha_secao)}")
    if sem_curso_id:
        print(f"\n{len(sem_curso_id)} arquivo(s) SEM curso_id (rode sugerir_curso_ids.py primeiro):")
        for p in sem_curso_id:
            print(f"  - {p}")
    if sem_match_no_json:
        print(f"\n{len(sem_match_no_json)} arquivo(s) com curso_id mas sem dado de mercado no JSON:")
        for p in sem_match_no_json:
            print(f"  - {p}")


if __name__ == "__main__":
    main()