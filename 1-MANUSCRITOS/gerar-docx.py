#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar arquivos Word com referências a partir do Markdown
Uso: python gerar-docx.py
Gera DOCX a partir dos manuscritos .md
"""

import os
import subprocess
import sys
from pathlib import Path
import time


def _build_resource_path(md_file: Path, base_dir: Path) -> str:
    paths = [
        md_file.parent,
        md_file.parent / "media",
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
    default_md_caracterizacao = base_dir / "2-CARACTERIZACAO_FEICAO" / "Caracterizacao_Feicao_Erosiva_Plintossolo_25122025.md"
    default_md_fem_bambu = base_dir / "5-SIMULACAO_FEM_BAMBU" / "Simulacao_FEM_Bambu.md"

    # Permite: python gerar-docx.py caminho/para/arquivo.md [outro.md ...]
    md_targets: list[Path] = []
    if len(sys.argv) > 1:
        md_targets.extend(Path(arg) for arg in sys.argv[1:])
    else:
        for candidate in (default_md_pt_controle, default_md_caracterizacao, default_md_fem_bambu):
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
        result = gerar_docx(
            md_file=md_file,
            output_file=output_file,
            bib_file=bib_file,
            csl_file=csl_file,
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
