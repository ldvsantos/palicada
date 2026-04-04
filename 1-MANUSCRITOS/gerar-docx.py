#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar arquivos Word com referências a partir do Markdown
Uso: python gerar-docx.py
Gera DOCX a partir dos manuscritos .md
"""

import os
import re
import subprocess
import sys
from pathlib import Path
import time
import zipfile
import xml.etree.ElementTree as ET
import shutil
import tempfile


def _extract_yaml_csl(md_file: Path) -> Path | None:
    """Lê o campo 'csl:' do YAML front matter do Markdown."""
    try:
        text = md_file.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    m = re.search(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return None
    for line in m.group(1).splitlines():
        cm = re.match(r"^csl:\s*['\"]?(.+?)['\"]?\s*$", line)
        if cm:
            csl_path = (md_file.parent / cm.group(1)).resolve()
            if csl_path.exists():
                return csl_path
    return None


def _build_resource_path(md_file: Path, base_dir: Path) -> str:
    paths = [
        md_file.parent,
        md_file.parent / "media",
        md_file.parent / "figuras",
        base_dir,
        base_dir / "media",
    ]
    # Pandoc usa separador específico por SO (Windows: ';', Unix: ':')
    unique_existing = []
    for p in paths:
        try:
            if p.exists():
                unique_existing.append(str(p))
        except Exception:
            continue
    return os.pathsep.join(dict.fromkeys(unique_existing))


# ── Mapeamento Pandoc → Taylor & Francis template ──
_WML = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
_NS = {"w": _WML}

# Mapeamento direto de estilos Pandoc → template T&F
_STYLE_MAP = {
    "Title": "Articletitle",
    "Author": "Authornames",
    "Date": "Receiveddates",
    "FirstParagraph": "Paragraph",
    "BodyText": "Newparagraph",
    "Bibliography": "References",
}


def _get_pstyle(p_elem):
    """Retorna o w:pStyle val de um parágrafo, ou string vazia."""
    ps = p_elem.find(".//w:pStyle", _NS)
    if ps is not None:
        return ps.get(f"{{{_WML}}}val", "")
    return ""


def _set_pstyle(p_elem, new_style):
    """Define o w:pStyle val de um parágrafo. Cria pPr/pStyle se necessário."""
    ppr = p_elem.find("w:pPr", _NS)
    if ppr is None:
        ppr = ET.SubElement(p_elem, f"{{{_WML}}}pPr")
        # inserir como primeiro filho
        p_elem.remove(ppr)
        p_elem.insert(0, ppr)
    ps = ppr.find("w:pStyle", _NS)
    if ps is None:
        ps = ET.SubElement(ppr, f"{{{_WML}}}pStyle")
    ps.set(f"{{{_WML}}}val", new_style)


def _get_text(p_elem):
    """Retorna texto concatenado de w:t dentro de um parágrafo."""
    return "".join(
        t.text for t in p_elem.findall(f".//{{{_WML}}}t") if t.text
    )


def _remap_styles_to_template(docx_path: Path) -> bool:
    """
    Pós-processa DOCX gerado pelo Pandoc, remapeando estilos para o
    template Taylor & Francis (modelo_formatacao.docx).
    
    Retorna True se bem-sucedido, False se falhar.
    """
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".docx")
        os.close(tmp_fd)

        # Registrar namespaces OOXML para não perder prefixos na serialização
        _ooxml_ns = {
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
            "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
            "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
            "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
            "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
            "o": "urn:schemas-microsoft-com:office:office",
            "v": "urn:schemas-microsoft-com:vml",
            "m": "http://schemas.openxmlformats.org/officeDocument/2006/math",
            "wps": "http://schemas.microsoft.com/office/word/2010/wordprocessingShape",
            "w14": "http://schemas.microsoft.com/office/word/2010/wordml",
            "w15": "http://schemas.microsoft.com/office/word/2012/wordml",
            "w16se": "http://schemas.microsoft.com/office/word/2015/wordml/symex",
            "wpg": "http://schemas.microsoft.com/office/word/2010/wordprocessingGroup",
            "wpc": "http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas",
            "wp14": "http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing",
        }
        for prefix, uri in _ooxml_ns.items():
            ET.register_namespace(prefix, uri)

        with zipfile.ZipFile(str(docx_path), "r") as zin:
            tree = ET.parse(zin.open("word/document.xml"))
            root = tree.getroot()
            body = root.find(f".//{{{_WML}}}body")
            if body is None:
                return False

            paragraphs = [
                c for c in body
                if c.tag == f"{{{_WML}}}p"
            ]

            # --- Fase 1: mapeamento direto ---
            for p in paragraphs:
                sty = _get_pstyle(p)
                if sty in _STYLE_MAP:
                    _set_pstyle(p, _STYLE_MAP[sty])

            # --- Fase 2: contexto — Abstract, Keywords, Figurecaption, Tabletitle ---
            all_children = list(body)
            in_abstract = False
            heading_styles = {"Ttulo1", "Ttulo2", "Ttulo3", "Ttulo4"}

            for i, elem in enumerate(all_children):
                if elem.tag != f"{{{_WML}}}p":
                    continue
                sty = _get_pstyle(elem)
                txt = _get_text(elem).strip()

                # Detectar seção Resumo/Abstract
                if sty in heading_styles:
                    lower = txt.lower().replace("1.", "").replace("2.", "").strip()
                    in_abstract = lower in ("resumo", "abstract")

                # Parágrafos dentro da seção Resumo → Abstract
                if in_abstract and sty in ("Paragraph", "Newparagraph"):
                    if txt.lower().startswith(("palavras-chave", "keywords")):
                        _set_pstyle(elem, "Keywords")
                    else:
                        _set_pstyle(elem, "Abstract")

                # Legendas de figura: texto com "Figura N" antes de um Figure
                if sty in ("Newparagraph", "Paragraph", "BodyText"):
                    if re.match(
                        r"^(Figura|Figure|Fig\.)\s*\d+", txt, re.IGNORECASE
                    ):
                        _set_pstyle(elem, "Figurecaption")

                # Legendas de tabela: texto com "Tabela N" ou "Table N"
                if sty in ("Newparagraph", "Paragraph", "BodyText"):
                    if re.match(
                        r"^(Tabela|Table|TABELA|TABLE)\s*\d+", txt, re.IGNORECASE
                    ):
                        _set_pstyle(elem, "Tabletitle")

            # --- Fase 3: gravar DOCX modificado ---
            with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    if item.filename == "word/document.xml":
                        xml_bytes = ET.tostring(
                            root, xml_declaration=True, encoding="UTF-8"
                        )
                        zout.writestr(item, xml_bytes)
                    else:
                        zout.writestr(item, zin.read(item.filename))

        # Substituir original
        shutil.move(tmp_path, str(docx_path))
        return True

    except Exception as e:
        print(f"⚠️  Erro no pós-processamento de estilos: {e}")
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return False


def gerar_docx(
    md_file: Path,
    output_file: Path,
    bib_file: Path,
    csl_file: Path,
    template_file: Path,
    lua_filter_file: Path | None = None,
    apendices_file: Path | None = None,
    base_dir: Path | None = None,
):
    """
    Gera arquivo DOCX usando Pandoc
    
    Args:
        md_file: Arquivo Markdown de entrada
        output_file: Arquivo DOCX de saída
        bib_file: Arquivo de bibliografia
        csl_file: Arquivo de estilo de citação
        apendices_file: Arquivo de apêndices (opcional)
    
    Returns:
        0 se sucesso, 1 se erro
    """
    print(f"\nGerando {output_file.name}...")
    
    # Remover arquivo antigo se existir
    if output_file.exists():
        print(f"📝 Removendo arquivo antigo: {output_file.name}")
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                output_file.unlink()
                break
            except PermissionError:
                if attempt < max_attempts - 1:
                    print(f"⚠️  Tentativa {attempt + 1}/{max_attempts}: Arquivo em uso, aguardando...")
                    time.sleep(0.6)
                else:
                    print(f"❌ Erro: Não foi possível remover '{output_file.name}'.")
                    print("   Certifique-se de que o arquivo não está aberto no Word ou OneDrive.")
                    return 1
    
    # Comando Pandoc
    cmd = [
        "pandoc",
        str(md_file),
    ]
    
    # Adicionar apêndices ANTES do --citeproc
    if apendices_file and apendices_file.exists():
        cmd.append(str(apendices_file))
        print(f"📎 Incluindo apêndices: {apendices_file.name}")
    
    # Adicionar processamento de citações
    cmd.extend([
        "--citeproc",
        "--bibliography", str(bib_file),
        "--csl", str(csl_file),
    ])

    # Template (reference doc) obrigatório
    if not template_file.exists():
        print(f"\n❌ Erro: template de formatação não encontrado: {template_file}")
        return 1
    try:
        with open(template_file, "rb"):
            pass
        print(f"Usando template: {template_file}")
        cmd.extend(["--reference-doc", str(template_file)])
    except PermissionError:
        print(f"\n❌ Erro: sem permissão para ler o template: {template_file}")
        print("   Feche o arquivo no Word/OneDrive e tente novamente.")
        return 1
    except Exception as e:
        print(f"\n❌ Erro: não foi possível acessar o template {template_file}: {e}")
        return 1

    # Lua filter (legenda acima), se existir
    if lua_filter_file and lua_filter_file.exists():
        cmd.extend(["--lua-filter", str(lua_filter_file)])
    elif lua_filter_file is not None:
        print(f"⚠️  Aviso: filtro Lua não encontrado: {lua_filter_file}")
        print("   As legendas das figuras podem ficar abaixo das imagens.")

    # Resource path para resolver imagens/arquivos relativos
    if base_dir is not None:
        resource_path = _build_resource_path(md_file, base_dir)
        if resource_path:
            cmd.extend(["--resource-path", resource_path])
    
    cmd.extend(["-o", str(output_file)])

    print("Executando Pandoc...")
    
    try:
        # Executar Pandoc
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # Mostrar warnings/erros do Pandoc
        if result.stderr:
            print(f"\n⚠️  Avisos do Pandoc para {output_file.name}:")
            print(result.stderr)
        
        # Verificar se o arquivo foi criado
        if output_file.exists():
            # Pós-processar estilos para o template T&F
            if _remap_styles_to_template(output_file):
                print("📐 Estilos remapeados para o template Taylor & Francis")
            print(f"\n✅ Arquivo {output_file.name} gerado com sucesso!")
            print(f"📍 Localização: {output_file.absolute()}")
            print(f"📊 Tamanho: {output_file.stat().st_size / 1024:.1f} KB")
            return 0
        else:
            print(f"\n❌ Erro: O arquivo {output_file.name} não foi gerado!")
            if result.stdout:
                print("Saída:", result.stdout)
            return 1
            
    except FileNotFoundError:
        print("\n❌ Erro: Pandoc não está instalado ou não está no PATH do sistema!")
        print("   Instale o Pandoc em: https://pandoc.org/installing.html")
        return 1
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        return 1

def main():
    # Definir o diretório base onde estão os arquivos
    script_dir = Path(__file__).parent
    base_dir = script_dir  # Diretório: 1-MANUSCRITOS
    os.chdir(base_dir)
    
    print("=" * 70)
    print("GERADOR DE WORD (Pandoc)")
    print("=" * 70)
    
    # Arquivos comuns
    bib_file = base_dir / "referencias_artigos.bib"
    csl_file = base_dir / "apa.csl"
    template_file = base_dir / "modelo_formatacao.docx"
    lua_filter_file = base_dir / "figura-legenda-acima.lua"
    # apendices_pt = base_dir / "apendices.md"  # Comentado: artigo ainda não possui apêndices
    
    # Verificar arquivos necessários
    arquivos_necessarios = [bib_file, csl_file, template_file]
    arquivos_faltando = [f for f in arquivos_necessarios if not f.exists()]
    
    if arquivos_faltando:
        print("\n❌ Erro: Arquivos necessários não encontrados:")
        for arquivo in arquivos_faltando:
            print(f"   - {arquivo}")
        return 1
    
    # Alvos padrão
    default_md_pt_controle = base_dir / "1-CONTROLE_PLITOSSOLO" / "Controle_Ravinas_Paliçadas.md"
    default_md_caracterizacao = base_dir / "2-CARACTERIZACAO_FEICAO" / "Caracterizacao_Feicao_Erosiva_Plintossolo.qmd"
    default_md_fem_bambu = base_dir / "5-SIMULACAO_FEM_BAMBU" / "Simulacao_FEM_Bambu.md"
    default_md_fem_bambu_en = base_dir / "5-SIMULACAO_FEM_BAMBU" / "Simulacao_FEM_Bambu_EN.md"

    # Permite: python gerar-docx.py caminho/para/arquivo.md [outro.md ...]
    md_targets: list[Path] = []
    if len(sys.argv) > 1:
        md_targets.extend(Path(arg) for arg in sys.argv[1:])
    else:
        for candidate in (default_md_pt_controle, default_md_caracterizacao, default_md_fem_bambu, default_md_fem_bambu_en):
            if candidate.exists():
                md_targets.append(candidate)

    if not md_targets:
        print("\n❌ Erro: nenhum Markdown alvo encontrado.")
        print(f"   Informe um arquivo .md (ex.: python gerar-docx.py {default_md_pt_controle})")
        return 1

    sucessos = 0
    total = len(md_targets)
    for md_file in md_targets:
        if not md_file.exists():
            print(f"\n❌ Arquivo Markdown não encontrado: {md_file}")
            continue
        output_file = md_file.with_suffix(".docx")
        # Usar CSL do YAML do manuscrito, se presente; senão, usar padrão (apa.csl)
        effective_csl = _extract_yaml_csl(md_file) or csl_file
        if effective_csl != csl_file:
            print(f"\U0001f4d6 CSL do YAML: {effective_csl.name}")
        result = gerar_docx(
            md_file=md_file,
            output_file=output_file,
            bib_file=bib_file,
            csl_file=effective_csl,
            template_file=template_file,
            lua_filter_file=lua_filter_file,
            apendices_file=None,
            base_dir=base_dir,
        )
        if result == 0:
            sucessos += 1
    
    # ========================================================================
    # RESUMO FINAL
    # ========================================================================
    print("\n" + "=" * 70)
    print("📊 RESUMO DA GERAÇÃO")
    print("=" * 70)
    print(f"Arquivos gerados com sucesso: {sucessos}/{total}")
    
    if sucessos == total:
        print("\nOK: geração concluída.")
        return 0
    elif sucessos > 0:
        print(f"\n⚠️  Alguns arquivos não foram gerados ({total - sucessos} falharam)")
        return 1
    else:
        print("\n❌ Nenhum arquivo foi gerado!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
