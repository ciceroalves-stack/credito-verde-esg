import pandas as pd
import streamlit as st

from src.ia import gerar_parecer
from src.score import Empresa, classificar

st.set_page_config(page_title="Crédito Verde ESG", page_icon="🌱", layout="wide")
st.title("🌱 Crédito Verde ESG")
st.caption("Score de crédito PJ que combina saúde financeira e práticas sustentáveis.")

df = pd.read_csv("data/empresas_exemplo.csv")
nome = st.sidebar.selectbox("Empresa de exemplo", df["nome"])
base = df[df["nome"] == nome].iloc[0].to_dict()
taxa_base = st.sidebar.number_input("Taxa base (% a.m.)", value=1.80, step=0.05)

with st.expander("✏️ Dados da empresa (edite para simular)", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Financeiro**")
        base["receita_anual"] = st.number_input("Receita anual (R$)", value=float(base["receita_anual"]))
        base["lucro_liquido"] = st.number_input("Lucro líquido (R$)", value=float(base["lucro_liquido"]))
        base["divida_total"] = st.number_input("Dívida total (R$)", value=float(base["divida_total"]))
        base["ativo_circulante"] = st.number_input("Ativo circulante (R$)", value=float(base["ativo_circulante"]))
        base["passivo_circulante"] = st.number_input("Passivo circulante (R$)", value=float(base["passivo_circulante"]))
        base["dias_atraso_12m"] = st.number_input("Dias de atraso (12m)", value=int(base["dias_atraso_12m"]))
    with c2:
        st.markdown("**ESG**")
        base["licenca_ambiental"] = st.checkbox("Licença ambiental válida", value=bool(base["licenca_ambiental"]))
        base["gestao_residuos"] = st.checkbox("Plano de gestão de resíduos", value=bool(base["gestao_residuos"]))
        base["inventario_emissoes"] = st.checkbox("Inventário de emissões", value=bool(base["inventario_emissoes"]))
        base["energia_renovavel_pct"] = st.slider("Energia renovável (%)", 0, 100, int(base["energia_renovavel_pct"]))
        base["pct_mulheres_lideranca"] = st.slider("Mulheres na liderança (%)", 0, 100, int(base["pct_mulheres_lideranca"]))
        base["certificacoes"] = st.number_input("Certificações (ISO, B Corp...)", value=int(base["certificacoes"]))

r = classificar(Empresa(**base), taxa_base)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Faixa de risco", r["faixa"])
k2.metric("Score final", r["score_final"])
k3.metric("Taxa sugerida", f"{r['taxa_sugerida_mensal']}% a.m.", f"-{r['bonus_verde_pp']} p.p. bônus verde")
k4.metric("Linha verde", "Elegível ✅" if r["elegivel_linha_verde"] else "Não elegível")
st.info(f"**Decisão sugerida:** {r['decisao']}")

c1, c2 = st.columns(2)
with c1:
    st.subheader(f"Financeiro · {r['score_financeiro']['total']}")
    st.table(pd.Series(r["score_financeiro"]["indicadores"], name="Valor"))
with c2:
    st.subheader(f"ESG · {r['score_esg']['total']}")
    st.bar_chart(pd.Series(r["score_esg"]["pilares"]))

st.subheader("📝 Parecer de crédito")
if st.button("Gerar parecer com IA"):
    with st.spinner("Analisando..."):
        st.markdown(gerar_parecer(r))
