"""Gera o parecer de crédito em texto a partir do resultado, sem depender de API externa."""

RECOMENDACOES_ESG = {
    "licenca_ambiental": ("Regularizar a licença ambiental", 35 * 0.5),
    "gestao_residuos": ("Implantar um plano de gestão de resíduos (PGRS)", 25 * 0.5),
    "inventario_emissoes": ("Fazer o inventário de emissões (GHG Protocol)", 15 * 0.5),
}


def gerar_parecer(r: dict, dados: dict, cadastro: dict | None = None) -> str:
    fin, esg = r["score_financeiro"], r["score_esg"]
    ind = fin["indicadores"]
    nome = (cadastro or {}).get("razao_social") or r["empresa"]

    fortes, atencao = [], []
    (fortes if ind["Margem líquida (%)"] >= 8 else atencao).append(f"margem líquida de {ind['Margem líquida (%)']}%")
    (fortes if ind["Liquidez corrente"] >= 1.2 else atencao).append(f"liquidez corrente de {ind['Liquidez corrente']}")
    (fortes if ind["Dívida / Receita"] <= 0.5 else atencao).append(f"dívida equivalente a {ind['Dívida / Receita']}x a receita")
    (fortes if ind["Dias de atraso (12m)"] <= 5 else atencao).append(f"{ind['Dias de atraso (12m)']} dias de atraso nos últimos 12 meses")
    for p, v in esg["pilares"].items():
        (fortes if v >= 60 else atencao).append(f"pilar {p} com {v} pontos")

    if cadastro:
        sit = str(cadastro.get("situacao", "")).upper()
        if sit and sit != "ATIVA":
            atencao.insert(0, f"situação cadastral **{sit}** na Receita Federal — impeditivo")
        if cadastro.get("alto_impacto"):
            atencao.append("setor de alto impacto ambiental: exigência ESG reforçada")

    recs = []
    for campo, (texto, ganho) in RECOMENDACOES_ESG.items():
        if not dados.get(campo):
            recs.append(f"{texto} (aprox. +{ganho:.0f} pts no score ESG)")
    if dados.get("energia_renovavel_pct", 0) < 50:
        recs.append("Ampliar o uso de energia renovável, ex.: solar (cada 10% ≈ +1,25 pt ESG)")
    if dados.get("certificacoes", 0) == 0:
        recs.append("Buscar uma primeira certificação (ISO 14001, B Corp, selo setorial)")
    if ind["Liquidez corrente"] < 1:
        recs.append("Reforçar capital de giro antes de novas captações de curto prazo")

    linha = "**é elegível**" if r["elegivel_linha_verde"] else "**ainda não é elegível**"
    t = [f"### Parecer de crédito — {nome}",
         f"**Decisão sugerida:** {r['decisao']} · Faixa **{r['faixa']}** · Score final **{r['score_final']}** "
         f"(financeiro {fin['total']} · ESG {esg['total']})",
         f"**Taxa sugerida:** {r['taxa_sugerida_mensal']}% a.m., já com bônus verde de {r['bonus_verde_pp']} p.p. "
         f"A empresa {linha} à linha de crédito verde.",
         "", "**Pontos fortes**"]
    t += [f"- {x}" for x in fortes] or ["- nenhum destaque"]
    t += ["", "**Pontos de atenção**"] + ([f"- {x}" for x in atencao] or ["- nenhum ponto crítico"])
    t += ["", "**Recomendações para a empresa reduzir a taxa**"] + ([f"- {x}" for x in recs] or ["- manter as práticas atuais"])
    return "\n".join(t)
