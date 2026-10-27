"""Gera o mapa de Saúde da Mulher preservando o layout visual original.
Usa casos já classificados em casos_por_area_usf.csv e incorpora o GeoJSON USF
no HTML gerado, sem dependência de fetch externo para os polígonos.
"""
import json
from pathlib import Path
import pandas as pd

RAIZ_PROJETO = Path(__file__).resolve().parents[0]
CSV_PATH = RAIZ_PROJETO / "dados" / "processados" / "casos_por_area_usf.csv"
USF_GEOJSON_PATH = RAIZ_PROJETO / "dados" / "referencia" / "mapaRioClaroUSF.geojson"
MUNICIPIO_GEOJSON_PATH = RAIZ_PROJETO / "dados" / "referencia" / "municipio_rio_claro.geojson"
HTML_OUTPUT_PATH = RAIZ_PROJETO / "saidas" / "mapa_rio_claro_saude_mulher.html"
PARQUET_AIH = RAIZ_PROJETO.parent / "dados_parquet" / "aih" / "aih_cancer_mulheres.parquet"
PARQUET_GEO = RAIZ_PROJETO.parent / "dados_parquet" / "aih" / "aih_rio_claro_geo.parquet"


def texto(v, default=""):
    if pd.isna(v): return default
    return str(v).strip()

def numero(v, default=0.0):
    try:
        if pd.isna(v): return default
        s = str(v).strip().replace("R$", "").replace(" ", "")
        if not s: return default
        if "," in s and "." in s:
            # O separador mais à direita é tratado como separador decimal.
            if s.rfind(",") > s.rfind("."):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s:
            s = s.replace(",", ".")
        return float(s)
    except (ValueError, TypeError): return default

def carregar_casos():
    """Casos classificados, todos como texto (mesmo formato do casos_por_area_usf.csv).
    Lê do Parquet unificado (dados_parquet/aih); se ele não existir, usa o CSV de antes."""
    if PARQUET_GEO.exists() and PARQUET_AIH.exists():
        print(f"Lendo casos classificados: {PARQUET_GEO.resolve()}")
        geo = pd.read_parquet(PARQUET_GEO)
        chave = ["tipo_cancer", "N_AIH", "ANO_CMPT", "MES_CMPT", "DT_INTER"]
        aih = pd.read_parquet(PARQUET_AIH, columns=chave + ["DIAS_PERM", "MORTE", "DIAG_PRINC"],
                              filters=[("MUNIC_RES", "=", "354390")])
        df = geo.merge(aih, on=chave, how="left", validate="one_to_one")
        df = df.astype(object).where(df.notna(), None)
        return df.map(lambda v: v if v is None else str(v))
    if not CSV_PATH.exists(): raise FileNotFoundError(f"Arquivo necessário não encontrado: {CSV_PATH}")
    print(f"Lendo casos classificados: {CSV_PATH.resolve()}")
    return pd.read_csv(CSV_PATH, sep=";", dtype=str, low_memory=False)

