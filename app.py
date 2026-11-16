import pandas as pd
import streamlit as st

from src.fontes import alto_impacto, consultar_cnpj, ler_balanco_pdf, setor_do_cnae
from src.parecer import gerar_parecer
from src.score import Empresa, classificar
from src.ui import aplicar, barras, cabecalho, passo, selo

st.set_page_config(page_title="Crédito Verde ESG", page_icon="🌱", layout="wide")
aplicar("#15803d", "#0f766e")
cabecalho("🌱", "Crédito Verde ESG",
          "Análise de crédito PJ que une saúde financeira e práticas sustentáveis, com taxa bonificada para quem faz a diferença.")

PADRAO = dict(nome="", setor="Outros", receita_anual=0.0, lucro_liquido=0.0, divida_total=0.0,
              ativo_circulante=0.0, passivo_circulante=0.0, dias_atraso_12m=0,
              licenca_ambiental=False, gestao_residuos=False, energia_renovavel_pct=0,
              inventario_emissoes=False, certificacoes=0, pct_mulheres_lideranca=0)
ss = st.session_state
for k, v in PADRAO.items():
    ss.setdefault(k, v)
ss.setdefault("cadastro", None)
ss.setdefault("aviso", None)


def br(x, c=1):
    return f"{x:.{c}f}".replace(".", ",")


def brl(v):
    return f"R$ {v:,.0f}".replace(",", ".")


with st.sidebar:
    st.markdown("### ⚙️ Parâmetros")
    taxa_base = st.number_input("Taxa base da linha (% a.m.)", value=1.80, step=0.05, format="%.2f")
    st.divider()
    st.markdown("### 🧪 Conhecer a ferramenta")
    exemplos = pd.read_csv("data/empresas_exemplo.csv")
    ex = st.selectbox("Empresa de demonstração", exemplos["nome"], index=None, placeholder="Escolha...")
    if st.button("Carregar demonstração", disabled=ex is None, width="stretch"):
        for k, v in exemplos[exemplos["nome"] == ex].iloc[0].to_dict().items():
            ss[k] = v.item() if hasattr(v, "item") else v
        ss.cadastro = None
        st.rerun()
    with open("data/balanco_exemplo.pdf", "rb") as f:
        st.download_button("Baixar balanço em PDF de teste", f, "balanco_exemplo.pdf", width="stretch")
    st.caption("Dados de CNPJ: base pública da Receita Federal (BrasilAPI, CNPJ.ws e ReceitaWS).")

# 1 · Empresa
passo(1, "Empresa", "consulta na Receita Federal")
c1, c2 = st.columns([3, 1], vertical_alignment="bottom")
cnpj = c1.text_input("CNPJ", placeholder="00.000.000/0000-00")
if c2.button("🔎 Consultar CNPJ", type="primary", width="stretch"):
    with st.spinner("Consultando a Receita Federal..."):
        try:
            cad = consultar_cnpj(cnpj)
            cad["alto_impacto"] = alto_impacto(cad["cnae"])
            ss.cadastro = cad
            ss.nome = cad["nome_fantasia"] or cad["razao_social"]
            ss.setor = setor_do_cnae(cad["cnae"])
        except Exception as e:
            ss.cadastro = None
            st.error(str(e))

if ss.cadastro:
    cad = ss.cadastro
    ativa = str(cad["situacao"]).upper() == "ATIVA"
    st.markdown(
        f'<div class="cartao"><div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">'
        f'<div><div style="font-size:1.15rem;font-weight:700">{cad["razao_social"]}</div>'
        f'<div style="color:#6b7280">{cad["nome_fantasia"] or "—"} · CNPJ {cnpj}</div></div>'
        f'{selo(cad["situacao"] or "Sem situação", "ok" if ativa else "ru")}</div>'
        f'<hr style="margin:12px 0;border:none;border-top:1px solid #eef0f3">'
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;font-size:.92rem">'
        f'<div><b>Atividade</b><br>{cad["cnae_descricao"] or "—"}</div>'
        f'<div><b>Abertura</b><br>{cad["abertura"] or "—"}</div>'
        f'<div><b>Porte</b><br>{cad["porte"] or "—"}</div>'
        f'<div><b>Local</b><br>{cad["municipio"]}/{cad["uf"]}</div></div></div>', unsafe_allow_html=True)
    if cad["alto_impacto"]:
        st.warning("🏭 Setor de alto impacto ambiental: a licença ambiental é obrigatória para a linha verde.")
st.text_input("Nome da empresa", key="nome")

# 2 · Financeiro
passo(2, "Dados financeiros", "do último balanço")
up1, up2 = st.columns([3, 1], vertical_alignment="bottom")
pdf = up1.file_uploader("Balanço / DRE em PDF (opcional): os campos são preenchidos automaticamente", type="pdf")
if up2.button("📄 Ler balanço", disabled=pdf is None, width="stretch"):
    with st.spinner("Lendo o balanço..."):
        achados = ler_balanco_pdf(pdf)
    if achados:
        for k, v in achados.items():
            ss[k] = float(v) if k == "lucro_liquido" else float(abs(v))
        ss.aviso = f"✅ {len(achados)} campos preenchidos a partir do PDF. Confira os valores abaixo."
    else:
        ss.aviso = "⚠️ Não reconheci as linhas do balanço neste PDF (ele pode ser escaneado). Preencha manualmente."
    st.rerun()
