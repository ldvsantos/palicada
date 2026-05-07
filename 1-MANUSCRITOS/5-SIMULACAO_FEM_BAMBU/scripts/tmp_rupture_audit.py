import sys
sys.path.insert(0, '.')
import numpy as np
from collections import Counter
from gerar_figuras_fem3d import _solve_single
from fem_palicada_3d import SEGMENTS

nodes, elems, U, fi = _solve_single('MED', 'median', 'pessimistic', 11.5)
fi = np.array(fi)
W = SEGMENTS['MED']['width']
H = SEGMENTS['MED']['height']

order = np.argsort(fi)[::-1]
print(f'W={W} m, H={H} m, n_elems={len(elems)}')
print('Top 15 elementos por FI:')
hdr = f"{'#':>4} {'FI':>7} {'type':>12} {'is_nz':>6} {'layer':>5} {'x_mid':>7} {'z_mid':>7}"
print(hdr)
for i in order[:15]:
    e = elems[i]
    p1, p2 = nodes[e['n1']], nodes[e['n2']]
    xm = (p1[0] + p2[0]) / 2
    zm = (p1[2] + p2[2]) / 2
    print(f"{i:>4} {fi[i]:>7.3f} {e['type']:>12} {str(e['is_nz']):>6} {e['layer']:>5} {xm:>7.2f} {zm:>7.2f}")

print()
print(f'FI > 0.50: {(fi > 0.5).sum()}/{len(fi)} elem ({(fi > 0.5).mean()*100:.1f}%)')
print(f'FI > 0.80: {(fi > 0.8).sum()}')
print(f'FI > 0.95: {(fi > 0.95).sum()}')

crit = [(e['type'], e['is_nz']) for e, f in zip(elems, fi) if f > 0.3]
print('Distribuição (tipo, is_node_zone) p/ FI>0.3:', Counter(crit))

# x positions of critical elements
x_crit = []
for i, e in enumerate(elems):
    if fi[i] > 0.5:
        p1, p2 = nodes[e['n1']], nodes[e['n2']]
        x_crit.append((p1[0] + p2[0]) / 2)
print('x dos elementos com FI>0.5:', sorted(set(round(x, 2) for x in x_crit)))