def gerar_html():
    """Monta o HTML completo do mapa e o devolve como texto (usado pelo site e por main())."""
    for caminho in (USF_GEOJSON_PATH, MUNICIPIO_GEOJSON_PATH):
        if not caminho.exists(): raise FileNotFoundError(f"Arquivo necessário não encontrado: {caminho}")
    df = carregar_casos()
    with open(USF_GEOJSON_PATH, encoding="utf-8") as f: usf_geojson = json.load(f)
    with open(MUNICIPIO_GEOJSON_PATH, encoding="utf-8") as f: municipio_geojson = json.load(f)
    for c in ["LATITUDE", "LONGITUDE"]:
        if c not in df.columns: df[c] = pd.NA
        df[c] = df[c].map(lambda v: numero(v, float("nan")))
    for c in ["IDADE_ANOS", "VAL_TOT_NUM", "DIAS_PERM"]:
        if c not in df.columns: df[c] = 0
        df[c] = df[c].map(lambda v: numero(v, 0)).fillna(0)
    if "MORTE" not in df.columns: df["MORTE"] = "0"
    if "AREA_USF" not in df.columns: df["AREA_USF"] = "NÃO CLASSIFICADO"
    if "DOENCA" not in df.columns: df["DOENCA"] = "Não informado"
    if "ANO_INTERNACAO" not in df.columns: df["ANO_INTERNACAO"] = ""
    records = []
    for _, row in df.iterrows():
        lat, lon = row.get("LATITUDE"), row.get("LONGITUDE")
        if pd.isna(lat) or pd.isna(lon): continue
        if not (-90 <= float(lat) <= 90 and -180 <= float(lon) <= 180): continue
        idade = int(numero(row.get("IDADE_ANOS"), 0))
        valor = numero(row.get("VAL_TOT_NUM"), 0)
        records.append({
            "cep": texto(row.get("CEP_NORMALIZADO", row.get("CEP", ""))),
            "bairro": texto(row.get("AREA_USF", "NÃO CLASSIFICADO")),
            "area_usf": texto(row.get("AREA_USF", "NÃO CLASSIFICADO")) or "NÃO CLASSIFICADO",
            "logradouro": texto(row.get("LOGRADOURO", "")),
            "lat": round(float(lat), 6), "lng": round(float(lon), 6),
            "idade": idade, "ano": texto(row.get("ANO_INTERNACAO", ""))[:4],
            "valor": round(valor, 2), "dias": int(numero(row.get("DIAS_PERM"), 0)),
            "morte": texto(row.get("MORTE", "0")).lower() in {"1", "true", "sim", "s"},
            "cid": texto(row.get("DIAG_PRINC", "")), "cid_desc": "Neoplasia maligna",
            "doenca": texto(row.get("DOENCA", "Não informado")),
        })
    total_internacoes = len(records)
    idade_media = round(sum(r["idade"] for r in records if r["idade"] > 0) / max(1, sum(1 for r in records if r["idade"] > 0)), 1)
    custo_total = sum(r["valor"] for r in records)
    bairros_unicos = len(set(r["area_usf"] for r in records if r["area_usf"] and r["area_usf"] != "NÃO CLASSIFICADO"))
    json_records = json.dumps(records, ensure_ascii=False).replace("</", "<\\/")
    json_municipio_geojson = json.dumps(municipio_geojson, ensure_ascii=False).replace("</", "<\\/")
    json_usf_geojson = json.dumps(usf_geojson, ensure_ascii=False).replace("</", "<\\/")
    print(f"Casos com coordenadas no mapa: {len(records)}")
    print(f"Áreas USF no GeoJSON: {len(usf_geojson.get('features', []))}")
    print(f"HTML será salvo em: {HTML_OUTPUT_PATH.resolve()}")
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rio Claro (SP) - Saúde da Mulher - Mapa de Internações (2021-2025)</title>
    
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    
    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
    
    <!-- Phosphor Icons -->
    <script src="https://unpkg.com/@phosphor-icons/web"></script>

    <style>
        :root {{
            --bg-dark: #090d16;
            --surface-dark: rgba(15, 23, 42, 0.90);
            --surface-card: rgba(30, 41, 59, 0.78);
            --border-glass: rgba(255, 255, 255, 0.12);
            --border-accent: rgba(244, 63, 94, 0.45);
            
            --brand-pink: #f43f5e;
            --brand-pink-gradient: linear-gradient(135deg, #fb7185 0%, #e11d48 50%, #9f1239 100%);
            
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            
            --radius-lg: 18px;
            --radius-md: 12px;
            --radius-sm: 8px;
            --shadow-glass: 0 12px 40px 0 rgba(0, 0, 0, 0.5);
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Plus Jakarta Sans', sans-serif;
            -webkit-font-smoothing: antialiased;
        }}

        body, html {{
            width: 100%;
            height: 100%;
            overflow: hidden;
            background-color: var(--bg-dark);
            color: var(--text-primary);
        }}

        #map {{
            width: 100%;
            height: 100%;
            z-index: 1;
        }}

        .sidebar {{
            position: absolute;
            top: 16px;
            left: 16px;
            bottom: 16px;
            width: 450px;
            max-width: calc(100vw - 32px);
            background: var(--surface-dark);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-glass);
            z-index: 1000;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .sidebar.collapsed {{
            transform: translateX(-470px);
        }}

        .sidebar-header {{
            padding: 22px 24px;
            background: linear-gradient(180deg, rgba(244, 63, 94, 0.18) 0%, transparent 100%);
            border-bottom: 1px solid var(--border-glass);
            position: relative;
        }}

        .badge-pill {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(244, 63, 94, 0.22);
            border: 1px solid rgba(244, 63, 94, 0.45);
            color: #fca5a5;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 4px 10px;
            border-radius: 999px;
            margin-bottom: 8px;
        }}

        .badge-pill i {{
            font-size: 14px;
            color: #fb7185;
        }}

        .sidebar-header h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 22px;
            font-weight: 700;
            line-height: 1.25;
            color: #ffffff;
            margin-bottom: 4px;
        }}

        .sidebar-header p {{
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.4;
        }}

        .toggle-btn {{
            position: absolute;
            top: 20px;
            right: -48px;
            width: 44px;
            height: 44px;
            background: var(--surface-dark);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-glass);
            border-left: none;
            border-radius: 0 var(--radius-md) var(--radius-md) 0;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 22px;
            cursor: pointer;
            box-shadow: 4px 0 16px rgba(0,0,0,0.35);
            z-index: 1001;
            transition: all 0.2s;
        }}

        .toggle-btn:hover {{
            background: var(--brand-pink);
            color: #fff;
        }}

        .sidebar-content {{
            flex: 1;
            padding: 18px 22px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }}

        .sidebar-content::-webkit-scrollbar {{
            width: 6px;
        }}

        .sidebar-content::-webkit-scrollbar-thumb {{
            background: rgba(255, 255, 255, 0.18);
            border-radius: 3px;
        }}

        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }}

        .kpi-card {{
            background: var(--surface-card);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-md);
            padding: 12px 14px;
            display: flex;
            flex-direction: column;
            gap: 3px;
            transition: transform 0.2s, border-color 0.2s;
        }}

        .kpi-card:hover {{
            transform: translateY(-2px);
            border-color: var(--border-accent);
        }}

        .kpi-title {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .kpi-title i {{
            font-size: 15px;
            color: var(--brand-pink);
        }}

        .kpi-value {{
            font-family: 'Outfit', sans-serif;
            font-size: 22px;
            font-weight: 800;
            color: #fff;
            letter-spacing: -0.02em;
        }}

        .kpi-subtext {{
            font-size: 11px;
            color: var(--text-muted);
        }}

        .filter-section {{
            background: var(--surface-card);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-md);
            padding: 15px;
        }}

        .section-header {{
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--text-primary);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .section-header i {{
            color: var(--brand-pink);
            font-size: 16px;
        }}

        .filter-label {{
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            color: var(--text-secondary);
            margin-bottom: 6px;
            display: block;
        }}

        .chip-group {{
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
            margin-bottom: 12px;
        }}

        .chip {{
            padding: 5px 10px;
            font-size: 11px;
            font-weight: 600;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--border-glass);
            color: var(--text-secondary);
            cursor: pointer;
            transition: all 0.2s;
            user-select: none;
        }}

        .chip:hover {{
            background: rgba(244, 63, 94, 0.18);
            color: #fff;
            border-color: rgba(244, 63, 94, 0.45);
        }}

        .chip.active {{
            background: var(--brand-pink-gradient);
            color: #fff;
            border-color: transparent;
            box-shadow: 0 4px 12px rgba(244, 63, 94, 0.35);
        }}

        .layer-toggle-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }}

        .layer-toggle-row:last-child {{
            border-bottom: none;
            padding-bottom: 0;
        }}

        .layer-info {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 12px;
            font-weight: 500;
        }}

        .layer-info i {{
            font-size: 17px;
            color: var(--brand-pink);
        }}

        .switch {{
            position: relative;
            display: inline-block;
            width: 38px;
            height: 20px;
        }}

        .switch input {{
            opacity: 0;
            width: 0;
            height: 0;
        }}

        .slider {{
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(255, 255, 255, 0.18);
            transition: .25s;
            border-radius: 20px;
        }}

        .slider:before {{
            position: absolute;
            content: "";
            height: 14px;
            width: 14px;
            left: 3px;
            bottom: 3px;
            background-color: white;
            transition: .25s;
            border-radius: 50%;
        }}

        input:checked + .slider {{
            background-color: var(--brand-pink);
        }}

        input:checked + .slider:before {{
            transform: translateX(18px);
        }}

        .search-box {{
            display: flex;
            align-items: center;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-sm);
            padding: 6px 10px;
            margin-bottom: 10px;
            gap: 8px;
        }}

        .search-box i {{
            color: var(--text-muted);
            font-size: 15px;
        }}

        .search-box input {{
            background: transparent;
            border: none;
            outline: none;
            color: #fff;
            font-size: 12px;
            width: 100%;
        }}

        .search-box input::placeholder {{
            color: var(--text-muted);
        }}

        .bairro-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 8px 10px;
            background: rgba(255, 255, 255, 0.03);
            border-radius: var(--radius-sm);
            margin-bottom: 5px;
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid transparent;
        }}

        .bairro-item:hover {{
            background: rgba(244, 63, 94, 0.16);
            border-color: rgba(244, 63, 94, 0.35);
            transform: translateX(4px);
        }}

        .bairro-name {{
            font-size: 12px;
            font-weight: 500;
            color: var(--text-primary);
            max-width: 240px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .bairro-count-badge {{
            background: rgba(244, 63, 94, 0.25);
            color: #fca5a5;
            font-weight: 700;
            font-size: 11px;
            padding: 2px 7px;
            border-radius: 999px;
        }}

        .basemap-selector {{
            position: absolute;
            top: 16px;
            right: 16px;
            background: var(--surface-dark);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-md);
            padding: 5px;
            z-index: 1000;
            display: flex;
            gap: 4px;
            box-shadow: var(--shadow-glass);
        }}

        .basemap-btn {{
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 7px 12px;
            font-size: 12px;
            font-weight: 600;
            border-radius: var(--radius-sm);
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 5px;
            transition: all 0.2s;
        }}

        .basemap-btn:hover {{
            color: #fff;
            background: rgba(255, 255, 255, 0.08);
        }}

        .basemap-btn.active {{
            background: var(--brand-pink-gradient);
            color: #fff;
            box-shadow: 0 2px 8px rgba(244, 63, 94, 0.3);
        }}

        .leaflet-popup-content-wrapper {{
            background: #0f172a !important;
            color: #f8fafc !important;
            border: 1px solid rgba(244, 63, 94, 0.5) !important;
            border-radius: 14px !important;
            box-shadow: 0 12px 36px rgba(0, 0, 0, 0.7) !important;
            backdrop-filter: blur(12px) !important;
            padding: 0 !important;
            overflow: hidden !important;
        }}

        .leaflet-popup-content {{
            margin: 0 !important;
            min-width: 280px;
        }}

        .popup-card {{
            padding: 16px 18px;
        }}

        .popup-header {{
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 8px;
            margin-bottom: 10px;
        }}

        .popup-tag {{
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            color: #fb7185;
            letter-spacing: 0.05em;
        }}

        .popup-title {{
            font-family: 'Outfit', sans-serif;
            font-size: 16px;
            font-weight: 700;
            color: #ffffff;
            margin-top: 2px;
        }}

        .popup-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 7px;
            font-size: 12px;
        }}

        .popup-label {{
            color: var(--text-secondary);
        }}

        .popup-value {{
            font-weight: 600;
            color: var(--text-primary);
        }}

        .leaflet-popup-tip {{
            background: #0f172a !important;
            border: 1px solid rgba(244, 63, 94, 0.5) !important;
        }}

        .bairro-tooltip {{
            background: rgba(15, 23, 42, 0.92) !important;
            border: 1px solid rgba(244, 63, 94, 0.6) !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            padding: 6px 10px !important;
            font-size: 12px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5) !important;
        }}

        .bairro-tooltip:before {{
            border-top-color: rgba(15, 23, 42, 0.92) !important;
        }}

        .map-legend {{
            position: absolute;
            bottom: 24px;
            right: 16px;
            background: var(--surface-dark);
            backdrop-filter: blur(16px);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-md);
            padding: 14px 18px;
            z-index: 1000;
            font-size: 11px;
            box-shadow: var(--shadow-glass);
            display: flex;
            flex-direction: column;
            gap: 6px;
            min-width: 175px;
        }}

        .map-legend-title {{
            font-weight: 700;
            text-transform: uppercase;
            font-size: 10px;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 4px;
        }}

        .legend-scale-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 11px;
            color: var(--text-primary);
        }}

        .legend-color-box {{
            width: 16px;
            height: 12px;
            border-radius: 3px;
            border: 1px solid rgba(255,255,255,0.2);
        }}
    </style>
