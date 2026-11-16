import pandas as pd
import streamlit as st

from src.fontes import alto_impacto, consultar_cnpj, ler_balanco_pdf, setor_do_cnae
from src.parecer import gerar_parecer
from src.score import Empresa, classificar

st.set_page_config(page_title="Crédito Verde ESG", page_icon="🌱", layout="wide")
st.title("🌱 Crédito Verde ESG")
st.caption("Análise de crédito PJ que combina saúde financeira e práticas sustentáveis.")

PADRAO = dict(nome="", setor="Outros", receita_anual=0.0, lucro_liquido=0.0, divida_total=0.0,
              ativo_circulante=0.0, passivo_circulante=0.0, dias_atraso_12m=0,
              licenca_ambiental=False, gestao_residuos=False, energia_renovavel_pct=0,
              inventario_emissoes=False, certificacoes=0, pct_mulheres_lideranca=0)
ss = st.session_state
for k, v in PADRAO.items():
    ss.setdefault(k, v)
ss.setdefault("cadastro", None)

with st.sidebar:
    st.subheader("Taxa")
    taxa_base = st.number_input("Taxa base da linha (% a.m.)", value=1.80, step=0.05)
    st.divider()
    st.caption("Quer só ver como funciona?")
    exemplos = pd.read_csv("data/empresas_exemplo.csv")
    ex = st.selectbox("Empresa de exemplo", exemplos["nome"], index=None, placeholder="Escolha...")
    if st.button("Carregar exemplo", disabled=ex is None):
        for k, v in exemplos[exemplos["nome"] == ex].iloc[0].to_dict().items():
            ss[k] = v.item() if hasattr(v, "item") else v
        ss.cadastro = None
        st.rerun()

# 1. Cadastro
st.header("1 · Empresa")
c1, c2 = st.columns([2, 1])
cnpj = c1.text_input("CNPJ", placeholder="00.000.000/0000-00")
if c2.button("Consultar na Receita", width="stretch"):
    try:
        cad = consultar_cnpj(cnpj)
        cad["alto_impacto"] = alto_impacto(cad["cnae"])
        ss.cadastro = cad
        ss.nome = cad["nome_fantasia"] or cad["razao_social"]
        ss.setor = setor_do_cnae(cad["cnae"])
    except Exception as e:
        st.error(str(e))

if ss.cadastro:
    cad = ss.cadastro
    a, b, c, d = st.columns(4)
    a.metric("Situação", cad["situacao"] or "—")
    b.metric("Abertura", cad["abertura"] or "—")
    c.metric("Porte", cad["porte"] or "—")
    d.metric("Local", f"{cad['municipio']}/{cad['uf']}")
    st.write(f"**{cad['razao_social']}** · CNAE {cad['cnae']} – {cad['cnae_descricao']}")
    if cad["alto_impacto"]:
        st.warning("Setor de alto impacto ambiental: licença ambiental obrigatória para a linha verde.")
st.text_input("Nome da empresa", key="nome")

# 2. Financeiro
st.header("2 · Dados financeiros")
pdf = st.file_uploader("Envie o balanço / DRE em PDF para preencher automaticamente (opcional)", type="pdf")
if pdf and st.button("Ler balanço"):
    achados = ler_balanco_pdf(pdf)
    if achados:
        for k, v in achados.items():
            ss[k] = float(abs(v)) if k != "lucro_liquido" else float(v)
        st.success(f"{len(achados)} campos preenchidos a partir do PDF. Confira abaixo.")
        st.rerun()
    else:
        st.error("Não reconheci as linhas do balanço neste PDF. Preencha manualmente.")

f1, f2, f3 = st.columns(3)
f1.number_input("Receita líquida anual (R$)", key="receita_anual", step=10000.0)
f1.number_input("Lucro líquido (R$)", key="lucro_liquido", step=10000.0)
f2.number_input("Ativo circulante (R$)", key="ativo_circulante", step=10000.0)
f2.number_input("Passivo circulante (R$)", key="passivo_circulante", step=10000.0)
f3.number_input("Dívida bancária total (R$)", key="divida_total", step=10000.0)
f3.number_input("Dias de atraso nos últimos 12 meses", key="dias_atraso_12m", step=1, min_value=0)

# 3. ESG
st.header("3 · Práticas ESG")
e1, e2 = st.columns(2)
e1.checkbox("Possui licença ambiental válida", key="licenca_ambiental")
e1.checkbox("Possui plano de gestão de resíduos", key="gestao_residuos")
e1.checkbox("Faz inventário de emissões de gases de efeito estufa", key="inventario_emissoes")
e2.slider("Energia de fonte renovável (%)", 0, 100, key="energia_renovavel_pct")
e2.slider("Mulheres em cargos de liderança (%)", 0, 100, key="pct_mulheres_lideranca")
e2.number_input("Certificações (ISO 14001, B Corp, selos...)", key="certificacoes", min_value=0, step=1)

# Resultado
st.header("Resultado")
if ss.receita_anual <= 0 or ss.passivo_circulante <= 0:
    st.info("Preencha pelo menos receita e passivo circulante para ver a análise.")
    st.stop()

dados = {k: ss[k] for k in PADRAO}
dados["nome"] = dados["nome"] or "Empresa analisada"
r = classificar(Empresa(**dados), taxa_base)

cad = ss.cadastro
if cad and str(cad.get("situacao", "")).upper() not in ("", "ATIVA"):
    r.update(faixa="E", decisao="Recusar: CNPJ não está ativo", elegivel_linha_verde=False)
if cad and cad["alto_impacto"] and not dados["licenca_ambiental"]:
    r["elegivel_linha_verde"] = False

k1, k2, k3, k4 = st.columns(4)
k1.metric("Faixa de risco", r["faixa"])
k2.metric("Score final", r["score_final"])
k3.metric("Taxa sugerida", f"{r['taxa_sugerida_mensal']}% a.m.", f"-{r['bonus_verde_pp']} p.p. bônus verde")
k4.metric("Linha verde", "Elegível ✅" if r["elegivel_linha_verde"] else "Não elegível")

g1, g2 = st.columns(2)
with g1:
    st.subheader(f"Financeiro · {r['score_financeiro']['total']}")
    st.table(pd.Series(r["score_financeiro"]["indicadores"], name="Valor").astype(str))
with g2:
    st.subheader(f"ESG · {r['score_esg']['total']}")
    st.bar_chart(pd.Series(r["score_esg"]["pilares"]))

st.divider()
st.markdown(gerar_parecer(r, dados, cad))
