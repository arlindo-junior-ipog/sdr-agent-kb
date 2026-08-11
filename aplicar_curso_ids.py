"""
aplicar_curso_ids.py

Lê revisao_curso_ids.csv (já revisado e com a coluna 'id_crm_confirmado'
preenchida por você) e grava o curso_id no frontmatter de cada arquivo
correspondente em produtos/.

Só atualiza arquivos cuja linha tenha 'id_crm_confirmado' preenchido —
linhas em branco são puladas (nada é escrito, nada quebra).

Uso:
    python aplicar_curso_ids.py
"""

import csv
import frontmatter

CAMINHO_CSV = "revisao_curso_ids.csv"


def main():
    atualizados = 0
    pulados = 0

    with open(CAMINHO_CSV, encoding="utf-8-sig") as f:
        # Ler a primeira linha para detectar o delimitador
        primeira_linha = f.readline()
        f.seek(0)
        
        # Se tiver ponto-e-vírgula, usa ele; caso contrário, usa vírgula
        delimiter = ';' if ';' in primeira_linha else ','
        
        leitor = csv.DictReader(f, delimiter=delimiter)
        linhas = list(leitor)

    for linha in linhas:
        id_confirmado = (linha.get("id_crm_confirmado") or "").strip()
        caminho_arquivo = linha["arquivo"]

        if not id_confirmado:
            pulados += 1
            continue

        post = frontmatter.load(caminho_arquivo)
        valor_anterior = post.get("curso_id")
        post["curso_id"] = int(id_confirmado)

        with open(caminho_arquivo, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        print(f"✓ {caminho_arquivo}: curso_id {valor_anterior} -> {id_confirmado}")
        atualizados += 1

    print(f"\n{atualizados} arquivo(s) atualizado(s), {pulados} pulado(s) (sem id_crm_confirmado).")


if __name__ == "__main__":
    main()