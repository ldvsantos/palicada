"""Apply all English corrections to the Springer .tex manuscript."""
import re

files = [
    r'c:\Users\vidal\OneDrive\Documentos\13 - CLONEGIT\artigo-posdoc\3-EROSIBIDADE\1-MANUSCRITOS\8-SIMULACAO_K_PLINTOSSOLO\Simulacao_Kplint_USLE_Springer.tex',
    r'c:\Users\vidal\OneDrive\Documentos\13 - CLONEGIT\artigo-posdoc\3-EROSIBIDADE\zenodo-kplint\manuscripts\Simulacao_Kplint_USLE_Springer.tex',
]

# Simple string replacements (applied in order)
simple_replacements = [
    # === VIB -> BIR (Portuguese abbreviation -> English) ===
    # Math-mode subscripts first (more specific patterns)
    ('\\mathrm{VIB_{ref}}', '\\mathrm{BIR_{ref}}'),
    ('\\mathrm{VIB_{local}}', '\\mathrm{BIR_{local}}'),
    ('\\mathrm{VIB}', '\\mathrm{BIR}'),
    # Table headers
    ('VIB upper', 'BIR upper'),
    ('VIB intermediate', 'BIR intermediate'),
    ('VIB lower', 'BIR lower'),

    # === CE -> RC (runoff coefficient — Portuguese abbreviation) ===
    ('runoff coefficient (CE)', 'runoff coefficient (RC)'),
    ('CE = 0.37', 'RC = 0.37'),
    ('CE = 0 for', 'RC = 0 for'),
    ('CE = 0.20', 'RC = 0.20'),
    ('CE = 0.56', 'RC = 0.56'),

    # === aluminium -> aluminum ===
    ('exchangeable-aluminium', 'exchangeable-aluminum'),
    ('aluminium', 'aluminum'),

    # === British -> American spellings ===
    ('synthesises', 'synthesizes'),
    ('normalised', 'normalized'),
    ('behaviour', 'behavior'),
    ('favourable', 'favorable'),
    ('favoured', 'favored'),
    ('favours', 'favors'),
    ('modelled', 'modeled'),
    ('modelling', 'modeling'),
    ('Acknowledgements', 'Acknowledgments'),
    ('penalises', 'penalizes'),
    ('penalisation', 'penalization'),
    ('realisations', 'realizations'),
    ('realisation ', 'realization '),  # trailing space to avoid partial match
    ('mobilised', 'mobilized'),
    ('parameterised', 'parameterized'),
    ('parameterisation', 'parameterization'),
    ('recognised', 'recognized'),
    ('optimisation', 'optimization'),
    ('totalling', 'totaling'),

    # === Technical terms ===
    ('simplified Bishop', "Bishop's simplified method"),
    ('uniform Manning regime', "uniform flow (Manning's equation)"),
    ('permeable check-dams', 'permeable check dams'),
    ('calibratable parameters', 'free parameters'),

    # === Style fixes ===
    ('may be considered sufficiently robust to support field calibration',
     'is sufficiently robust to support field calibration'),
    ('The greater recoverability of',
     'The more accurate recovery of'),
    ('accumulate upstream sediment',
     'trap upstream sediment'),
    ('allocating instrumental effort',
     'allocating field-measurement resources'),
]

# Regex replacements for remaining VIB/CE occurrences
regex_replacements = [
    # Standalone VIB in running text (not inside \mathrm{})
    (r'(?<!\\mathrm\{)(?<!\{)(?<!_)\bVIB\b(?!\{)', 'BIR'),
    # CE in math subscript context: \mathrm{CE} or CE}_{
    (r'\\mathrm\{CE\}', r'\\mathrm{RC}'),
    # CE}_{ pattern for subscripted CE
    (r'\{CE\}_', r'{RC}_'),
]

for fpath in files:
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()

        original = content

        # Apply simple replacements
        for old, new in simple_replacements:
            content = content.replace(old, new)

        # Apply regex replacements
        for pattern, repl in regex_replacements:
            content = re.sub(pattern, repl, content)

        # Count lines changed
        orig_lines = original.splitlines()
        new_lines = content.splitlines()
        changed = sum(1 for a, b in zip(orig_lines, new_lines) if a != b)

        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f'OK: ...{fpath[-60:]}')
        print(f'   {changed} lines changed, {len(content)} total chars')
    except Exception as e:
        print(f'ERROR: {fpath}: {e}')

print('\nAll replacements applied.')
