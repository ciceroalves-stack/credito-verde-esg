# 🌱 Crédito Verde ESG

> Análise de crédito PJ que combina **saúde financeira** e **práticas ESG**, sugere uma **taxa bonificada** para empresas sustentáveis e entrega um **parecer de crédito pronto para o comitê**.
[LINK DO PROJETO](https://credito-verde-esg-lmjcrckkamk7gvujga8bcz.streamlit.app/)

## Problema de negócio

Bancos e cooperativas querem expandir carteiras de crédito sustentável, mas a análise ESG ainda é manual, subjetiva e demorada. Na prática, o gerente PJ não tem um critério padronizado para dizer *quanto* uma boa prática ambiental deve valer na taxa.

## Como funciona

1. **Consulta do CNPJ** na base pública da Receita Federal: razão social, situação cadastral, CNAE, porte e data de abertura. CNPJ inativo é recusado automaticamente.
2. **Leitura automática do balanço/DRE em PDF**: o sistema localiza receita líquida, lucro líquido, ativo e passivo circulante e endividamento, e preenche os campos sozinho.
3. **Questionário ESG**: licença ambiental, resíduos, emissões, energia renovável, diversidade na liderança e certificações.
4. **Score**: financeiro (70%) + ESG (30%), com faixa de risco de A a E.
5. **Precificação**: taxa base + ajuste de risco − **bônus verde** (até 0,30 p.p. a.m.).
6. **Parecer**: pontos fortes, pontos de atenção e o que a empresa precisa fazer para reduzir a taxa, com o ganho estimado de cada ação.

```
CNPJ ──► Receita Federal ─┐
PDF do balanço ──► leitura ├─► Score financeiro + ESG ──► Faixa + Taxa ──► Parecer
Questionário ESG ─────────┘
```

## Regras de segurança da análise

- **ESG não compensa financeiro ruim**: abaixo de 50 pontos financeiros não há bônus verde.
- **Setores de alto impacto ambiental** (identificados pelo CNAE) só entram na linha verde com licença ambiental.
- Todo número do resultado é rastreável até a regra que o gerou. Crédito precisa ser explicável.

## Como usar

Abra o app, digite um CNPJ real, envie o PDF do balanço (ou preencha os campos) e responda o questionário ESG. Para só conhecer a ferramenta, use **Carregar exemplo** na barra lateral, ou envie o arquivo `data/balanco_exemplo.pdf`.

Não precisa de nenhuma chave ou cadastro: a consulta de CNPJ usa a base pública da Receita Federal.

## Publicar

Em [share.streamlit.io](https://share.streamlit.io), crie um app apontando para este repositório e o arquivo `app.py`.

> Os pesos e faixas do score são ilustrativos e devem ser calibrados com o histórico de inadimplência da instituição. A leitura de PDF funciona com balanços que têm texto selecionável (não escaneados).
