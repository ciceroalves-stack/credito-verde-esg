# 🌱 Crédito Verde ESG

> Score de crédito PJ que combina **saúde financeira** e **práticas ESG**, sugere uma **taxa bonificada** para empresas sustentáveis e gera um **parecer de crédito com IA**.

## Problema de negócio

Bancos e cooperativas querem expandir carteiras de crédito sustentável, mas a análise ESG ainda é manual, subjetiva e demorada. Na prática, o gerente PJ não tem um critério padronizado para dizer *quanto* uma boa prática ambiental deve valer na taxa.

## Solução

1. **Score financeiro (70%)** — margem líquida, liquidez corrente, endividamento e pontualidade.
2. **Score ESG (30%)** — licença ambiental, resíduos, energia renovável, inventário de emissões, diversidade na liderança e certificações.
3. **Precificação** — taxa base + ajuste de risco − **bônus verde** (até 0,30 p.p. a.m.).
4. **Trava de segurança** — ESG nunca compensa um financeiro ruim: abaixo de 50 pontos financeiros não há bônus.
5. **Parecer com IA** — um LLM transforma os números em um parecer pronto para o comitê de crédito, com recomendações para a empresa melhorar.

```
Dados da empresa ──► Regras de score (auditáveis) ──► Faixa + Taxa ──► LLM ──► Parecer
```

**Por que regras + IA, e não só IA?** Decisão de crédito precisa ser explicável e auditável. A IA não decide o número; ela explica e recomenda.

## Resultado esperado

- Análise que levava horas cai para minutos.
- Critério ESG padronizado entre agências.
- Empresa recebe um caminho claro: "melhore X e sua taxa cai Y".

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

IA opcional: defina `OPENAI_API_KEY` ou `ANTHROPIC_API_KEY`. Sem chave, o app roda em modo demonstração.

## Estrutura

```
app.py                  Interface (Streamlit)
src/score.py            Regras de score e precificação
src/ia.py               Geração do parecer com LLM
data/empresas_exemplo.csv  5 empresas fictícias de setores diferentes
```

> Dados 100% fictícios. Pesos e faixas são ilustrativos e devem ser calibrados com histórico real de inadimplência.
