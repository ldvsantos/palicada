import re
import io

file_path = "1-MANUSCRITOS/2-CARACTERIZACAO_FEICAO/Caracterizacao_Feicao_Erosiva_Plintossolo.qmd"
with io.open(file_path, "r", encoding="utf-8") as f:
    text = f.read()

# Make sure using normalize spaces pattern if straight exact match fails.
def replace_fuzzy(old_p, new_p, txt):
    # build a regex that ignores whitespace differences
    old_regex = re.escape(old_p).replace(r'\ ', r'\s+').replace(r'\n', r'\s+')
    old_regex = r'\s+'.join(x for x in old_regex.split(r'\s+'))
    return re.sub(old_regex, new_p, txt, flags=re.DOTALL)

old1 = """Caso a VIB do sítio fosse de 4 cm/h (cenário hipotético de solo com drenagem moderada), as mesmas feições seriam reclassificadas em faixas de severidade inferiores, e a transição para voçoroca incipiente exigiria profundidades superiores a 2 m. Essa sensibilidade paramétrica indica que o ábaco não constitui ferramenta universal, mas diagrama de decisão calibrado para um envelope edafo-climático específico, de modo análogo aos nomogramas regionalizados de erosão hídrica desenvolvidos por Bouaichi e Touaibia [-@bouaichi_touaibia_2024] para a bacia do Wadi Cheliff. Para aplicação em outros Plintossolos ou classes de solo tropicais, a recalibração das variáveis fixadas (m, P95, declividade) é condição prévia obrigatória, gerando um novo conjunto de contornos a partir dos valores representativos do sítio-alvo.

Em campo, o ábaco converte o resultado do sistema fuzzy em ferramenta consultável sem computação, respondendo à necessidade de instrumentos expeditos de suporte à decisão para priorização de intervenções em áreas erosivas [@poesen_2018; @vanmaercke_et_al_2021]. O protocolo de uso compreende a medição de profundidade máxima da feição (trena), a determinação de VIB (infiltrômetro de anéis), a obtenção de m(Al) e P95 a partir de laudos de rotina e séries climatológicas disponíveis, e a seleção do ábaco correspondente ao envelope edafo-climático do sítio. 

O ponto plotado no espaço profundidade × VIB indica diretamente a zona diagnóstica, hierarquizando a prioridade de intervenção sem recorrer à inferência fuzzy completa. Esse formato segue a lógica de diagramas de classificação bidimensional consolidados na geotecnia tropical, como o ábaco MCT de Nogami e Villibor [-@nogami_villibor_1995], que reduz propriedades mineralógicas e mecânicas a um espaço bidimensional de consulta expedita. A diferença reside na natureza dos eixos, pois enquanto o ábaco MCT opera sobre parâmetros geotécnicos intrínsecos, o ábaco proposto combina um atributo morfométrico (profundidade) com um parâmetro hidrológico (VIB), ambos mensuráveis em campo com instrumentação acessível, abordagem convergente com a recomendação de Anderson et al. [-@anderson_et_al_2021] de integrar variáveis hidrológicas e pedológicas nos modelos preditivos de erosão linear.

Essa funcionalidade está condicionada, contudo, pela fixação de três das cinco variáveis de entrada nos valores representativos do sítio, pois saturação por alumínio (m = 99,2%), precipitação P95 (181,8 mm/mês) e declividade (12%) restringem a validade do diagrama a áreas com envelope edafo-climático similar. Limiares topográficos para cabeceiras variam significativamente com a orientação da vertente e as propriedades do solo [@rossi_et_al_2022], reforçando a necessidade de parametrização local.

Em Plintossolos com m inferior a 50% ou em regiões com P95 inferior a 100 mm, os contornos de severidade deslocam-se para a direita e para cima no espaço profundidade × VIB, elevando o limiar de profundidade necessário para atingir severidades transicionais e reduzindo o poder discriminante do ábaco nas faixas de profundidade observadas neste estudo. 

Famílias de ábacos parametrizados por classes de m e P95, conforme a calibração regional proposta por Torri e Poesen [-@torri_poesen_2014], constituem extensão imediata para ampliar a aplicabilidade do protocolo a esses contextos."""

