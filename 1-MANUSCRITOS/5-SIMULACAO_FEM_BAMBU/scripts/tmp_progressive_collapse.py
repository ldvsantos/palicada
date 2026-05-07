"""
Análise de colapso progressivo
==============================
A FEM é linear, então a tensão escala linearmente com a carga (multiplicador
λ) e o índice Tsai-Hill escala quadraticamente:

    FI_i(λ) = λ² · FI_i(1)
    →  λ_falha,i = 1 / √FI_i(1)

Pergunta: a partir do estado atual (t = 11.5 a, MED, hidrologia mediana,
degradação pessimista, com a 1ª estaca já em FI = 0.97), quanto mais
carga é necessária para colapsar TODA a paliçada?
"""
import sys
import numpy as np
from collections import defaultdict
sys.path.insert(0, '.')
from gerar_figuras_fem3d import _solve_single
from fem_palicada_3d import SEGMENTS

nodes, elems, U, fi = _solve_single('MED', 'median', 'pessimistic', 11.5)
fi = np.array(fi)
n = len(elems)

# Multiplicador de carga necessário para cada elemento atingir FI=1
lam_fail = np.where(fi > 1e-9, 1.0 / np.sqrt(fi), np.inf)

# Estatísticas
order = np.argsort(lam_fail)
print(f'Estado de referência: t=11.5 a, MED, mediana, pessimista')
print(f'  carga lateral atual = q_ref (Rankine + degradação)')
print(f'  λ = multiplicador da carga atual')
print()
print(f'  λ p/ 1ª  ruptura (já existe)  : {lam_fail[order[0]]:.3f}  → +{(lam_fail[order[0]]-1)*100:5.1f}% de carga')
print(f'  λ p/ 25% dos elementos romperem: {lam_fail[order[int(0.25*n)]]:.3f}  → +{(lam_fail[order[int(0.25*n)]]-1)*100:5.1f}%')
print(f'  λ p/ 50% dos elementos romperem: {lam_fail[order[int(0.50*n)]]:.3f}  → +{(lam_fail[order[int(0.50*n)]]-1)*100:5.1f}%')
print(f'  λ p/ 75% dos elementos romperem: {lam_fail[order[int(0.75*n)]]:.3f}  → +{(lam_fail[order[int(0.75*n)]]-1)*100:5.1f}%')
print(f'  λ p/ TODOS os elementos romperem: {lam_fail[order[-1]]:.3f}  → +{(lam_fail[order[-1]]-1)*100:5.1f}%')
print()

# Sequência de falha por tipo
type_seq = defaultdict(list)
for i in order:
    type_seq[elems[i]['type']].append(lam_fail[i])

print('Sequência de falha por tipo de elemento:')
for t, lams in type_seq.items():
    lams = np.array(lams)
    print(f'  {t:>14}: 1ª falha λ={lams[0]:.3f}  |  última λ={lams[-1]:.3f}  |  N={len(lams)}')
print()

# Tabela: λ vs % de elementos rompidos
print('Curva de colapso progressivo:')
print(f'  {"λ":>6} {"+carga":>8} {"% rompidos":>11} {"N rompidos":>11}')
for lam in [1.00, 1.014, 1.05, 1.10, 1.25, 1.50, 1.75, 2.00, 2.50, 3.00, 4.00, 5.00, 7.00, 10.0]:
    n_failed = (lam_fail <= lam).sum()
    pct = n_failed / n * 100
    print(f'  {lam:>6.3f} {(lam-1)*100:>+7.1f}% {pct:>10.1f}% {n_failed:>6}/{n}')

# Cargas físicas correspondentes (q_Rankine ~ K_a γ z; tomamos a magnitude no
# topo do colmo mais carregado ~ no nó central da camada inferior)
# Carga atual: a estaca central já reage em FI=0.97 com carga atual.
# A "destruição completa" exige λ_max = 1/sqrt(min FI não-zero).
fi_nz = fi[fi > 1e-6]
print()
print(f'FI mínimo não-trivial: {fi_nz.min():.5f}')
print(f'FI máximo:             {fi_nz.max():.5f}')
print(f'Razão entre o mais e o menos carregado: {fi_nz.max()/fi_nz.min():.1f}×')
