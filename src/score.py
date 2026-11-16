"""Motor de score: combina saúde financeira e práticas ESG de uma empresa PJ.

Regras transparentes e auditáveis — a IA só explica o resultado,
quem decide o número é a regra de negócio.
"""
from dataclasses import dataclass


@dataclass
class Empresa:
    nome: str
    setor: str
    receita_anual: float
    lucro_liquido: float
    divida_total: float
    ativo_circulante: float
    passivo_circulante: float
    dias_atraso_12m: int
    licenca_ambiental: bool
    gestao_residuos: bool
    energia_renovavel_pct: float  # 0-100
    inventario_emissoes: bool
    certificacoes: int
    pct_mulheres_lideranca: float  # 0-100


def _limitar(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


def score_financeiro(e: Empresa) -> dict:
    margem = e.lucro_liquido / e.receita_anual * 100 if e.receita_anual else 0
    liquidez = e.ativo_circulante / e.passivo_circulante if e.passivo_circulante else 3
    endiv = e.divida_total / e.receita_anual if e.receita_anual else 9

    pts_margem = _limitar(margem * 5)              # 20% de margem = 100
    pts_liquidez = _limitar((liquidez - 0.5) * 50)  # 2.5 = 100
    pts_endiv = _limitar(100 - endiv * 80)          # 0 = 100, 1.25x receita = 0
    pts_pontual = _limitar(100 - e.dias_atraso_12m * 3)

    total = 0.25 * pts_margem + 0.25 * pts_liquidez + 0.25 * pts_endiv + 0.25 * pts_pontual
    return {
        "total": round(total, 1),
        "indicadores": {
            "Margem líquida (%)": round(margem, 1),
            "Liquidez corrente": round(liquidez, 2),
            "Dívida / Receita": round(endiv, 2),
            "Dias de atraso (12m)": e.dias_atraso_12m,
        },
    }


def score_esg(e: Empresa) -> dict:
    ambiental = (
        (35 if e.licenca_ambiental else 0)
        + (25 if e.gestao_residuos else 0)
        + 0.25 * e.energia_renovavel_pct
        + (15 if e.inventario_emissoes else 0)
    )
    social = _limitar(e.pct_mulheres_lideranca * 2)  # 50% = 100
    governanca = _limitar(e.certificacoes * 34)
    total = 0.5 * _limitar(ambiental) + 0.25 * social + 0.25 * governanca
    return {
        "total": round(total, 1),
        "pilares": {
            "Ambiental": round(_limitar(ambiental), 1),
            "Social": round(social, 1),
            "Governança": round(governanca, 1),
        },
    }


def classificar(e: Empresa, taxa_base_mensal: float = 1.80) -> dict:
    fin = score_financeiro(e)
    esg = score_esg(e)
    final = round(0.7 * fin["total"] + 0.3 * esg["total"], 1)

    if fin["total"] < 40:
        faixa, decisao = "E", "Recusar ou exigir garantia real"
    elif final >= 80:
        faixa, decisao = "A", "Aprovar"
    elif final >= 65:
        faixa, decisao = "B", "Aprovar"
    elif final >= 50:
        faixa, decisao = "C", "Aprovar com limite reduzido"
    else:
        faixa, decisao = "D", "Análise manual do comitê"

    # Bônus verde: até 0,30 p.p. ao mês de desconto, só se o financeiro for aceitável
    bonus = round(0.30 * esg["total"] / 100, 2) if fin["total"] >= 50 else 0.0
    ajuste_risco = {"A": -0.20, "B": 0.0, "C": 0.35, "D": 0.70, "E": 1.20}[faixa]
    taxa = round(taxa_base_mensal + ajuste_risco - bonus, 2)

    return {
        "empresa": e.nome,
        "score_financeiro": fin,
        "score_esg": esg,
        "score_final": final,
        "faixa": faixa,
        "decisao": decisao,
        "bonus_verde_pp": bonus,
        "taxa_sugerida_mensal": taxa,
        "elegivel_linha_verde": esg["total"] >= 60 and fin["total"] >= 50,
    }