if ss.aviso:
    (st.success if ss.aviso.startswith("✅") else st.warning)(ss.aviso)
    ss.aviso = None

f1, f2, f3 = st.columns(3)
f1.number_input("Receita líquida anual (R$)", key="receita_anual", step=10000.0, min_value=0.0)
f1.number_input("Lucro líquido (R$)", key="lucro_liquido", step=10000.0)
f2.number_input("Ativo circulante (R$)", key="ativo_circulante", step=10000.0, min_value=0.0)
f2.number_input("Passivo circulante (R$)", key="passivo_circulante", step=10000.0, min_value=0.0)
f3.number_input("Dívida bancária total (R$)", key="divida_total", step=10000.0, min_value=0.0)
f3.number_input("Dias de atraso nos últimos 12 meses", key="dias_atraso_12m", step=1, min_value=0)

# 3 · ESG
passo(3, "Práticas ESG", "ambiental, social e governança")
e1, e2 = st.columns(2)
with e1:
    st.checkbox("🌿 Possui licença ambiental válida", key="licenca_ambiental")
    st.checkbox("♻️ Possui plano de gestão de resíduos", key="gestao_residuos")
    st.checkbox("🌍 Faz inventário de emissões de gases de efeito estufa", key="inventario_emissoes")
    st.number_input("🏅 Certificações (ISO 14001, B Corp, selos...)", key="certificacoes", min_value=0, step=1)
with e2:
    st.slider("☀️ Energia de fonte renovável (%)", 0, 100, key="energia_renovavel_pct")
    st.slider("👩‍💼 Mulheres em cargos de liderança (%)", 0, 100, key="pct_mulheres_lideranca")

# Resultado
passo("✓", "Resultado da análise")
if ss.receita_anual <= 0 or ss.passivo_circulante <= 0:
    st.info("Preencha pelo menos **receita** e **passivo circulante** (ou envie o PDF do balanço) para ver a análise.")
    st.stop()

dados = {k: ss[k] for k in PADRAO}
dados["nome"] = dados["nome"] or "Empresa analisada"
r = classificar(Empresa(**dados), taxa_base)

cad = ss.cadastro
if cad and str(cad.get("situacao", "")).upper() not in ("", "ATIVA"):
    r.update(faixa="E", decisao="Recusar: CNPJ não está ativo na Receita", elegivel_linha_verde=False, bonus_verde_pp=0.0)
if cad and cad["alto_impacto"] and not dados["licenca_ambiental"]:
    r["elegivel_linha_verde"] = False

tipo = {"A": "ok", "B": "ok", "C": "at", "D": "at", "E": "ru"}[r["faixa"]]
st.markdown(f'<div class="cartao" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">'
            f'<div><span style="color:#6b7280">Decisão sugerida</span><br>'
            f'<span style="font-size:1.4rem;font-weight:800">{r["decisao"]}</span></div>'
            f'<div>{selo("Faixa " + r["faixa"], tipo)} &nbsp; '
            f'{selo("Linha verde: elegível", "ok") if r["elegivel_linha_verde"] else selo("Linha verde: não elegível", "ne")}</div></div>',
            unsafe_allow_html=True)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Score final", f"{br(r['score_final'])}/100")
k2.metric("Score financeiro", f"{br(r['score_financeiro']['total'])}/100")
k3.metric("Score ESG", f"{br(r['score_esg']['total'])}/100")
k4.metric("Taxa sugerida", f"{br(r['taxa_sugerida_mensal'], 2)}% a.m.",
          f"-{br(r['bonus_verde_pp'], 2)} p.p. bônus verde" if r["bonus_verde_pp"] else None)

g1, g2 = st.columns(2)
with g1:
    st.markdown("##### Indicadores financeiros")
    ind = r["score_financeiro"]["indicadores"]
    st.dataframe(pd.DataFrame({"Indicador": ind.keys(), "Valor": [br(v, 2 if isinstance(v, float) and k != "Margem líquida (%)" else 1) if isinstance(v, float) else str(v)
                                                 for k, v in ind.items()]}),
                 hide_index=True, width="stretch")
    st.caption(f"Receita {brl(dados['receita_anual'])} · Lucro {brl(dados['lucro_liquido'])} · Dívida {brl(dados['divida_total'])}")
with g2:
    st.markdown("##### Pilares ESG")
    if r["score_esg"]["total"] > 0:
        barras(pd.Series(r["score_esg"]["pilares"]), "#15803d", horizontal=True, altura=200)
    else:
        st.info("Nenhuma prática ESG informada ainda. Responda o passo 3 para pontuar.")

with st.container(border=True):
    st.markdown(gerar_parecer(r, dados, cad))
