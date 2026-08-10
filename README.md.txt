# sdr-agent-kb

Base de conhecimento do Agente SDR (pré-vendas) do IPOG.

Este repositório é a **fonte da verdade** de todo o conteúdo consultado pelo
agente em tempo real (produtos, objeções, políticas, playbook de vendas).
Toda alteração deve passar por Pull Request — o conteúdo aqui é o que o
agente usa para responder a leads reais, então mudanças erradas viram
promessa errada para um cliente.

## Como funciona

A cada `push` na branch `main`, um GitHub Action reindexação automaticamente
todo o conteúdo `.md` no banco vetorial (Supabase/pgvector) usado pelo
agente em produção. Não é preciso fazer deploy manual — só dar merge.

## Estrutura

produtos/ → informações por curso (grade, formato, carga horária, público-alvo)
objecoes/ → como lidar com objeções comuns durante a qualificação
politicas/ → regras de negócio (descontos, formas de pagamento) — alçada do Financeiro
playbook/ → metodologia de qualificação (SPIN, BANT) usada pelo agente
faq.md → perguntas frequentes gerais, fora das categorias acima
## Formato dos arquivos

Todo arquivo `.md` deve ter frontmatter com metadata, usado pelo agente
para filtrar o retrieval por curso/categoria:

```yaml
---
categoria: objecao | produto | politica | playbook | faq
curso: todos | slug-do-curso
atualizado_em: AAAA-MM-DD
aprovado_por: nome ou área responsável
---
```

## Regras de conteúdo

- Nunca inclua valor de curso, desconto ou condição de pagamento sem
  aprovação do Financeiro registrada em `politicas/`.
- Nunca prometa vaga garantida, aprovação garantida ou resultado de carreira.
- Revisão por PR obrigatória antes de merge em `main`.