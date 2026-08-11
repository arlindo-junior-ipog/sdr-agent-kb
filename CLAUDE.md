# CLAUDE.md — Pipeline de modelagem de cursos para o Agente SDR (sdr-agent-kb)

Este arquivo orienta o Claude Code neste projeto. Ele descreve como transformar
PDFs originais de material comercial de curso (uma pasta de "originais") em
arquivos `.md` prontos para a pasta `produtos/` do repositório `sdr-agent-kb`,
que alimenta a base de conhecimento (RAG) do Agente SDR do IPOG.

## Contexto do projeto

- `sdr-agent-kb` é a fonte da verdade do conteúdo consultado pelo Agente SDR em
  tempo real (produtos, objeções, políticas, playbook).
- A cada push em `main`, um GitHub Action reindexação automaticamente o
  conteúdo `.md` no banco vetorial (Supabase/pgvector) usado pelo agente.
- Este pipeline cuida apenas da pasta `produtos/` — informações sobre cursos
  (grade, formato, carga horária, público-alvo). Preço, desconto e condição de
  pagamento NUNCA entram aqui — isso é exclusivo de `politicas/`, aprovado pelo
  Financeiro.

## Estrutura de pastas esperada

```
<pasta de trabalho>/
  originais/          ← PDFs de material comercial de curso (entrada, somente leitura)
  sdr-agent-kb/
    produtos/          ← saída deste pipeline (.md modelados)
    objecoes/
    politicas/
    playbook/
    faq.md
```

Ajuste os caminhos acima se a estrutura real do projeto for diferente — pergunte
ao usuário se não encontrar as pastas.

## Fluxo de trabalho

Quando o usuário pedir para processar PDFs novos (ex.: "modele os PDFs novos da
pasta originais"):

1. Liste os arquivos em `originais/` e liste os slugs já existentes em
   `sdr-agent-kb/produtos/` (nome do arquivo sem extensão). Processe apenas os
   PDFs que ainda não têm um `.md` correspondente, a menos que o usuário peça
   explicitamente para reprocessar um curso existente.
2. Para cada PDF novo, extraia o texto (ex.: `pdftotext`, `pypdf`, ou
   equivalente disponível no ambiente) e aplique o **template de modelagem**
   abaixo.
3. Salve o resultado em `sdr-agent-kb/produtos/<slug>.md`.
4. Ao final, liste para o usuário: quais arquivos foram criados, e quaisquer
   **alertas** que precisam de revisão humana antes do merge (ver seção
   "Alertas obrigatórios" abaixo) — nunca faça `git commit`/`push` sem o
   usuário confirmar que revisou o conteúdo gerado.

## Convenção de slug

`<tipo>-<nome-do-curso-em-kebab-case-sem-acentos>`, onde `<tipo>` é:
- `pos-` para Pós-graduação/Especialização
- `mba-` para MBA
- `extensao-` para Curso de Extensão Universitária (presencial ou EaD)

Exemplos já em uso: `pos-gestao-estrategica-logistica`,
`mba-gestao-estrategica-pessoas`, `extensao-compliance-eficiencia-tributaria-agronegocio`.

## Template de modelagem (estrutura fixa do `.md`)

Sempre gere o arquivo com esta estrutura exata. Omita uma seção somente se a
informação genuinamente não existir no PDF de origem — nunca invente conteúdo
que não está no material fornecido.

```markdown
---
categoria: produto
curso: <slug>
atualizado_em: <AAAA-MM-DD de hoje>
aprovado_por: comercial
---

# <Nome completo do curso, com tipo (Pós-Graduação/MBA/Curso de Extensão Universitária)>

## Resumo para qualificação (SPIN)
2-3 linhas: que palavras-chave/temas o lead menciona que indicam fit com este
curso; para quem é claramente indicado (área de origem, objetivo profissional).

## Ficha técnica
- **Tipo:** ...
- **Carga horária:** ...
- **Modalidade:** (EaD assíncrono / On-line e Ao Vivo / Presencial — copie
  exatamente o que o PDF diz; se houver ambiguidade entre capa e seção de
  duração, sinalize isso em "Alertas" em vez de escolher uma versão)
- **Estrutura:** número de módulos
- **Horários:** se o curso tiver formato de fim de semana (sexta/sábado/domingo),
  liste os horários
- **Atividades práticas:** como funciona (Sala de Aula Invertida, Workshop de
  Práticas etc.)

## Para quem é o curso
Público-alvo conforme descrito no PDF. Se houver RESTRIÇÃO explícita de
formação (ex.: "restrito para Psicologia e Medicina"), deixe isso em
**destaque** nesta seção, não apenas mencionado de passagem.

## Documentação necessária para matrícula
Liste exatamente o que o PDF pede (diploma original, RG/CPF, ID profissional,
CNH etc.). Alguns cursos de extensão não pedem diploma — reflita isso
corretamente, não copie de um template genérico.

## Módulos (ementa resumida)
Liste os módulos/disciplinas por nome. Não é necessário copiar o conteúdo
detalhado de cada módulo linha por linha — um resumo de 1 linha por módulo é
suficiente, exceto quando um módulo tiver relevância comercial direta (ex.:
menção a legislação recente, diferencial forte) ou exigir um alerta de
conteúdo sensível.

## Coordenação
Nome, titulação principal e 1-2 linhas de credencial de maior peso comercial
(não copie o mini-currículo inteiro).

## Diferenciais para argumentação
2-4 bullets com o que mais diferencia este curso de concorrentes ou de cursos
irmãos do próprio IPOG (corpo docente notável, temas exclusivos, formato,
regulamentação recente abordada etc.).

## Objeções comuns específicas deste curso
1-3 pares pergunta/resposta curtos, específicos deste curso (não objeções
genéricas de preço — essas já vivem em `objecoes/preco.md`).

## Alertas (opcional — inclua somente se aplicável)
Sinalize aqui, de forma explícita, qualquer um destes casos:
- Curso com ementa muito parecida com outro curso já modelado (irmãos) — cite
  o outro slug e sugira uma pergunta de desambiguação para o agente usar.
- Informação ambígua ou conflitante dentro do próprio PDF (ex.: modalidade).
- Conteúdo sensível na ementa (temas de saúde mental, violência, exploração
  infantil, crimes etc.) — instrua o agente a tratar apenas no nível da ementa
  pública, sem aprofundar.
- Restrição de elegibilidade que pode gerar expectativa errada no lead.
```

## Alertas obrigatórios (revisão humana antes do merge)

Sempre que o pipeline gerar um arquivo com uma seção "Alertas", ou quando o
PDF de origem tiver informação ambígua/conflitante, **avise o usuário
explicitamente no final da execução** — não deixe isso só documentado dentro
do `.md`. O merge para `main` dispara reindexação automática, então conteúdo
errado vira resposta errada para um lead real.

## Regras de conteúdo (herdadas do README do sdr-agent-kb)

- Nunca inclua valor de curso, desconto ou condição de pagamento.
- Nunca prometa vaga garantida, aprovação garantida ou resultado de carreira.
- Nunca copie a ementa detalhada módulo a módulo na íntegra — resuma; o
  objetivo é dar contexto suficiente para o agente responder, não reproduzir o
  PDF inteiro.
- Se dois cursos tiverem a mesma coordenação e ementas parecidas, sempre
  adicione a referência cruzada nos "Alertas" de ambos.
