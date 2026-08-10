import os
import glob
import frontmatter
from sentence_transformers import SentenceTransformer
import psycopg2
from psycopg2.extras import execute_values

MODELO = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def carregar_documentos(base_path="."):
    docs = []
    for path in glob.glob(f"{base_path}/**/*.md", recursive=True):
        nome_arquivo = os.path.basename(path).lower()
        caminho_normalizado = path.replace("\\", "/")

        if nome_arquivo == "readme.md":
            continue
        if "/.github/" in caminho_normalizado:
            continue

        post = frontmatter.load(path)
        docs.append({
            "path": path,
            "categoria": post.get("categoria", "geral"),
            "curso": post.get("curso", "todos"),
            "conteudo": post.content,
        })
    return docs

def chunk_texto(texto, tamanho=800, overlap=100):
    chunks = []
    i = 0
    while i < len(texto):
        chunks.append(texto[i:i + tamanho])
        i += tamanho - overlap
    return chunks

def gerar_embedding(texto):
    return MODELO.encode(texto).tolist()

def indexar(conn_str):
    docs = carregar_documentos()
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()

    rows = []
    for doc in docs:
        for chunk in chunk_texto(doc["conteudo"]):
            if not chunk.strip():
                continue
            emb = gerar_embedding(chunk)
            rows.append((doc["path"], doc["categoria"], doc["curso"], chunk, emb))

    execute_values(
        cur,
        """INSERT INTO kb_chunks (source_path, categoria, curso, conteudo, embedding)
           VALUES %s
           ON CONFLICT (source_path, conteudo) DO NOTHING""",
        rows,
    )
    conn.commit()
    cur.close()
    conn.close()
    print(f"Indexados {len(rows)} chunks de {len(docs)} documentos.")

if __name__ == "__main__":
    indexar(os.environ["DATABASE_URL"])