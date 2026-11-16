"""Camada de IA: transforma o resultado numérico em um parecer de crédito.

Funciona com OpenAI ou Anthropic (definidos por variável de ambiente).
Sem chave configurada, gera um parecer a partir de um modelo de texto,
para a demonstração nunca quebrar.
"""
import json
import os

PROMPT = """Você é um analista de crédito PJ sênior de uma cooperativa financeira,
especialista em finanças sustentáveis. Com base no resultado abaixo, escreva um
parecer de crédito em português, objetivo, com:
1. Resumo da decisão (2 linhas)
2. Pontos fortes
3. Pontos de atenção
4. Recomendações para a empresa melhorar o score ESG e reduzir a taxa
Não invente números além dos fornecidos.

Resultado:
{dados}
"""


def gerar_parecer(resultado: dict) -> str:
    dados = json.dumps(resultado, ensure_ascii=False, indent=2)
    prompt = PROMPT.format(dados=dados)

    if os.getenv("ANTHROPIC_API_KEY"):
        import anthropic
        cli = anthropic.Anthropic()
        msg = cli.messages.create(
            model=os.getenv("LLM_MODEL", "claude-sonnet-4-5"),
            max_tokens=900,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text

    if os.getenv("OPENAI_API_KEY"):
        from openai import OpenAI
        cli = OpenAI()
        r = cli.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
        )
        return r.choices[0].message.content

    return _parecer_offline(resultado)


def _parecer_offline(r: dict) -> str:
    fin, esg = r["score_financeiro"], r["score_esg"]
    pilares = esg["pilares"]
    fraco = min(pilares, key=pilares.get)
    forte = max(pilares, key=pilares.get)
    linha = "é elegível" if r["elegivel_linha_verde"] else "ainda não é elegível"
    return f"""**Resumo:** {r['empresa']} recebeu faixa **{r['faixa']}** (score final {r['score_final']}). Decisão sugerida: **{r['decisao']}**, com taxa de {r['taxa_sugerida_mensal']}% a.m.

**Pontos fortes:** score financeiro de {fin['total']} e melhor pilar ESG em {forte} ({pilares[forte]}).

**Pontos de atenção:** pilar {fraco} com {pilares[fraco]} pontos.

**Recomendações:** a empresa {linha} à linha de crédito verde. Evoluir o pilar {fraco} é o caminho mais rápido para ampliar o bônus verde (hoje {r['bonus_verde_pp']} p.p.).

_Parecer gerado em modo demonstração (sem chave de API)._"""
