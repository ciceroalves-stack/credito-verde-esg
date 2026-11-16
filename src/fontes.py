"""Fontes de dados reais, sem chave de API.

- Consulta de CNPJ na base pública da Receita Federal (BrasilAPI, com fallback).
- Leitura automática de balanço/DRE em PDF.
"""
import re

import requests

CNAE_SETOR = {
    "01": "Agropecuária", "02": "Agropecuária", "03": "Agropecuária",
    "10": "Agroindústria / Alimentos", "11": "Bebidas",
    "41": "Construção", "42": "Construção", "43": "Construção",
    "45": "Comércio de veículos", "46": "Comércio atacadista", "47": "Comércio varejista",
    "49": "Transporte / Logística", "52": "Transporte / Logística",
    "55": "Hospedagem", "56": "Alimentação",
    "62": "Tecnologia", "86": "Saúde",
}

# Setores com maior exposição a risco ambiental: exigência ESG mais rígida
SETOR_ALTO_IMPACTO = {"01", "02", "03", "05", "06", "07", "08", "10", "19", "20", "23", "24", "35", "38", "49"}


def cnpj_valido(num: str) -> bool:
    if len(num) != 14 or len(set(num)) == 1:
        return False
    def dv(base, pesos):
        r = sum(int(a) * b for a, b in zip(base, pesos)) % 11
        return "0" if r < 2 else str(11 - r)
    p1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = dv(num[:12], p1)
    d2 = dv(num[:12] + d1, [6] + p1)
    return num[12:] == d1 + d2


def consultar_cnpj(cnpj: str) -> dict:
    num = re.sub(r"\D", "", cnpj)
    if not cnpj_valido(num):
        raise ValueError("CNPJ inválido. Confira os números digitados.")

    fontes = (f"https://brasilapi.com.br/api/cnpj/v1/{num}",
              f"https://publica.cnpj.ws/cnpj/{num}",
              f"https://receitaws.com.br/v1/cnpj/{num}")
    nao_achou = 0
    for url in fontes:  # tenta todas: cada base pública às vezes falha ou está desatualizada
        try:
            r = requests.get(url, timeout=12, headers={"User-Agent": "credito-verde-esg"})
            if r.status_code == 200:
                j = r.json()
                if j.get("status") == "ERROR":  # receitaws responde 200 com erro
                    nao_achou += 1
                    continue
                return _normalizar(j, num)
            if r.status_code == 404:
                nao_achou += 1
        except (requests.RequestException, ValueError):
            continue
    if nao_achou == len(fontes):
        raise ValueError("CNPJ não encontrado na Receita Federal.")
    raise ConnectionError("As bases públicas de CNPJ não responderam agora. Tente de novo em 1 minuto "
                          "ou preencha o nome da empresa manualmente.")


def _normalizar(j: dict, num: str) -> dict:
    if "nome" in j and "atividade_principal" in j and isinstance(j["atividade_principal"], list):  # receitaws
        ativ = (j["atividade_principal"] or [{}])[0]
        return {
            "cnpj": num, "razao_social": j.get("nome", ""), "nome_fantasia": j.get("fantasia") or "",
            "cnae": re.sub(r"\D", "", ativ.get("code", "")).zfill(7), "cnae_descricao": ativ.get("text", ""),
            "situacao": j.get("situacao", ""), "abertura": j.get("abertura", ""), "porte": j.get("porte", ""),
            "municipio": j.get("municipio", ""), "uf": j.get("uf", ""),
        }
    if "razao_social" in j and "estabelecimento" in j:  # formato cnpj.ws
        est = j["estabelecimento"]
        cnae = re.sub(r"\D", "", str(est.get("atividade_principal", {}).get("id", ""))).zfill(7)
        return {
            "cnpj": num, "razao_social": j["razao_social"],
            "nome_fantasia": est.get("nome_fantasia") or "",
            "cnae": cnae, "cnae_descricao": est.get("atividade_principal", {}).get("descricao", ""),
            "situacao": est.get("situacao_cadastral", ""), "abertura": est.get("data_inicio_atividade", ""),
            "porte": (j.get("porte") or {}).get("descricao", ""),
            "municipio": (est.get("cidade") or {}).get("nome", ""), "uf": (est.get("estado") or {}).get("sigla", ""),
        }
    cnae = re.sub(r"\D", "", str(j.get("cnae_fiscal", ""))).zfill(7)
    return {
        "cnpj": num, "razao_social": j.get("razao_social", ""),
        "nome_fantasia": j.get("nome_fantasia") or "",
        "cnae": cnae, "cnae_descricao": j.get("cnae_fiscal_descricao", ""),
        "situacao": j.get("descricao_situacao_cadastral", ""), "abertura": j.get("data_inicio_atividade", ""),
        "porte": j.get("porte", "") or j.get("descricao_porte", ""),
        "municipio": j.get("municipio", ""), "uf": j.get("uf", ""),
    }


def setor_do_cnae(cnae: str) -> str:
    return CNAE_SETOR.get(cnae[:2], "Outros")


def alto_impacto(cnae: str) -> bool:
    return cnae[:2] in SETOR_ALTO_IMPACTO


# ---------------- leitura de balanço em PDF ----------------

CAMPOS = {
    "receita_anual": [r"receita\s+(operacional\s+)?l[ií]quida", r"receita\s+l[ií]quida\s+de\s+vendas", r"faturamento"],
    "lucro_liquido": [r"lucro\s*\(?preju[ií]zo\)?\s+l[ií]quido", r"(lucro|resultado)\s+l[ií]quido\s+do\s+exerc[ií]cio", r"lucro\s+l[ií]quido"],
    "ativo_circulante": [r"(total\s+do\s+)?ativo\s+circulante"],
    "passivo_circulante": [r"(total\s+do\s+)?passivo\s+circulante"],
    "emprestimos_cp": [r"empr[ée]stimos\s+e\s+financiamentos"],
    "passivo_nao_circulante": [r"(total\s+do\s+)?passivo\s+n[ãa]o\s+circulante", r"exig[ií]vel\s+a\s+longo\s+prazo"],
}

NUM = r"\(?-?\s?R?\$?\s?\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?\)?|\(?-?\d+(?:,\d{1,2})?\)?"


def _para_float(txt: str) -> float:
    neg = txt.strip().startswith("(") or "-" in txt
    limpo = re.sub(r"[^\d,]", "", txt).replace(",", ".")
    v = float(limpo) if limpo else 0.0
    return -v if neg else v


def ler_balanco_pdf(arquivo) -> dict:
    """Procura as linhas-chave do balanço e da DRE e devolve o primeiro valor de cada uma
    (normalmente o exercício mais recente)."""
    import pdfplumber

    with pdfplumber.open(arquivo) as pdf:
        texto = "\n".join((p.extract_text() or "") for p in pdf.pages)

    encontrados = {}
    for linha in texto.splitlines():
        baixa = linha.lower()
        for campo, padroes in CAMPOS.items():
            if campo in encontrados:
                continue
            if any(re.search(p, baixa) for p in padroes):
                numeros = [n for n in re.findall(NUM, linha) if re.search(r"\d{3}", n)]
                if numeros:
                    encontrados[campo] = _para_float(numeros[0])

    if "emprestimos_cp" in encontrados or "passivo_nao_circulante" in encontrados:
        encontrados["divida_total"] = abs(encontrados.pop("emprestimos_cp", 0)) + abs(encontrados.pop("passivo_nao_circulante", 0))
    return encontrados
