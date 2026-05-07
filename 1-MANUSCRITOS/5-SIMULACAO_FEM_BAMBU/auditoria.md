Vou fazer uma leitura cirúrgica do manuscrito completo e depois montar a auditoria ponto a ponto.

 

Read [](file:///c%3A/Users/vidal/OneDrive/Documentos/13%20-%20CLONEGIT/artigo-posdoc/3-EROSIBIDADE/1-MANUSCRITOS/5-SIMULACAO_FEM_BAMBU/Simulacao_FEM_Bambu_EN.md#1-1), lines 1 to 250

Read [](file:///c%3A/Users/vidal/OneDrive/Documentos/13%20-%20CLONEGIT/artigo-posdoc/3-EROSIBIDADE/1-MANUSCRITOS/5-SIMULACAO_FEM_BAMBU/Simulacao_FEM_Bambu_EN.md#250-250), lines 250 to 292

Agora tenho o manuscrito completo. Vou montar a auditoria sênior ponto a ponto.

---

# AUDITORIA DE REVISOR SÊNIOR — Simulacao_FEM_Bambu_EN.md

**Revisor:** Diego Vidal (FEM + Geotecnia Ambiental)
**Alvo:** Q1 (Geotextiles and Geomembranes / Ecological Engineering / Catena)
**Método:** Leitura cirúrgica completa + comparação estrutural com Romano et al. (2016), Tardio & Mickovski (2017), Yang et al. (2024), He et al. (2024)

---

## BLOCO A — INCOERÊNCIAS DE DADOS (7 itens)

### A1. SF = 27 vs. 1/0.04 = 25
**Linha:** §3.1 — "FI_max = 0.04, SF = 27"
**Problema:** 1/0.04 = 25, não 27. Divergência de ~8%. Corrigir para 25 ou recalcular o FI que gerou SF=27 (FI=0.037).

### A2. Contradição entre nota da Fig. 3 e texto
**Linha:** nota da Fig. 3 diz "median hydrology and pessimistic degradation" mas o texto do §3.1 discute majoritariamente P95. A figura-âncora do artigo mostra o cenário mediano, enquanto o texto enfatiza o pior caso. O leitor não sabe qual regime a Fig. 3 representa sem ler a nota em letra miúda.

### A3. 42% no primeiro trimestre chuvoso — localização errada
**Linha:** §3.5 — "The concentration of 42% of the annual sediment input in the first rainy trimester..."
**Problema:** Esse dado é sobre dinâmica de sedimentos, não sobre deslocamento lateral. Está na subseção errada (3.5 Lateral displacement). Deveria estar em 3.4 (Temporal evolution) ou em uma subseção própria de "Field evidence".

### A4. Fig. 10 entra tarde e sem costura narrativa
**Linha:** §3.5 final — A Fig. 10 (evidência de campo: sediment wedge + cupins) aparece após 4 parágrafos de discussão de deslocamento, sem transição. O texto pula de "desiltation is the priority" para "the upstream sediment wedge progressively filled" sem conectivo. A figura é importante mas está mal posicionada.

### A5. Retenção empírica vs. modelo — validação frágil
**Linha:** §3.5 — "the absence of structural failures during the same period... indirectly corroborates the mechanical thresholds"
**Problema:** "Indirectly corroborates" é uma validação negativa (ausência de falha não prova que o modelo está certo, só que não está grosseiramente errado). Para Q1, isso é insuficiente. Romano et al. (2016) usam deslocamento medido vs. simulado com RMSE < 15%. Aqui não há métrica de erro.

### A6. Fator de vegetação (Eq. 2) inteiramente hipotético
**Linha:** §2.4 — "The parameters V_max, r, and t_m were adopted as hypothetical values"
**Problema:** Três parâmetros de uma equação que modula o carregamento hidrodinâmico são "hipotéticos". A análise de sensibilidade mitiga parcialmente, mas um revisor Q1 perguntará: por que não medir cobertura vegetal nas inspeções bianuais? Se há registro fotográfico padronizado, há material para estimar V_max.

### A7. SF > 2.7 no abstract vs. SF = 2.7 no texto
**Linha:** Abstract diz "SF remained above 2.7" e §3.1 diz "SF = 2.7" como pior caso.
**Problema:** "Above 2.7" implica > 2.7 estrito. Se o pior caso é exatamente 2.7 (ou 2.78 arredondado), o abstract deveria dizer "SF ≥ 2.7" ou "SF remained above 2.5".

---

## BLOCO B — PROBLEMAS ESTRUTURAIS (5 itens)

### B1. Métodos: dados de campo e modelo embolados
**Situação atual:** 2.1 mistura descrição do sítio, construção das paliçadas, resultados do monitoramento (eficiências de retenção, ANOVA, EI30) e thresholds hidrológicos.
**Padrão Q1:** Romano et al. (2016) e Tardio & Mickovski (2017) separam: (a) Study area + field data collection, (b) Model description, (c) Model calibration/validation strategy.
**Ação:** Separar 2.1 em duas subseções: "2.1 Study site and field monitoring" (só descrição) e "2.2 Field-derived model inputs" (eficiências, thresholds). Os resultados estatísticos do campo (ANOVA, concentração de 42%) vão para Results.

### B2. Results: temporal evolution aparece em 3 seções diferentes
**Situação atual:** A evolução temporal do FI é discutida em 3.1 (global response), 3.3 (stress concentration), e 3.4 (temporal evolution). A Fig. 5 é citada em 3.1 e 3.4. A Fig. 8 é citada em 3.3 e 3.4.
**Padrão Q1:** Yang et al. (2024) organizam: Global response → Parametric analysis → Failure mode → Temporal degradation → Design implications. Cada figura aparece em UMA subseção.
**Ação:** Consolidar toda a evolução temporal em 3.4. Mover Fig. 5 e Fig. 8 para lá. A Fig. 4 (collapse envelope) vai para subseção própria "3.5 Post-rupture behavior".

### B3. Collapse envelope (Fig. 4) no lugar errado
**Situação atual:** Fig. 4 está em 3.1 (Global structural response), mas é uma análise pós-ruptura com λ variando de 1 a 212. Não é "global response" — é "post-rupture progressive collapse".
**Padrão Q1:** Análises de colapso progressivo em FEM aparecem após a discussão de modos de falha, como subseção final de Results (He et al. 2024, Bacharoudis & Philippidis 2015).
**Ação:** Mover Fig. 4 para subseção própria após 3.4 (temporal evolution), renomeando para "3.5 Post-rupture progressive collapse".

### B4. Conclusão: um parágrafo único de 190 palavras
**Situação atual:** A conclusão é um bloco monolítico com 5 sentenças longas.
**Padrão Q1:** Conclusões em Ecological Engineering, Geotextiles and Geomembranes e Catena têm 3-4 parágrafos curtos: (1) síntese do achado principal, (2) implicação para prática/dimensionamento, (3) limitações, (4) trabalhos futuros.
**Ação:** Estruturar em 4 parágrafos conforme modelo Q1.

### B5. Ausência de subseção de limitações
**Situação atual:** Limitações estão diluídas ao longo do texto (Winkler, degradação uniforme, T_sat abrupto) e concentradas na última frase da conclusão.
**Padrão Q1:** Tardio & Mickovski (2017) e Romano et al. (2016) têm parágrafo dedicado "Model limitations" ou "Assumptions and caveats" ANTES da conclusão.
**Ação:** Inserir §3.6 "Model assumptions and limitations" antes de Conclusions.

---

## BLOCO C — SEQUÊNCIA PROPOSTA (REORGANIZAÇÃO)

### Methods
```
2.1 Study site and experimental system
2.2 Field monitoring and data collection
2.3 Geometric model and finite element discretisation
2.4 Material properties and degradation model
2.5 Loading model and hydrological scenarios
2.6 Failure criterion and simulation design
2.7 Statistical analysis
```

### Results and Discussion
```
3.1 Field-derived parameterisation (eficiências, ANOVA, thresholds, T_sat)
3.2 Global structural response and segment comparison (Fig. 3, Fig. 6)
3.3 Critical elements and failure mode hierarchy (Fig. 5, Fig. 7)
3.4 Temporal evolution and degradation-hydrology interaction (Fig. 5, Fig. 8)
3.5 Post-rupture progressive collapse (Fig. 4)
3.6 Lateral displacement and serviceability (Fig. 9)
3.7 Field evidence and maintenance implications (Fig. 10)
3.8 Model assumptions and limitations
```

---

## BLOCO D — MELHORIAS PARA Q1 (8 itens)

### D1. Inserir estudo de convergência de malha
Nenhum artigo Q1 de FEM publica resultados sem demonstrar independência de malha. Para o segmento MED (81 elementos, 72 nós), rodar a mesma configuração com 40, 81, 160 e 320 elementos e reportar a variação percentual do FI_max e do deslocamento máximo. Se a variação entre 81 e 160 elementos for < 3%, a malha atual é adequada.

### D2. Substituir "indirectly corroborates" por métrica quantitativa
Há duas opções: (a) comparar o deslocamento simulado nos primeiros 2 anos (< 2 mm) com a precisão da trena milimétrica usada nas inspeções (ex.: "simulated displacements remained below the 2 mm detection limit of the field tape measurements"), ou (b) reportar que as inspeções não detectaram deslocamento visível, o que é consistente com u < 2 mm.

### D3. Estimar V_max a partir dos registros fotográficos
Se há registros fotográficos padronizados das inspeções bianuais, é possível estimar a fração de cobertura vegetal na face da paliçada por classificação de imagem (threshold HSV ou Otsu). Isso substituiria o "hypothetical" por "estimated from field photographs".

### D4. Inserir tabela de parâmetros de carga
A carga hidrodinâmica depende de v (velocidade do fluxo), que não é declarada. O texto menciona C_d = 1.2 e ρ_w, mas não diz qual v foi usado para calcular q_d. Inserir tabela:
| Parameter | Symbol | Value | Unit | Source |
|-----------|--------|-------|------|--------|
| Flow velocity (P95) | v | ? | m/s | |
| Drag coefficient | C_d | 1.2 | - | |
| Debris impact (P95) | F_deb | 400 | N | |

### D5. Separar claramente o que é dado de campo do que é modelagem
Atualmente, as eficiências de retenção (1.12 a 1.97 × 10⁻⁴ cm/mm) são apresentadas em Methods como se fossem inputs, mas são o principal resultado do monitoramento de 2 anos. Isso enfraquece a contribuição experimental do artigo. Mover para Results 3.1 com a devida discussão.

### D6. Inserir comparação quantitativa com literatura de barreiras permeáveis
O texto compara qualitativamente com Piton et al. (2017), Nardin et al. (2010), Romano et al. (2016), mas não quantifica. Exemplo: "Romano et al. (2016) reported SF = 3-5 for timber check dams in semiarid basins; the SF ≥ 2.7 obtained here for bamboo under pessimistic degradation is comparable despite the lower initial strength of the material."

### D7. Mimetizar a estrutura de parágrafo de Romano et al. (2016)
Romano et al. (2016, Ecological Engineering) abrem cada subseção de Results com 1 frase de contexto, 2-3 frases de dado, 1 frase de interpretação mecânica, 1 frase de comparação com literatura. O presente manuscrito tem parágrafos longos que misturam dado, interpretação e literatura na mesma sentença.

### D8. Fig. 3 muito densa — considerar split
Cinco painéis (a-e) com geometria, mesh, 3 estágios temporais e pós-ruptura é excessivo para uma figura. Sugestão: Fig. 3 = (a) geometria + mesh + BCs, (b) t=5 yr, (c) t=10 yr. Fig. 4 = (a) t=11.5 yr incipient rupture, (b) λ=2.5 post-rupture. E a curva de colapso progressivo vira Fig. 5.

---

## BLOCO E — PLANO DE EXECUÇÃO (Checklist)

| # | Ação | Prioridade | Bloco |
|---|------|-----------|-------|
| 1 | Corrigir SF = 27 → 25 (ou recalcular FI) | Alta | A1 |
| 2 | Harmonizar nota da Fig. 3 com o texto (declarar cenário exato) | Alta | A2 |
| 3 | Mover "42% no primeiro trimestre" para 3.4 | Média | A3 |
| 4 | Criar transição para Fig. 10 | Média | A4 |
| 5 | Substituir "indirectly corroborates" por métrica quantitativa | Alta | A5, D2 |
| 6 | Estimar V_max de fotos ou declarar limitação com mais precisão | Média | A6, D3 |
| 7 | Corrigir "above 2.7" → "≥ 2.7" no abstract | Baixa | A7 |
| 8 | Separar 2.1 em "Study site" + "Field-derived inputs" | Alta | B1 |
| 9 | Consolidar evolução temporal em 3.4 | Alta | B2 |
| 10 | Mover Fig. 4 para subseção própria pós-3.4 | Alta | B3 |
| 11 | Estruturar conclusão em 4 parágrafos | Alta | B4 |
| 12 | Inserir §3.8 "Model assumptions and limitations" | Alta | B5 |
| 13 | Inserir estudo de convergência de malha | Média | D1 |
| 14 | Inserir tabela de parâmetros de carga com v explícito | Média | D4 |
| 15 | Mover eficiências de retenção para Results 3.1 | Alta | D5 |
| 16 | Inserir comparação quantitativa com SF da literatura | Média | D6 |
| 17 | Encurtar parágrafos conforme padrão Romano et al. (2016) | Média | D7 |
| 18 | Split Fig. 3 em duas figuras | Baixa | D8 |

---

## BLOCO F — DIAGNÓSTICO FINAL

O manuscrito tem um **núcleo sólido**: a pergunta é relevante (não há framework quantitativo para longevidade de paliçadas de bambu), o método é adequado (FEM 3D com Tsai-Hill ortotrópico + degradação exponencial + cenários hidrológicos), e os resultados são coerentes entre si (567 combinações, SF ≥ 2.7, estacas como elementos críticos, saturação precede falha).

Os problemas são **quase todos de apresentação e posicionamento**: dados de campo tratados como métodos, evolução temporal fragmentada em 3 seções, colapso progressivo no lugar errado, conclusão monolítica, validação apenas qualitativa. Nenhum desses problemas exige re-simulação — são resolvidos com reordenação e reescrita cirúrgica.

O gap mais sério para Q1 é a **ausência de convergência de malha** (D1) e a **validação apenas indireta** (D2). O primeiro se resolve com 3-4 rodadas adicionais do solver. O segundo exige decidir se o artigo se apresenta como "numerical framework" (dispensando validação experimental forte) ou como "validated model" (exigindo métrica de erro). Para Q1, recomendo o primeiro enquadramento, com a validação de campo tratada como "qualitative consistency check" e não como "experimental validation".

---

Quer que eu execute algum bloco específico primeiro? Recomendo começar pelos Blocos A (correções pontuais de dados) e B (reorganização estrutural), que são os de maior impacto e menor custo.