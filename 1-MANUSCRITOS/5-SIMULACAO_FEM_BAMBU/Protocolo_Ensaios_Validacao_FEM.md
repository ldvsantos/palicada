# Protocolo experimental para validação do modelo FEM de paliçadas de *Bambusa vulgaris*

## 1. Área de estudo e material vegetal

Todos os ensaios utilizam colmos de *Bambusa vulgaris* Schrad. ex J.C. Wendl. colhidos em touceiras adultas (idade de corte ≥ 3 anos) localizadas no entorno da Estação Experimental Campus Rural da Universidade Federal de Sergipe, São Cristóvão, SE (10°55'28,8" S; 37°11'58,9" O), fonte do mesmo material empregado na construção das paliçadas P1 a P4 instaladas sobre Plintossolo Argilúvico distrófico. A seleção dos colmos segue critérios de diâmetro externo compatível com o modelo FEM (90 a 110 mm), espessura de parede de 12 a 18 mm e ausência de danos mecânicos visíveis ou infestação por insetos. Os colmos são seccionados em segmentos de 1,0 m de comprimento, acondicionados em sacos plásticos e transportados ao laboratório no mesmo dia da colheita para minimizar variação de umidade. As coordenadas de colheita, o diâmetro externo, a espessura de parede e a posição do entrenó são registradas para cada segmento, assegurando rastreabilidade entre corpo de prova e colmo de origem.

Os ensaios de campo são conduzidos nas paliçadas P1 a P4 já instaladas na ravina, com foco no segmento MED (L = 3,00 m, H = 0,76 m, três estacas espaçadas 1,50 m), que concentra os maiores índices de falha previstos pelo modelo ($FI_{max} = 0{,}36$ a $t = 10$ anos sob degradação pessimista).

## 2. Ensaio de cisalhamento interlaminar — regiões nodal e internodal

### 2.1 Objetivo

Determinar a resistência ao cisalhamento interlaminar ($\tau_{LR}$) de corpos de prova de *B. vulgaris* extraídos de regiões internodais e nodais, quantificando o fator de redução nodal real comparando o valor adotado a partir da literatura de *Phyllostachys edulis* e *Guadua angustifolia*. A resistência ao cisalhamento responde por 98% do índice de Tsai-Hill no elemento crítico do modelo FEM, tornando $\tau_{LR}$ o parâmetro de maior sensibilidade do sistema.

### 2.2 Norma de referência

ASTM D2344/D2344M — *Standard Test Method for Short-Beam Strength of Polymer Matrix Composite Materials and Their Laminates*, adaptada para material natural ortotrópico conforme recomendações de Shao et al. (2010) e Meng et al. (2023). A norma ISO 22157:2019 (*Bamboo structures — Determination of physical and mechanical properties of bamboo culms*) é consultada como referência complementar para geometria de corpos de prova de bambu.

### 2.3 Preparação dos corpos de prova

De cada colmo selecionado, dois tipos de corpo de prova são extraídos com serra de bancada refrigerada: (a) internodal, extraído do terço central do entrenó, e (b) nodal, centrado no diafragma do nó. As dimensões nominais seguem a relação span/thickness = 4 prescrita pela ASTM D2344 para ensaio de viga curta (short beam shear): comprimento $L = 4h + 2$ mm, largura $b = h$, espessura $h$ = espessura de parede do colmo (12 a 18 mm). O plano de cisalhamento é orientado na direção longitudinal-radial (L-R), coincidente com o plano de falha interlaminar do modelo FEM. São preparados no mínimo 10 corpos de prova internodais e 10 nodais por colmo, totalizando no mínimo 5 colmos (100 corpos de prova). A umidade de equilíbrio é estabilizada em câmara climatizada a 20 ± 2 °C e 65 ± 5% UR por 72 h antes do ensaio, com registro individual de massa e dimensões por paquímetro digital (resolução 0,01 mm).

### 2.4 Procedimento de ensaio

Os corpos de prova são posicionados em dispositivo de flexão de três pontos com rolos de apoio de 6 mm de diâmetro e rolo de carga de 6 mm, montados em máquina universal de ensaios (capacidade mínima de 10 kN, célula de carga Classe 1 conforme ISO 7500-1). A velocidade de carregamento é de 1,0 mm/min. O ensaio prossegue até ruptura ou queda de 30% da carga máxima registrada.

### 2.5 Grandezas medidas e cálculo

A resistência ao cisalhamento interlaminar aparente é calculada por $\tau_{LR} = 0{,}75 \cdot F_{max} / (b \cdot h)$, onde $F_{max}$ é a carga máxima registrada. O fator de redução nodal é obtido pela razão $\bar{\tau}_{nodal} / \bar{\tau}_{internodal}$. São reportados média, desvio padrão, coeficiente de variação e intervalo de confiança de 95% para cada região. O teste t de Student (ou Mann-Whitney U, se a normalidade for rejeitada pelo teste de Shapiro-Wilk a $\alpha = 0{,}05$) avalia a significância da diferença entre regiões.

## 3. Ensaio de degradação acelerada *in situ*

### 3.1 Objetivo

Determinar a taxa de decaimento real ($k$) das propriedades mecânicas de *B. vulgaris* em contato com Plintossolo Argilúvico úmido, verificando se a degradação da resistência ao cisalhamento interlaminar ($k_\tau$) difere significativamente da degradação da resistência à flexão ($k_\sigma$). O modelo FEM atual adota $k$ uniforme para todas as propriedades, simplificação reconhecida como potencialmente não conservadora para o modo cisalhante.

### 3.2 Delineamento experimental

Corpos de prova padronizados (Seção 2.3 para cisalhamento e Seção 4.3 para flexão) são extraídos de colmos frescos e distribuídos em dois tratamentos: (a) enterrados a 15 cm de profundidade no Plintossolo do leito da ravina, na posição adjacente às paliçadas existentes, simulando a condição de exposição real das estacas e da tora basal; (b) controle, armazenados em câmara climatizada (20 ± 2 °C, 65 ± 5% UR). Os corpos de prova enterrados são acondicionados em sacos de tela (mesh 2 mm) que permitem contato com solo e biota sem perda de fragmentos, com identificação individual por plaqueta de aço inoxidável.

O período de monitoramento é de 30 meses, com retiradas destrutivas a cada 6 meses ($t = 0$, 6, 12, 18, 24 e 30 meses), resultando em 6 instantes de amostragem. Em cada retirada, 10 corpos de prova de cisalhamento (5 nodais + 5 internodais) e 10 de flexão são extraídos do solo, limpos com escova macia, acondicionados em câmara climatizada por 72 h e ensaiados conforme as Seções 2.4 e 4.4. O controle ($t = 0$) utiliza 10 + 10 corpos de prova ensaiados no dia da instalação. O total estimado é de 120 corpos de prova (60 de cisalhamento + 60 de flexão), acrescidos de 20 controles.

### 3.3 Análise dos dados e calibração de $k$

Para cada propriedade mecânica ($\tau_{LR}$ e $\sigma_{tL}$), o valor médio normalizado pelo controle ($P(t)/P_0$) é ajustado pelo modelo exponencial $P(t)/P_0 = e^{-k \cdot t}$ (Equação 1 do manuscrito), estimando $k$ por regressão não linear (mínimos quadrados) com intervalo de confiança de 95% para o parâmetro. A hipótese de degradação diferencial ($k_\tau \neq k_\sigma$) é testada pela comparação dos intervalos de confiança de $k_\tau$ e $k_\sigma$ e, complementarmente, pelo teste F de modelos encaixados (modelo com $k$ único *vs.* modelo com $k$ diferencial). A taxa de afinamento de parede (mm/mês) é estimada pela medição da espessura residual dos corpos de prova a cada retirada, com paquímetro digital em três posições equidistantes, e comparada ao valor de 1 mm ano$^{-1}$ adotado no modelo.

Adicionalmente, em cada retirada, os corpos de prova enterrados são fotografados em escala padronizada (resolução mínima de 300 dpi) e a perda de massa é registrada (balança analítica, resolução 0,01 g) para correlação com a degradação mecânica.

### 3.4 Monitoramento ambiental

Um sensor de temperatura e umidade do solo (tipo capacitivo, resolução 0,1 °C / 0,1% v/v) é instalado a 15 cm de profundidade, adjacente aos corpos de prova, com registro horário em datalogger autônomo. Precipitação diária é obtida da estação meteorológica automática de Aracaju-SE (INMET). Essas variáveis possibilitam correlacionar a taxa de degradação com as condições ambientais locais.

## 4. Ensaio de flexão estática em colmos inteiros

### 4.1 Objetivo

Determinar o módulo de elasticidade longitudinal ($E_L$), a resistência à flexão ($\sigma_{fL}$) e a resistência à compressão longitudinal ($\sigma_{cL}$) de colmos de *B. vulgaris* do sítio experimental, substituindo os valores da literatura ($E_L = 12$ GPa, $\sigma_{tL} = 180$ MPa) por medições diretas com estimativa de variabilidade (média ± desvio padrão), ausente na Tabela 1 do modelo FEM.

### 4.2 Norma de referência

ISO 22157:2019 — *Bamboo structures — Determination of physical and mechanical properties of bamboo culms*, Seção 11 (flexão), complementada pela ASTM D3043 — *Standard Test Methods for Structural Panels in Flexure*. A relação span/diâmetro é mantida entre 20 e 30 para minimizar contribuição do cisalhamento na deformação.

### 4.3 Preparação dos corpos de prova

Segmentos de colmo inteiro com comprimento de 600 a 900 mm (mínimo de 2 entrenós completos), diâmetro externo de 90 a 110 mm e espessura de parede de 12 a 18 mm são selecionados conforme os critérios da Seção 1. São ensaiados no mínimo 15 colmos (5 de cada classe de diâmetro: 90–95 mm, 96–102 mm, 103–110 mm), com umidade de equilíbrio estabilizada em câmara climatizada. As dimensões (diâmetro externo, diâmetro interno, espessura de parede, comprimento) são medidas por paquímetro digital em três seções (apoio esquerdo, centro, apoio direito), com três repetições por seção. Momento de inércia e módulo de seção são calculados com base na geometria tubular oca média.

### 4.4 Procedimento de ensaio

Ensaio de flexão em quatro pontos conforme ISO 22157:2019, com distância entre apoios ($L_{span}$) de 20 a 30 vezes o diâmetro externo médio, e distância entre pontos de carga de $L_{span}/3$. O carregamento é aplicado por máquina universal de ensaios (capacidade mínima de 50 kN) com velocidade de deslocamento de 5 mm/min. O deslocamento no centro do vão é medido por extensômetro LVDT (curso 50 mm, resolução 0,01 mm) fixado em suporte independente. O ensaio prossegue até ruptura ou queda de 30% da carga máxima.

### 4.5 Grandezas medidas e cálculo

O módulo de elasticidade longitudinal é calculado pela inclinação da região linear da curva carga-deslocamento: $E_L = \frac{23 \Delta F \cdot L_{span}^3}{1296 \cdot \Delta \delta \cdot I}$, onde $\Delta F / \Delta \delta$ é a taxa de carga-deslocamento no trecho linear e $I$ é o momento de inércia médio da seção tubular oca. A resistência à flexão é $\sigma_{fL} = M_{max} \cdot c / I$, onde $M_{max}$ é o momento máximo e $c$ é a distância da fibra extrema ao eixo neutro. São reportados média, desvio padrão e coeficiente de variação para $E_L$, $\sigma_{fL}$ e $\sigma_{cL}$ (obtida pela face comprimida), com testes de normalidade (Shapiro-Wilk) e ANOVA unidirecional para avaliar efeito da classe de diâmetro.

## 5. Ensaio de rigidez rotacional da conexão arame-colmo-estaca

### 5.1 Objetivo

Determinar a rigidez rotacional ($k_\theta$, em kN·m/rad) da conexão colmo-estaca por arame recozido, em condição de montagem recente (pós-instalação) e após 8 meses de exposição em campo (pré-manutenção), quantificando a degradação da conexão ao longo do ciclo de manutenção. O modelo FEM atual idealiza essa conexão como junta rígida (12 DOF compartilhados), com análise paramétrica indicando que a redução para 10% da rigidez de referência eleva o FI máximo a 0,40.

### 5.2 Montagem do aparato de ensaio

O ensaio é conduzido em configuração de bancada que reproduz a geometria de campo. Uma estaca vertical de *B. vulgaris* (diâmetro externo 100 mm, comprimento 600 mm) é fixada em base rígida com engaste a 300 mm de profundidade (bloco de concreto armado com parafusos laterais). Um colmo horizontal (mesmas dimensões) é amarrado à estaca com arame recozido n.° 18 (diâmetro 1,24 mm), utilizando o mesmo padrão de amarração executado nas paliçadas de campo (três voltas cruzadas com torção manual). A extremidade livre do colmo horizontal funciona como braço de alavanca para aplicação do momento.

### 5.3 Procedimento de ensaio

Uma carga transversal crescente é aplicada na extremidade livre do colmo horizontal (braço de alavanca de 400 mm) por meio de tração controlada com célula de carga (capacidade 2 kN, Classe 1). A rotação relativa entre colmo e estaca é medida por dois inclinômetros digitais (resolução 0,01°) fixados a 50 mm de cada lado da junção com adesivo cianoacrilato e fita metálica. A velocidade de carregamento é de 0,5 mm/min. O ensaio é conduzido em ciclos de carga-descarga (0 → 100 N → 0, repetido 3 vezes para acomodação) seguidos de carregamento monotônico até deslizamento visível ou rotação relativa de 5°.

O momento aplicado é $M = F \times d$, onde $F$ é a carga transversal e $d = 0{,}400$ m é o braço. A rigidez rotacional é obtida pela inclinação da região linear da curva momento-rotação: $k_\theta = \Delta M / \Delta \theta$ (kN·m/rad).

### 5.4 Tratamentos e repetições

São ensaiadas no mínimo 10 junções em condição nova (montadas no laboratório no dia do ensaio) e 10 junções retiradas de campo após 8 meses de exposição (extraídas das paliçadas durante a manutenção programada). A razão $k_{\theta,8meses} / k_{\theta,novo}$ quantifica a degradação da conexão no ciclo de manutenção. A significância da diferença entre tratamentos é avaliada pelo teste t de Student (ou teste não paramétrico equivalente).

## 6. Ensaio de prova de carga lateral em estacas *in situ*

### 6.1 Objetivo

Determinar a curva carga-deslocamento lateral ($p$-$y$) de estacas de *B. vulgaris* cravadas no Plintossolo Argilúvico, derivando o coeficiente de reação horizontal do solo ($k_h$, em MN/m³) para calibração de um modelo de interação solo-estrutura por molas de Winkler, substituindo a condição de engaste total adotada no modelo FEM.

### 6.2 Seleção das estacas

São selecionadas no mínimo três estacas do segmento MED, com preferência por estacas externas (E1 e E3) e central (E2) da paliçada, de modo a capturar possíveis variações de confinamento lateral associadas à posição na seção transversal da ravina. As estacas devem estar cravadas há pelo menos 6 meses, com o solo já reconsolidado ao redor.

### 6.3 Aparato e instrumentação

O carregamento lateral é aplicado por macaco hidráulico de capacidade 20 kN, posicionado a 50 mm acima do nível do solo, reagindo contra uma viga de referência ancorada em estacas de aço independentes (distância mínima de 2 m da estaca de ensaio para evitar interferência). A carga é medida por célula de carga digital (capacidade 20 kN, resolução 1 N) interposta entre o macaco e a estaca. O deslocamento lateral no ponto de aplicação da carga é medido por dois comparadores mecânicos (curso 25 mm, resolução 0,01 mm) alinhados perpendicularmente ao eixo da estaca e fixados na viga de referência, eliminando movimentos espúrios. Um terceiro comparador é posicionado a 300 mm acima do nível do solo (topo da estaca) para registrar o perfil de deslocamento ao longo da altura exposta.

### 6.4 Procedimento de carregamento

O carregamento segue protocolo incremental com patamares de 0,25 kN, mantidos por 5 minutos cada para estabilização, com registros de carga e deslocamento ao final de cada patamar. O ciclo de carga-descarga é executado até a carga máxima de 5 kN ou deslocamento lateral de 15 mm (o que ocorrer primeiro), seguido de descarga em patamares idênticos. São executados três ciclos em cada estaca.

### 6.5 Grandezas derivadas

O coeficiente de reação horizontal ($k_h$) é calculado pela inclinação da região linear do primeiro ciclo de carga: $k_h = \Delta p / (\Delta y \cdot D_{ext})$, onde $\Delta p / \Delta y$ é a taxa carga-deslocamento por unidade de profundidade e $D_{ext}$ é o diâmetro externo da estaca. O valor médio de $k_h$ é comparado à faixa de 10 a 20 MN/m³ admitida no modelo para solos argilosos. Adicionalmente, a rigidez à rotação na base ($k_{rot}$) é estimada pela razão entre o momento calculado no nível do solo ($M_0 = F \times h_{aplicação}$) e a rotação inferida pela diferença de deslocamento entre os dois comparadores.

## 7. Monitoramento de deslocamento lateral *in situ*

### 7.1 Objetivo

Medir o deslocamento lateral real no topo das estacas do segmento MED durante eventos de chuva, para validação direta da previsão do modelo FEM (deslocamento máximo de 16,1 mm sob degradação pessimista a $t = 10$ anos; < 2 mm nos primeiros dois anos). A validação atual do modelo limita-se à ausência de desalinhamento visível nas vistorias semestrais.

### 7.2 Instrumentação

Dois comparadores mecânicos de longa duração (curso 25 mm, resolução 0,01 mm, protegidos por cápsula de PVC contra salpicos e sedimentos) são instalados no topo de duas estacas do segmento MED (estaca central E2 e uma estaca externa), fixados em suportes metálicos ancorados nos taludes laterais da ravina por estacas de aço cravadas a 1,0 m de profundidade, fora da zona de influência das paliçadas. A haste do comparador encosta em plaqueta de aço inoxidável colada na estaca de bambu com adesivo epóxi. A leitura de referência (zero) é registrada em condição seca (solo com umidade abaixo da capacidade de campo) e sem escoamento.

Alternativamente, se disponíveis, transdutores LVDT com datalogger autônomo (resolução 0,01 mm, taxa de aquisição 1 Hz) podem substituir os comparadores mecânicos, possibilitando registro contínuo durante eventos de chuva sem presença de operador.

### 7.3 Procedimento de monitoramento

O monitoramento cobre no mínimo uma estação chuvosa completa (maio a agosto no litoral de Sergipe, de acordo com a climatologia local), com leituras manuais antes e depois de cada evento de chuva identificável (>10 mm acumulados), totalizando estimativa de 15 a 25 eventos por estação. Para cada evento, são registrados: (a) deslocamento lateral nos dois comparadores, (b) precipitação acumulada do evento (estação meteorológica automática), (c) nível de água na ravina a montante e a jusante da paliçada (escala hidrométrica com resolução de 1 cm), (d) altura do depósito sedimentar (trena).

### 7.4 Análise dos dados

O deslocamento lateral medido é comparado com o deslocamento previsto pelo modelo FEM para o mesmo instante temporal e o mesmo percentual de preenchimento sedimentar observado. Regressão linear entre deslocamento medido e precipitação acumulada do evento permite estimar a sensibilidade hidro-mecânica da estrutura. Caso haja discrepância sistemática superior a 30% entre medido e simulado, os parâmetros de rigidez do modelo ($E_L$, $k_h$, condição de contorno) são recalibrados por análise inversa (minimização do resíduo quadrático entre curva simulada e medida).

## 8. Ensaio de fator de concentração de tensão por extensometria

### 8.1 Objetivo

Determinar o fator de concentração de tensão (SCF) real nas zonas nodais e nas junções colmo-estaca de *B. vulgaris*, substituindo o valor de 1,8 extraído de Pilkey (1997) para furo em cilindro oco. O próprio manuscrito reconhece que essa geometria "não é idêntica ao diafragma nodal do bambu". A variação paramétrica de SCF entre 1,5 e 2,2 propaga incerteza de 0,26 a 0,48 no FI máximo.

### 8.2 Instrumentação

Extensômetros de resistência elétrica (strain gauges uniaxiais, base de 5 mm, fator de gauge 2,0 ± 0,5%) são colados na superfície externa de colmos inteiros, nas seguintes posições: (a) três extensômetros na zona internodal (terço central do entrenó, espaçados 120° na circunferência), (b) três extensômetros na zona nodal (posicionados a 5 mm de cada lado do diafragma e sobre o diafragma), (c) três extensômetros na zona de junção colmo-estaca (posicionados na estaca, a 5 mm acima e 5 mm abaixo do ponto de amarração, e sobre o arame). A preparação da superfície inclui lixamento com lixa 220, limpeza com álcool isopropílico e colagem com adesivo cianoacrilato conforme procedimento padrão para extensometria em materiais naturais.

Alternativamente, se o equipamento estiver disponível, o campo de deformação pode ser obtido por correlação de imagem digital (DIC) com câmera de alta resolução (mínimo 5 Mpx), iluminação difusa e padrão de pontos aplicado por spray (stochastic speckle), possibilitando a visualização do campo de deformação em toda a superfície do colmo, incluindo o entorno do diafragma nodal.

### 8.3 Procedimento de ensaio

Colmos inteiros (comprimento 600 mm, com nó posicionado no terço central) são submetidos a flexão em quatro pontos conforme a Seção 4.4, com carregamento incremental em patamares de 0,5 kN, mantidos por 30 segundos para estabilização. As deformações ($\varepsilon$) são adquiridas por condicionador de sinais (ponte de Wheatstone 1/4, excitação 2,5 V) com taxa de 10 Hz. A tensão é calculada por $\sigma = E_L \cdot \varepsilon$, utilizando o $E_L$ obtido no ensaio de flexão (Seção 4).

### 8.4 Cálculo do SCF

O fator de concentração de tensão é definido como a razão entre a deformação (ou tensão) máxima local na zona de descontinuidade e a deformação nominal na zona internodal para o mesmo nível de carga: $SCF = \varepsilon_{max,nodal} / \varepsilon_{nominal,internodal}$. O SCF da junção colmo-estaca é calculado de modo análogo, substituindo $\varepsilon_{max,nodal}$ pela deformação máxima na zona do arame. São ensaiados no mínimo 8 colmos com extensômetros (4 com nó, 4 com junção amarrada), reportando média, desvio padrão e intervalo de confiança de 95% para o SCF em cada zona.

## 9. Resumo do plano amostral e cronograma estimado

| **Ensaio** | **n total (CP/medições)** | **Equipamento principal** | **Duração** |
|---|---|---|---|
| 2. Cisalhamento interlaminar | 100 CP | Máquina universal de ensaios 10 kN | 2 semanas |
| 3. Degradação acelerada | 140 CP (6 retiradas) | Máquina universal + câmara climatizada | 30 meses |
| 4. Flexão estática | 15 colmos | Máquina universal 50 kN + LVDT | 2 semanas |
| 5. Rigidez da conexão | 20 junções | Célula de carga 2 kN + inclinômetros | 1 semana |
| 6. Prova de carga lateral | 3 estacas | Macaco hidráulico 20 kN + comparadores | 3 dias |
| 7. Deslocamento *in situ* | 2 estacas (15–25 eventos) | Comparadores mecânicos ou LVDT | 4 meses |
| 8. Extensometria (SCF) | 8 colmos | Strain gauges + condicionador ou DIC | 2 semanas |

A execução dos ensaios 2, 4 e 8 pode ser simultânea, utilizando a mesma máquina universal de ensaios e os mesmos colmos (regiões distintas). O ensaio 3 é o limitante temporal (30 meses), porém os primeiros resultados parciais (6 e 12 meses) permitem estimativa preliminar de $k$ para atualização do modelo FEM. Os ensaios de campo (6 e 7) são executados preferencialmente no início da estação chuvosa, quando as paliçadas estão sob carregamento efetivo.

## 10. Tratamento estatístico consolidado

Todos os ensaios reportam média, desvio padrão, coeficiente de variação e intervalo de confiança de 95% para as grandezas primárias. A normalidade é verificada pelo teste de Shapiro-Wilk ($\alpha = 0{,}05$); em caso de rejeição, testes não paramétricos equivalentes (Mann-Whitney U para duas amostras, Kruskal-Wallis para três ou mais) substituem os testes paramétricos. Correlações entre propriedades mecânicas e variáveis geométricas (diâmetro, espessura de parede, posição nodal) são avaliadas por coeficiente de Pearson ou Spearman conforme a distribuição. Os ajustes de regressão (exponencial para degradação, linear para rigidez) incluem métricas de qualidade (R², RMSE) e intervalos de confiança para os parâmetros estimados. As análises são conduzidas em R (≥ 4.4.0) ou Python (≥ 3.10 com scipy e statsmodels), com scripts versionados no repositório do projeto.
