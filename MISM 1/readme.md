# Monitoramento de Câncer de Mama — Rio Claro/SP

Plataforma de visualização geográfica de casos de câncer de mama no município de Rio Claro (SP), com mapa interativo por bairro e evolução histórica dos dados (2021–2025).

> **Status do projeto:** planejamento / definição de arquitetura. Ainda não há implementação de código.

## Objetivo

Disponibilizar um site público com um mapa interativo da cidade, onde cada bairro com incidência da doença pode ser clicado para exibir:
- Número de casos por ano (2021–2025)
- Tendência (aumento, queda ou estabilidade) ao longo do período

## Fontes de dados

| Fonte | Uso | Status |
|---|---|---|
| CSV extraído via [PySUS](https://github.com/AlertaDengue/PySUS) | Base de casos | Em mãos — **fonte exata (SISCAN/SIH/SIM) a confirmar** |
| CEP dos pacientes (respeitando a LGPD) | Associação caso → bairro | Em mãos |
| [ViaCEP](https://viacep.com.br/) | Tradução CEP → bairro | A implementar |
| Malha geográfica de bairros | Geometria para o mapa | Em definição (ver abaixo) |
| Censo IBGE 2022 (setores censitários / população) | Denominador para taxas, possível base da malha | A obter |

### ⚠️ Ponto em aberto: fonte real do PySUS

O PySUS não fornece um registro de incidência de câncer propriamente dito. É necessário confirmar qual sistema DATASUS foi usado na extração (SISCAN/SISMAMA, SIH ou SIM), pois isso muda a interpretação e a nomenclatura correta a ser usada no produto final (rastreamento ≠ diagnóstico confirmado ≠ mortalidade).

### ⚠️ Ponto em aberto: malha de bairros

- IBGE não delimita bairros oficialmente (apenas distritos/setores censitários).
- Prefeitura de Rio Claro **não possui** malha geográfica de bairros digitalizada (IPPLAN inexistente/sem esse dado).
- OpenStreetMap mapeia a maioria dos bairros apenas como pontos (*nodes*), não como polígonos — cobertura insuficiente para uso direto.
- **Caminho em avaliação:** verificar se Rio Claro está coberta pela [Malha de Bairros do Censo Demográfico 2022 (IBGE)](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/), que ajusta setores censitários a bairros legalmente instituídos. Se não estiver, alternativas: (1) usar setor censitário como unidade territorial, (2) consultar a Secretaria de Saúde sobre território de UBS/ESF (e-SUS Território), (3) desenho manual cruzando múltiplas fontes (CEP/ViaCEP, imobiliárias, conhecimento local).

## Arquitetura planejada

```
CSV PySUS + CEP dos pacientes
        │
        ▼
   ETL (Python)
   - Limpeza dos dados
   - CEP → bairro via ViaCEP (com cache)
   - Normalização de nomes de bairro
   - Agregação por bairro × ano
   - Cálculo de taxa (por 100 mil hab.) e tendência
        │
        ▼
PostgreSQL + PostGIS (Neon ou Supabase)
   - Tabela de bairros (geometria + população)
   - Tabela de casos agregados por bairro/ano
        │
        ▼
   API (Next.js — Route Handlers)
        │
        ▼
Frontend (Next.js + Leaflet, hospedado na Vercel)
   - Mapa coroplético por taxa de incidência
   - Clique no bairro → painel com série histórica e tendência
```

## Stack

- **ETL:** Python (pandas / geopandas)
- **Banco de dados:** PostgreSQL + extensão PostGIS
- **Hospedagem do banco:** Neon ou Supabase
- **Backend:** Next.js (API routes)
- **Frontend:** Next.js + React + Leaflet (react-leaflet)
- **Hospedagem do site:** Vercel

## Privacidade e LGPD

Dado de saúde é dado sensível. Diretrizes aplicadas ao projeto:

- O CEP bruto dos pacientes é usado **apenas na etapa de ETL**, para classificar cada caso em um bairro. Ele **não é armazenado** no banco de produção que alimenta o site.
- O banco público expõe **apenas dados agregados** (bairro, ano, contagem ou faixa) — nunca casos individuais.
- Bairros com poucos casos por ano estão sujeitos a **regra de supressão** (exibição em faixas em vez de números exatos), para evitar reidentificação.
- A metodologia e as fontes de dados devem estar documentadas e visíveis publicamente no site, incluindo o que exatamente está sendo medido (rastreamento, internação ou mortalidade).

## Roadmap

- [ ] Confirmar a fonte exata dos dados do PySUS (SISCAN/SIH/SIM)
- [ ] Resolver a malha geográfica de bairros (Censo IBGE 2022 / setor censitário / UBS-ESF)
- [ ] Implementar ETL: CEP → bairro via ViaCEP + cache
- [ ] Normalizar nomes de bairro entre fontes
- [ ] Modelar e popular o banco PostgreSQL/PostGIS
- [ ] Construir API
- [ ] Construir frontend com mapa interativo
- [ ] Definir e aplicar regra de supressão de números pequenos
- [ ] Deploy em produção (Vercel)
- [ ] Definir processo de atualização anual dos dados

## Estrutura do repositório (planejada)

```
├── etl/              # scripts de limpeza, geocodificação e agregação
├── db/                # schema e migrations (PostgreSQL/PostGIS)
├── api/               # rotas do backend (Next.js)
├── web/               # frontend (mapa, componentes)
└── docs/              # metodologia, fontes de dados, decisões
```

## Licença

A definir.

## Contato

A definir.
