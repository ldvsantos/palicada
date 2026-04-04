# Propostas de Nova Chave de Classificação de Processos Erosivos em Plintossolos Tropicais

> Documento de trabalho — Abril 2026

## 1. Diagnóstico: Lacunas na Literatura

| Aspecto | Status na literatura |
|---|---|
| Chaves morfológicas (EGC, Poesen, Sidorchuk) | Existem, mas calibradas em ambientes temperados/semiáridos |
| Classificação processo-dominante para trópicos | **Lacuna explícita** |
| ML para *tipo* de ravina/voçoroca | **Inexistente** — há ML para susceptibilidade, nunca para tipologia |
| Integração de química do solo (Al, m%) como critério | **Nunca formalizada** em chave classificatória |
| Vínculo SiBCS ↔ tipologia erosiva | **Inexistente** |

### Referências-chave

- **EGC:** Thwaites et al. (2022) — *ESPL*, 47(1):109–128
- **Continuum sulco–ravina–voçoroca:** Poesen et al. (2003) — *Catena*, 50:91–133; Poesen (2018) — *ESPL*, 43:64–84
- **Morfodinâmica de estágios:** Sidorchuk (2006) — *ESPL*, 31:1329–1344
- **Contexto tropical brasileiro:** Cassol et al. (2023); Lafayette et al. (2011); de Oliveira et al. (2024)
- **Índice híbrido de vulnerabilidade:** Singh et al. (2023) — *LDD*, 34:3131–3149
- **Laterita/plintita:** Ghosh et al. (2022) — *Geology, Ecology, and Landscapes*, 6(3):188–216
- **Deep learning detecção:** Ganerod et al. (2023) — CNN para inventário (não tipologia)

## 2. Dados Disponíveis no Manuscrito

- **6 feições** com morfometria completa (profundidade 0.4–1.5 m, largura 1.3–2.4 m, comprimento 8–35 m)
- **Perfil edáfico** com 4 horizontes (Ap, AB, BAc, Bt): granulometria, pH, Al³⁺, V%, m%
- **VIB** em 3 posições da vertente (3.13, 1.53, 1.59 cm/h)
- **Série climatológica** 20 anos (2005–2025): P90 = 168.1 mm, P95 = 181.8 mm
- **Análise multitemporal** 16 anos (2007–2023)
- **PCA** morfométrica já realizada (Fig. 9)

## 3. Propostas

### Proposta 1 — Chave Determinística Processo-Funcional

Árvore de decisão rule-based que estende a EGC com bifurcações por processo dominante e condicionantes edafo-climáticos:

- **Nível 1 (Profundidade):** sulco / ravina / voçoroca
- **Nível 2 (Mecanismo dominante):** saturação-dominante / incisão-dominante / subsuperficial / regressão-dominante
- **Nível 3 (Vulnerabilidade funcional):** baixa / moderada / crítica (contagem de indicadores)

**Vantagem:** Publicável com dados atuais. Operacional em campo. Desloca classificação de rótulo → mecanismo.

### Proposta 2 — Classificação por Lógica Fuzzy

Resolve o continuum sulco–ravina–voçoroca com funções de pertinência:

- **Entradas:** profundidade, VIB, m_Al, P95, declividade
- **Conjuntos fuzzy:** "baixo/moderado/alto" com trapezoidais calibradas nos limiares empíricos
- **Regras Mamdani:** ~15-20 regras IF-THEN de expertise
- **Saída:** grau de pertinência simultâneo a sulco (0–1), ravina (0–1), voçoroca (0–1)

**Vantagem:** Resolve formalmente o "continuum problem" de Poesen. Funciona com n = 6 (regras de expertise, não data-driven).

### Proposta 3 — Clustering Exploratório + Framework ML (agenda futura)

- Clustering hierárquico e k-means sobre matriz normalizada (n = 6, exploratório)
- Framework CART/Random Forest para n > 30 (roadmap metodológico)

### Proposta 4 — Rede Bayesiana Processo-Resposta (mais ambiciosa)

- DAG causal: precipitação → escoamento → tensão cisalhante → incisão → morfologia
- Probabilidades condicionais de literatura + campo
- Inferência de trajetória evolutiva

## 4. Estratégia Adotada

**Combinar Proposta 1 + Proposta 2** como **Material Suplementar** do artigo principal:

- A chave determinística fornece estrutura operacional de campo
- A lógica fuzzy resolve formalmente o continuum
- O clustering entra como análise validatória dos agrupamentos
- Mantém o artigo principal focado na caracterização e nos limites da EGC

### Arquivos de implementação

- `scripts/classificacao_fuzzy_erosiva.py` — Sistema fuzzy + chave determinística + clustering
- Material suplementar em MD integrado ao artigo

## 5. Tabela-Resumo de Viabilidade

| Proposta | Esforço | Novidade | Dados atuais bastam? | Revista-alvo |
|---|---|---|---|---|
| 1. Chave determinística | Baixo | Moderada | **Sim** | Catena, ESPL |
| 2. Lógica Fuzzy | Moderado | **Alta** | **Sim** | Catena, Geomorphology |
| 3. Clustering + framework ML | Moderado | Alta | Parcial | LDD, RemSens |
| 4. Rede Bayesiana | Alto | **Muito alta** | Sim (conceitual) | ESPL, LDD |


## 3.5 Implicações para manejo e limitações

A operacionalização dos critérios em campo requer dados acessíveis na escala de manejo. A VIB é determinável por infiltrômetro de anéis concêntricos em ensaios de 120 minutos, a granulometria e os atributos químicos integram laudos pedológicos de rotina, e os limiares P90/P95 são deriváveis de séries meteorológicas disponíveis em estações automáticas regionais [@duarte_santos_castelhano_2021]. Feições com vulnerabilidade crítica podem beneficiar-se de barreiras permeáveis tipo paliçada para dissipação de energia e retenção de sedimentos [@lucas_borja_et_al_2021; @guerra_bezerra_jorge_2023], associadas à estabilização mecânica de taludes, ao passo que feições com vulnerabilidade moderada podem responder a práticas vegetativas de menor custo [@frankl_et_al_2021; @dagar_2018].

A classificação proposta não incorpora análise de estabilidade de taludes por métodos de equilíbrio limite (por exemplo, Morgenstern-Price), que permitiria quantificar o fator de segurança (FOS) das paredes das incisões sob diferentes cenários de saturação. Essa extensão requer parâmetros geotécnicos (coesão efetiva, ângulo de atrito, peso específico natural e saturado) obtidos em ensaios de cisalhamento direto ou triaxial, não realizados neste estudo. De modo análogo, o tamanho amostral (n = 6) impediu a aplicação de testes não paramétricos de comparação de grupos (por exemplo, Kruskal-Wallis), que poderiam avaliar se as diferenças morfométricas entre agrupamentos são estatisticamente significativas; um inventário ampliado pode viabilizar essa verificação.