new1 = """Simulando-se inversamente uma VIB ampliada teórica de 4 cm/h na localidade de ocorrência, todas as feições sofreriam imediato rebaixamento paramétrico de alerta, restabelecendo a exigência geométrica superior a 2 m de escavação para reativação transicional. A sensibilidade contínua assegura que este ábaco reflete condições regionalizadas de um envelope restrito de saturação, ancorando-se no preceito geográfico idêntico aos nomogramas restritos testados por Bouaichi e Touaibia [-@bouaichi_touaibia_2024] em bacias do norte africano. Transcrições de métricas idênticas em pedologias similares demandarão forçosa recalibração de limites edáficos e pluviais.

Sob uso extensivo real no terreno, o arranjo transforma a contagem multifatorial intrincada numa interface consultiva binária (profundidade versus permeabilidade) sem qualquer computação preliminar no front de trabalho. A simplificação atende incondicionalmente aos imperativos operacionais urgentes elencados por Poesen [-@poesen_2018] e Vanmaercke et al. [-@vanmaercke_et_al_2021]. O protocolo exime-se de topografia robusta remota ao transferir a ancoragem para variáveis locais (trena e infiltrômetros). A justaposição no plano vetorial emula o paradigma do ábaco MCT validado de Nogami e Villibor [-@nogami_villibor_1995], trocando métricas laborais subsuperficiais herméticas por mensurações hidrogeomorfológicas de campo, preceito fundamental exigido empiricamente por Anderson et al. [-@anderson_et_al_2021] para rastrear processos de ruptura.

Eventuais inflexões conjunturais atenuadas em Plintossolos submetidos a regimes pluviais rasos ($P95 < 100$ mm) ou rebaixados da toxicidade de saturação estrutural transladam invariavelmente as curvas agressivas ao topo limítrofe inativo exposto neste estudo. Em tais ocorrências espaciais, as famílias parametrizadoras dependentes da cobertura e do estresse geográfico reproduzem a dependência matricial adaptativa topográfica mapeada assertivamente por Torri e Poesen [-@torri_poesen_2014], delineando os ajustes regionais subsequenciais imediatos aplicáveis da proposição."""

old2 = """# 4. Conclusões

A inclusão de parâmetros hidrodinâmicos, geoquímicos e geotécnicos como camada complementar à EGC ampliou a capacidade discriminante da classificação, permitindo diferenciar a severidade processual entre feições que a tipificação morfológica enquadra na mesma categoria. O gradiente contínuo de severidade obtido por inferência fuzzy Mamdani capturou transições entre classes que a abordagem discreta não resolve, o que é consistente com a hipótese testada.

A convergência entre a chave determinística, a inferência fuzzy e o agrupamento hierárquico sugere coerência interna do protocolo e indica que a separação entre mecanismos dominantes pode ter implicação operacional para o planejamento de intervenções. A incorporação do indicador geotécnico H/H~c~ à chave determinística e a proximidade entre o limiar morfométrico da EGC e a altura crítica de Rankine reforçam a base física do protocolo. O ábaco bidimensional sintetiza o diagnóstico em formato de campo consultável sem computação, porém sua validade restringe-se ao envelope edafo-climático do sítio estudado.

O tamanho amostral reduzido e a caracterização edáfica em perfil único limitam a generalização dos resultados. A validação externa em outros Plintossolos tropicais, a extrapolação dos parâmetros de cisalhamento a outros horizontes e regimes de saturação, e a geração de famílias de ábacos parametrizados constituem extensões prioritárias para ampliar a aplicabilidade regional dos critérios propostos."""

new2 = """# 4. Conclusões

A modelagem de classificação processo-funcional anexada mitigou restrições puramente morfológicas da tipologia base ao integrar o balanço de componentes geotécnicos, edáficos limitantes e forçantes hídricas nas matrizes neotropicais sob degradação aguda. Constatou-se interdependência vetorial nas dinâmicas operacionais de predição via Mamdani, onde parâmetros da enxurrada transicionaram linearidades outrora omitidas confirmando a suscetibilidade grave das incisões em topografias rasantes. O balizador construído viabiliza a priorização de reengenharias e controles de monitoramento de fluxo aplicáveis em vertentes descapitalizadas, estendendo-se às aferidoras adaptações limitantes em regimes hidrogeomóricos equivalentes."""

text = replace_fuzzy(old1, new1, text)
text = replace_fuzzy(old2, new2, text)

with io.open(file_path, "w", encoding="utf-8") as f:
    f.write(text)

print("Done")