</head>
<body>

    <div id="map"></div>

    <div class="basemap-selector">
        <button class="basemap-btn active" onclick="setBasemap('light', this)">
            <i class="ph ph-sun"></i> Claro
        </button>
        <button class="basemap-btn" onclick="setBasemap('dark', this)">
            <i class="ph ph-moon"></i> Escuro
        </button>
        <button class="basemap-btn" onclick="setBasemap('satellite', this)">
            <i class="ph ph-planet"></i> Satélite
        </button>
        <button class="basemap-btn" onclick="setBasemap('osm', this)">
            <i class="ph ph-map-trifold"></i> Ruas
        </button>
    </div>

    <div class="map-legend">
        <div class="map-legend-title">Casos por Bairro</div>
        <div class="legend-scale-item">
            <span class="legend-color-box" style="background: #881337;"></span>
            <span>15+ casos (Muito Alta)</span>
        </div>
        <div class="legend-scale-item">
            <span class="legend-color-box" style="background: #e11d48;"></span>
            <span>10 - 14 casos (Alta)</span>
        </div>
        <div class="legend-scale-item">
            <span class="legend-color-box" style="background: #f97316;"></span>
            <span>6 - 9 casos (Média-Alta)</span>
        </div>
        <div class="legend-scale-item">
            <span class="legend-color-box" style="background: #facc15;"></span>
            <span>3 - 5 casos (Média)</span>
        </div>
        <div class="legend-scale-item">
            <span class="legend-color-box" style="background: #4ade80;"></span>
            <span>1 - 2 casos (Baixa)</span>
        </div>
        <div class="legend-scale-item">
            <span class="legend-color-box" style="background: #334155; opacity:0.5;"></span>
            <span>0 casos (no filtro)</span>
        </div>
    </div>

    <div class="sidebar" id="sidebar">
        <button class="toggle-btn" onclick="toggleSidebar()" title="Ocultar/Expandir Painel">
            <i class="ph ph-sidebar-simple" id="toggleIcon"></i>
        </button>

        <div class="sidebar-header">
            <div class="badge-pill">
                <i class="ph ph-heartbeat"></i> DATASUS - SIH/SUS SP
            </div>
            <h1>Rio Claro (SP)</h1>
            <p>Saúde da Mulher: Internações Oncologicas Multidoenças (2021 a 2025).</p>
        </div>

        <div class="sidebar-content">
            
            <div class="kpi-grid">
                <div class="kpi-card">
                    <span class="kpi-title"><i class="ph ph-users-three"></i> Internações</span>
                    <span class="kpi-value" id="kpiTotal">{total_internacoes}</span>
                    <span class="kpi-subtext">Casos com AIH registrada</span>
                </div>
                <div class="kpi-card">
                    <span class="kpi-title"><i class="ph ph-calendar"></i> Idade Média</span>
                    <span class="kpi-value" id="kpiIdade">{idade_media} <small style="font-size:13px; font-weight:500;">anos</small></span>
                    <span class="kpi-subtext">Todas as faixas etárias</span>
                </div>
                <div class="kpi-card">
                    <span class="kpi-title"><i class="ph ph-map-pin"></i> Bairros</span>
                    <span class="kpi-value" id="kpiBairros">{bairros_unicos}</span>
                    <span class="kpi-subtext">Fronteiras mapeadas</span>
                </div>
                <div class="kpi-card">
                    <span class="kpi-title"><i class="ph ph-currency-dollar"></i> Custo SUS</span>
                    <span class="kpi-value" id="kpiCusto">R$ {custo_total:,.0f}</span>
                    <span class="kpi-subtext">Total hospitalar pago</span>
                </div>
            </div>

            <div class="filter-section">
                <div class="section-header">
                    <span>Filtros Interativos</span>
                    <i class="ph ph-funnel"></i>
                </div>

                <span class="filter-label">Diagnóstico / Doença:</span>
                <div class="chip-group" id="filterDoenca">
                    <div class="chip active" onclick="filtrarDoenca('todas', this)">Todas (7)</div>
                    <div class="chip" onclick="filtrarDoenca('Câncer de Mama', this)">Mama</div>
                    <div class="chip" onclick="filtrarDoenca('Câncer do Colo do Útero', this)">Colo do Útero</div>
                    <div class="chip" onclick="filtrarDoenca('Câncer Colorretal', this)">Colorretal</div>
                    <div class="chip" onclick="filtrarDoenca('Câncer de Ovário', this)">Ovário</div>
                    <div class="chip" onclick="filtrarDoenca('Câncer de Pele (Não Melanoma)', this)">Pele (Não Mel.)</div>
                    <div class="chip" onclick="filtrarDoenca('Câncer de Pulmão', this)">Pulmão</div>
                    <div class="chip" onclick="filtrarDoenca('Câncer de Tireoide', this)">Tireoide</div>
                </div>

                <span class="filter-label">Ano da Internação:</span>
                <div class="chip-group" id="filterAno">
                    <div class="chip active" onclick="filtrarAno('todos', this)">Todos</div>
                    <div class="chip" onclick="filtrarAno('2021', this)">2021</div>
                    <div class="chip" onclick="filtrarAno('2022', this)">2022</div>
                    <div class="chip" onclick="filtrarAno('2023', this)">2023</div>
                    <div class="chip" onclick="filtrarAno('2024', this)">2024</div>
                    <div class="chip" onclick="filtrarAno('2025', this)">2025</div>
                </div>

                <span class="filter-label">Faixa Etária:</span>
                <div class="chip-group" id="filterIdade">
                    <div class="chip active" onclick="filtrarFaixa('todas', this)">Todas</div>
                    <div class="chip" onclick="filtrarFaixa('ate40', this)">&lt; 40</div>
                    <div class="chip" onclick="filtrarFaixa('40a49', this)">40 - 49</div>
                    <div class="chip" onclick="filtrarFaixa('50a59', this)">50 - 59</div>
                    <div class="chip" onclick="filtrarFaixa('60a69', this)">60 - 69</div>
                    <div class="chip" onclick="filtrarFaixa('70mais', this)">70+</div>
                </div>

                <span class="filter-label" style="margin-top: 10px;">Camadas no Mapa:</span>
                
                <div class="layer-toggle-row">
                    <div class="layer-info">
                        <i class="ph ph-polygon"></i>
                        <span>Áreas de Saúde (USF)</span>
                    </div>
                    <label class="switch">
                        <input type="checkbox" id="toggleBairros" checked onchange="atualizarCamadas()">
                        <span class="slider"></span>
                    </label>
                </div>

                <div class="layer-toggle-row">
                    <div class="layer-info">
                        <i class="ph ph-circles-three"></i>
                        <span>Casos agrupados por coordenada</span>
                    </div>
                    <label class="switch">
                        <input type="checkbox" id="toggleClusters" checked onchange="atualizarCamadas()">
                        <span class="slider"></span>
                    </label>
                </div>

                <div class="layer-toggle-row">
                    <div class="layer-info">
                        <i class="ph ph-flame"></i>
                        <span>Mancha de Calor Contínua (Heatmap)</span>
                    </div>
                    <label class="switch">
                        <input type="checkbox" id="toggleHeatmap" onchange="atualizarCamadas()">
                        <span class="slider"></span>
                    </label>
                </div>

                <div class="layer-toggle-row">
                    <div class="layer-info">
                        <i class="ph ph-shield-check"></i>
                        <span>Limite Municipal de Rio Claro</span>
                    </div>
                    <label class="switch">
                        <input type="checkbox" id="toggleMunicipio" checked onchange="atualizarCamadas()">
                        <span class="slider"></span>
                    </label>
                </div>
            </div>

            <div class="filter-section">
                <div class="section-header">
                    <span>Ranking das Áreas USF</span>
                    <i class="ph ph-buildings"></i>
                </div>

                <div class="search-box">
                    <i class="ph ph-magnifying-glass"></i>
                    <input type="text" id="bairroSearch" placeholder="Buscar área USF..." oninput="filtrarListaBairros(this.value)">
                </div>

                <div id="listaTopBairros" style="max-height: 220px; overflow-y: auto;">
                </div>
            </div>

        </div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
    <script src="https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js"></script>

    <script>
        const rawData = {json_records};
        const municipioGeoJSON = {json_municipio_geojson};
        const areasUSFGeoJSON = {json_usf_geojson};

        let filtroDoencaAtivo = 'todas';
        let filtroAnoAtivo = 'todos';
        let filtroFaixaAtiva = 'todas';
        let buscaBairroTexto = '';
        let listaBairrosAtual = [];
        let areasLayer = null, heatLayer = null, clusterGroup = null, municipioLayer = null;

        const centerRC = [-22.4149, -47.5614];
        const map = L.map('map', {{ center: centerRC, zoom: 12.8, zoomControl: false, minZoom: 10, maxZoom: 18 }});
        L.control.zoom({{ position: 'bottomright' }}).addTo(map);
        const basemaps = {{
            light: L.layerGroup([
                L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ attribution: 'Tiles &copy; Esri', maxZoom: 16 }}),
                L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ maxZoom: 16 }})
            ]),
            dark: L.layerGroup([
                L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ attribution: 'Tiles &copy; Esri', maxZoom: 16 }}),
                L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ maxZoom: 16 }})
            ]),
            satellite: L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}', {{ attribution: 'Tiles &copy; Esri', maxZoom: 18 }}),
            osm: L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{ attribution: '&copy; OpenStreetMap contributors', maxZoom: 19 }})
        }};
        let activeBasemap = basemaps.light;
        activeBasemap.addTo(map);
        function setBasemap(type, btnEl) {{
            if (activeBasemap) map.removeLayer(activeBasemap);
            activeBasemap = basemaps[type]; activeBasemap.addTo(map);
            document.querySelectorAll('.basemap-btn').forEach(btn => btn.classList.remove('active'));
            if (btnEl) btnEl.classList.add('active');
        }}
        municipioLayer = L.geoJSON(municipioGeoJSON, {{ style: {{ color: '#f43f5e', weight: 2.5, dashArray: '6, 6', fillOpacity: 0 }} }}).addTo(map);

        function toggleSidebar() {{ document.getElementById('sidebar').classList.toggle('collapsed'); }}
        function filtrarDoenca(doenca, el) {{
            filtroDoencaAtivo = doenca;
            document.querySelectorAll('#filterDoenca .chip').forEach(c => c.classList.remove('active'));
            el.classList.add('active'); aplicarFiltros();
        }}
        function filtrarAno(ano, el) {{
            filtroAnoAtivo = ano;
            document.querySelectorAll('#filterAno .chip').forEach(c => c.classList.remove('active'));
            el.classList.add('active'); aplicarFiltros();
        }}
        function filtrarFaixa(faixa, el) {{
            filtroFaixaAtiva = faixa;
            document.querySelectorAll('#filterIdade .chip').forEach(c => c.classList.remove('active'));
            el.classList.add('active'); aplicarFiltros();
        }}
        function filtrarListaBairros(texto) {{ buscaBairroTexto = texto.toLowerCase().trim(); renderizarListaBairros(); }}
        function atendeFiltros(item) {{
            if (filtroDoencaAtivo !== 'todas' && item.doenca !== filtroDoencaAtivo) return false;
            if (filtroAnoAtivo !== 'todos' && item.ano !== filtroAnoAtivo) return false;
            const id = item.idade;
            if (filtroFaixaAtiva === 'ate40' && id >= 40) return false;
            if (filtroFaixaAtiva === '40a49' && (id < 40 || id > 49)) return false;
            if (filtroFaixaAtiva === '50a59' && (id < 50 || id > 59)) return false;
            if (filtroFaixaAtiva === '60a69' && (id < 60 || id > 69)) return false;
            if (filtroFaixaAtiva === '70mais' && id < 70) return false;
            return true;
        }}
        function getCorPorCasos(n) {{
            if (n >= 15) return '#881337'; if (n >= 10) return '#e11d48';
            if (n >= 6) return '#f97316'; if (n >= 3) return '#facc15';
            if (n >= 1) return '#4ade80'; return '#334155';
        }}
        function nomeArea(feature) {{
            const p = feature && feature.properties ? feature.properties : {{}};
            return String(p.AREA_USF || p.area_usf || p.nome || p.NOME || p.name || 'Área sem nome');
        }}
        function escapar(s) {{ return String(s ?? '').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}
        function aplicarFiltros() {{
            const dados = rawData.filter(atendeFiltros);
            atualizarVisualizacao(dados); atualizarKPIs(dados);
        }}
        function atualizarKPIs(dados) {{
            const total = dados.length;
            const media = total ? dados.reduce((s,d)=>s+d.idade,0)/total : 0;
            const custo = dados.reduce((s,d)=>s+d.valor,0);
            document.getElementById('kpiTotal').textContent = total.toLocaleString('pt-BR');
            document.getElementById('kpiIdade').innerHTML = media.toFixed(1).replace('.', ',') + ' <small style="font-size:13px;font-weight:500">anos</small>';
            document.getElementById('kpiBairros').textContent = new Set(dados.map(d=>d.area_usf).filter(Boolean)).size.toLocaleString('pt-BR');
            document.getElementById('kpiCusto').textContent = 'R$ ' + custo.toLocaleString('pt-BR',{{maximumFractionDigits:0}});
        }}
        function renderizarListaBairros() {{
            const listEl = document.getElementById('listaTopBairros'); if (!listEl) return;
            listEl.innerHTML = '';
            const filtrados = listaBairrosAtual.filter(([nome]) => !buscaBairroTexto || nome.toLowerCase().includes(buscaBairroTexto));
            if (!filtrados.length) {{ listEl.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:8px;">Nenhuma área encontrada.</div>'; return; }}
            filtrados.forEach(([nome,count]) => {{
                const item=document.createElement('div'); item.className='bairro-item';
                item.innerHTML='<span class="bairro-name" title="'+escapar(nome)+'">'+escapar(nome)+'</span><span class="bairro-count-badge">'+count+' '+(count===1?'caso':'casos')+'</span>';
                item.onclick=()=>focarBairro(nome); listEl.appendChild(item);
            }});
        }}
        function focarBairro(nome) {{
            if (!areasLayer) return;
            areasLayer.eachLayer(layer => {{ if (nomeArea(layer.feature) === nome) {{ map.fitBounds(layer.getBounds(), {{maxZoom:15}}); layer.openPopup(); }} }});
            const p=rawData.filter(d=>d.area_usf===nome); if (p.length) map.setView([p[0].lat,p[0].lng],14);
        }}
        function popupArea(nome, stats, total) {{
            const n=stats ? stats.casos : 0, pct=total ? (n/total*100).toFixed(1) : '0.0';
            const idade=stats && stats.idades.length ? (stats.idades.reduce((a,b)=>a+b,0)/stats.idades.length).toFixed(1) : '-';
            const anos=stats ? [...stats.anos].sort().join(', ') : '-';
            const custo=stats ? stats.custo : 0;
            return '<div class="popup-card"><div class="popup-header"><span class="popup-tag">Área de Saúde (USF)</span><div class="popup-title">'+escapar(nome)+'</div></div>'+ 
                '<div class="popup-row"><span class="popup-label">Total de internações:</span><span class="popup-value">'+n+'</span></div>'+ 
                '<div class="popup-row"><span class="popup-label">Participação no filtro:</span><span class="popup-value">'+pct+'%</span></div>'+ 
                '<div class="popup-row"><span class="popup-label">Média de idade:</span><span class="popup-value">'+idade+' anos</span></div>'+ 
                '<div class="popup-row"><span class="popup-label">Anos registrados:</span><span class="popup-value">'+escapar(anos)+'</span></div>'+ 
                '<div class="popup-row"><span class="popup-label">Valor SUS total:</span><span class="popup-value">R$ '+custo.toLocaleString('pt-BR',{{minimumFractionDigits:2}})+'</span></div></div>';
        }}
        function atualizarVisualizacao(dados) {{
            if (areasLayer) map.removeLayer(areasLayer); if (heatLayer) map.removeLayer(heatLayer); if (clusterGroup) map.removeLayer(clusterGroup);
            const stats={{}};
            dados.forEach(d=>{{ const a=d.area_usf || 'NÃO CLASSIFICADO'; if(!stats[a]) stats[a]={{casos:0,idades:[],custo:0,anos:new Set()}}; stats[a].casos++; if(d.idade>0)stats[a].idades.push(d.idade); stats[a].custo+=d.valor; stats[a].anos.add(d.ano); }});
            const total=dados.length || 1;
            areasLayer=L.geoJSON(areasUSFGeoJSON, {{
                style: feature => {{ const n=stats[nomeArea(feature)]?.casos || 0; return {{color:n?'#ffffff':'#64748b',weight:n?1.5:0.8,opacity:n?0.85:0.4,fillColor:getCorPorCasos(n),fillOpacity:n?0.55:0.12}}; }},
                onEachFeature: (feature,layer) => {{ const nome=nomeArea(feature); layer.bindTooltip('<strong>'+escapar(nome)+'</strong><br><span style="color:#fb7185">'+(stats[nome]?.casos||0)+' casos</span>',{{sticky:true}}); layer.bindPopup(popupArea(nome,stats[nome],total)); layer.on({{mouseover:e=>e.target.setStyle({{weight:3,color:'#fb7185',fillOpacity:0.82}}),mouseout:e=>areasLayer.resetStyle(e.target)}}); }}
            }});
            const gruposCoord=new Map();
            dados.forEach(d=>{{const key=d.lat.toFixed(6)+','+d.lng.toFixed(6);if(!gruposCoord.has(key))gruposCoord.set(key,[]);gruposCoord.get(key).push(d);}});
            heatLayer=L.heatLayer([...gruposCoord.values()].map(g=>[g[0].lat,g[0].lng,g.length]),{{radius:26,blur:16,maxZoom:16,max:Math.max(1,...[...gruposCoord.values()].map(g=>g.length)),gradient:{{0.2:'#0055ff',0.4:'#00ffee',0.6:'#33ff33',0.8:'#ffee00',1:'#ff0044'}}}});
            clusterGroup=L.layerGroup();
            gruposCoord.forEach(g=>{{
                const first=g[0], n=g.length, areas=[...new Set(g.map(x=>x.area_usf).filter(Boolean))];
                const marker=L.circleMarker([first.lat,first.lng],{{radius:Math.min(7+Math.sqrt(n)*3,22),fillColor:getCorPorCasos(n),color:'#ffffff',weight:2,opacity:0.9,fillOpacity:0.85}});
                marker.bindTooltip(n+' '+(n===1?'caso':'casos')+' · '+g.length+' registros',{{direction:'top'}});
                const doencas=[...new Set(g.map(x=>x.doenca))].join(', '), ceps=[...new Set(g.map(x=>x.cep).filter(Boolean))].join(', ');
                marker.bindPopup('<div class="popup-card"><div class="popup-header"><span class="popup-tag">Casos agrupados por coordenada</span><div class="popup-title">'+n+' '+(n===1?'caso':'casos')+'</div></div><div class="popup-row"><span class="popup-label">Área USF:</span><span class="popup-value">'+escapar(areas.join(', ')||'Não classificado')+'</span></div><div class="popup-row"><span class="popup-label">CEP(s):</span><span class="popup-value">'+escapar(ceps||'Não informado')+'</span></div><div class="popup-row"><span class="popup-label">Doença(s):</span><span class="popup-value">'+escapar(doencas)+'</span></div></div>');
                clusterGroup.addLayer(marker);
            }});
            const ranking=Object.entries(stats).sort((a,b)=>b[1].casos-a[1].casos).map(([n,s])=>[n,s.casos]);
            listaBairrosAtual=ranking; renderizarListaBairros();
            if(document.getElementById('toggleBairros').checked) areasLayer.addTo(map);
            if(document.getElementById('toggleClusters').checked) clusterGroup.addTo(map);
            if(document.getElementById('toggleHeatmap').checked) heatLayer.addTo(map);
        }}
        function atualizarCamadas() {{
            const showAreas=document.getElementById('toggleBairros').checked, showCases=document.getElementById('toggleClusters').checked, showHeat=document.getElementById('toggleHeatmap').checked, showMunicipio=document.getElementById('toggleMunicipio').checked;
            if(areasLayer){{if(showAreas&&!map.hasLayer(areasLayer))map.addLayer(areasLayer);if(!showAreas&&map.hasLayer(areasLayer))map.removeLayer(areasLayer);}}
            if(clusterGroup){{if(showCases&&!map.hasLayer(clusterGroup))map.addLayer(clusterGroup);if(!showCases&&map.hasLayer(clusterGroup))map.removeLayer(clusterGroup);}}
            if(heatLayer){{if(showHeat&&!map.hasLayer(heatLayer))map.addLayer(heatLayer);if(!showHeat&&map.hasLayer(heatLayer))map.removeLayer(heatLayer);}}
            if(municipioLayer){{if(showMunicipio&&!map.hasLayer(municipioLayer))map.addLayer(municipioLayer);if(!showMunicipio&&map.hasLayer(municipioLayer))map.removeLayer(municipioLayer);}}
        }}
        [document.getElementById('toggleBairros'),document.getElementById('toggleClusters'),document.getElementById('toggleHeatmap'),document.getElementById('toggleMunicipio')].forEach(el=>el.addEventListener('change',atualizarCamadas));
        aplicarFiltros();
    </script>
</body>
</html>"""
    return html_content


def main():
    html_content = gerar_html()
    HTML_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HTML_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Mapa unificado gerado em: {HTML_OUTPUT_PATH.resolve()}")


if __name__ == "__main__":
    main()