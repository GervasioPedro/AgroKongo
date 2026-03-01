#!/usr/bin/env python3
"""
AgroKongo - Conversor de Imagens para WebP
Otimizado para zonas rurais (reduz ~30-40% do tamanho)
Mantém identidade visual enquanto economiza dados

Uso:
    python scripts/convert_to_webp.py [--quality 82] [--thumb-size 400] [--backup]

Autor: AgroKongo Team
Data: 2026-02-22
"""

import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageOps
from datetime import datetime
import hashlib

# ==================== CONFIGURAÇÃO ====================
# Diretórios base (ajusta conforme teu setup)
BASE_DIR = Path(__file__).parent.parent
DATA_STORAGE = BASE_DIR / 'data_storage'
PUBLIC_FOLDER = DATA_STORAGE / 'public'
PRIVATE_FOLDER = DATA_STORAGE / 'private'

# Configurações de conversão
DEFAULT_QUALITY = 82  # 82 = bom equilíbrio qualidade/tamanho
DEFAULT_THUMB_SIZE = 400  # Thumbnail para mobile (economiza dados)
MAX_IMAGE_SIZE = 1200  # Redimensiona imagens maiores que isto
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}

# Estatísticas
stats = {
    'processed': 0,
    'converted': 0,
    'skipped': 0,
    'errors': 0,
    'original_size': 0,
    'new_size': 0
}


def calcular_hash(filepath):
    """Calcula hash SHA256 do arquivo para detectar duplicatas."""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()[:8]


def converter_para_webp(
        input_path: Path,
        output_path: Path,
        quality: int = DEFAULT_QUALITY,
        max_size: int = MAX_IMAGE_SIZE,
        criar_thumbnail: bool = True,
        thumb_size: int = DEFAULT_THUMB_SIZE
) -> dict:
    """
    Converte imagem para WebP com otimizações para mobile/rural.

    Args:
        input_path: Caminho da imagem original
        output_path: Caminho de saída (sem extensão)
        quality: Qualidade WebP (1-100, 82 recomendado)
        max_size: Tamanho máximo (largura/altura)
        criar_thumbnail: Se deve criar thumbnail para mobile
        thumb_size: Tamanho do thumbnail

    Returns:
        dict com estatísticas da conversão
    """
    result = {
        'success': False,
        'original_size': 0,
        'new_size': 0,
        'thumbnail_created': False,
        'message': ''
    }

    try:
        # Verifica se arquivo existe
        if not input_path.exists():
            result['message'] = f'Arquivo não encontrado: {input_path}'
            return result

        # Tamanho original
        original_size = input_path.stat().st_size
        result['original_size'] = original_size

        # Abre imagem
        with Image.open(input_path) as img:
            # Converte para RGB (necessário para WebP)
            if img.mode in ('RGBA', 'P', 'LA'):
                # Preserva transparência convertendo para RGBA primeiro
                img = img.convert('RGBA')
                # WebP suporta transparência, então mantemos RGBA
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Orientação EXIF (corrige fotos de celular)
            img = ImageOps.exif_transpose(img)

            # Redimensiona se necessário (economiza dados mobile)
            if max(img.size) > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

            # Salva como WebP
            output_path_webp = Path(str(output_path) + '.webp')
            img.save(
                output_path_webp,
                'WEBP',
                quality=quality,
                method=6,  # Máxima compressão
                exact=True
            )

            # Tamanho novo
            new_size = output_path_webp.stat().st_size
            result['new_size'] = new_size
            result['success'] = True

            # Cria thumbnail para mobile (opcional)
            if criar_thumbnail:
                thumb_path = Path(str(output_path) + '_thumb.webp')
                thumb = img.copy()
                thumb.thumbnail((thumb_size, thumb_size), Image.Resampling.LANCZOS)
                thumb.save(
                    thumb_path,
                    'WEBP',
                    quality=quality,
                    method=6
                )
                result['thumbnail_created'] = True

            # Calcula economia
            economy = ((original_size - new_size) / original_size * 100) if original_size > 0 else 0
            result['message'] = f'✅ Convertido ({economy:.1f}% menor)'

    except Exception as e:
        result['message'] = f'❌ Erro: {str(e)}'

    return result


def processar_diretorio(
        directory: Path,
        quality: int = DEFAULT_QUALITY,
        max_size: int = MAX_IMAGE_SIZE,
        criar_thumbnail: bool = True,
        thumb_size: int = DEFAULT_THUMB_SIZE,
        backup: bool = False,
        dry_run: bool = False
):
    """
    Processa todos os arquivos de imagem num diretório.
    """
    global stats

    print(f"\n📁 Processando: {directory}")
    print("=" * 60)

    if not directory.exists():
        print(f"⚠️ Diretório não existe: {directory}")
        return

    # Encontra todas as imagens
    image_files = []
    for ext in SUPPORTED_FORMATS:
        image_files.extend(directory.rglob(f'*{ext}'))
        image_files.extend(directory.rglob(f'*{ext.upper()}'))

    print(f"📊 Encontradas {len(image_files)} imagens")

    if dry_run:
        print("🔍 DRY RUN - Nenhuma alteração será feita")
        for img_path in image_files:
            print(f"  • {img_path.relative_to(BASE_DIR)}")
        return

    # Processa cada imagem
    for img_path in image_files:
        stats['processed'] += 1

        # Pula se já for WebP
        if img_path.suffix.lower() == '.webp':
            stats['skipped'] += 1
            continue

        # Define caminho de saída
        relative_path = img_path.relative_to(directory)
        output_path = directory / relative_path.parent / img_path.stem

        # Backup (opcional)
        if backup:
            backup_path = img_path.with_suffix(img_path.suffix + '.backup')
            try:
                import shutil
                shutil.copy2(img_path, backup_path)
            except Exception as e:
                print(f"⚠️ Falha backup {img_path.name}: {e}")

        # Converte
        print(f"[{stats['processed']}/{len(image_files)}] {img_path.name}...", end=' ')
        result = converter_para_webp(
            img_path,
            output_path,
            quality=quality,
            max_size=max_size,
            criar_thumbnail=criar_thumbnail,
            thumb_size=thumb_size
        )

        if result['success']:
            stats['converted'] += 1
            stats['original_size'] += result['original_size']
            stats['new_size'] += result['new_size']

            # Economia
            economy = ((result['original_size'] - result['new_size']) / result['original_size'] * 100)
            print(f"✅ {economy:.1f}% menor", end='')
            if result['thumbnail_created']:
                print(" + thumbnail", end='')
            print()

            # Remove original (opcional - comenta se quiser manter)
            # img_path.unlink()

        else:
            stats['errors'] += 1
            print(f"❌ {result['message']}")

    print("=" * 60)


def mostrar_relatorio():
    """Mostra relatório final de conversão."""
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO DE CONVERSÃO")
    print("=" * 60)
    print(f"✅ Processadas: {stats['processed']}")
    print(f"✅ Convertidas: {stats['converted']}")
    print(f"⏭️  Puladas: {stats['skipped']}")
    print(f"❌ Erros: {stats['errors']}")
    print("-" * 60)

    # Tamanho
    original_mb = stats['original_size'] / (1024 * 1024)
    new_mb = stats['new_size'] / (1024 * 1024)
    economy_mb = original_mb - new_mb
    economy_pct = ((stats['original_size'] - stats['new_size']) / stats['original_size'] * 100) if stats[
                                                                                                       'original_size'] > 0 else 0

    print(f"📦 Tamanho Original: {original_mb:.2f} MB")
    print(f"📦 Tamanho Final: {new_mb:.2f} MB")
    print(f"💾 Economia: {economy_mb:.2f} MB ({economy_pct:.1f}%)")
    print("=" * 60)

    # Impacto para zonas rurais
    if economy_mb > 0:
        print("\n🌍 IMPACTO PARA ZONAS RURAIS:")
        print(f"   • Dados economizados: {economy_mb:.2f} MB")
        print(f"   • Páginas mais rápidas: ~{economy_pct:.0f}%")
        print(f"   • Custo dados reduzido: ~{economy_pct:.0f}%")
        print(f"   • Bateria economizada: ~{economy_pct / 2:.0f}%")
    print("=" * 60 + "\n")


def main():
    """Função principal com argumentos de linha de comando."""
    parser = argparse.ArgumentParser(
        description='AgroKongo - Conversor de Imagens para WebP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
    python scripts/convert_to_webp.py
    python scripts/convert_to_webp.py --quality 75 --thumb-size 300
    python scripts/convert_to_webp.py --backup --dry-run
    python scripts/convert_to_webp.py --public-only
        """
    )

    parser.add_argument(
        '--quality', '-q',
        type=int,
        default=DEFAULT_QUALITY,
        help=f'Qualidade WebP (1-100, default: {DEFAULT_QUALITY})'
    )

    parser.add_argument(
        '--thumb-size', '-t',
        type=int,
        default=DEFAULT_THUMB_SIZE,
        help=f'Tamanho do thumbnail (default: {DEFAULT_THUMB_SIZE}px)'
    )

    parser.add_argument(
        '--max-size', '-m',
        type=int,
        default=MAX_IMAGE_SIZE,
        help=f'Tamanho máximo da imagem (default: {MAX_IMAGE_SIZE}px)'
    )

    parser.add_argument(
        '--backup', '-b',
        action='store_true',
        help='Cria backup das imagens originais (.backup)'
    )

    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Simula conversão sem modificar arquivos'
    )

    parser.add_argument(
        '--public-only',
        action='store_true',
        help='Processa apenas pasta pública (safras, perfil)'
    )

    parser.add_argument(
        '--private-only',
        action='store_true',
        help='Processa apenas pasta privada (comprovativos, documentos)'
    )

    args = parser.parse_args()

    # Header
    print("\n" + "=" * 60)
    print("🌱 AGROKONGO - CONVERSOR WEBP")
    print("Otimizado para Zonas Rurais de Angola")
    print("=" * 60)
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"⚙️  Qualidade: {args.quality}")
    print(f"📱 Thumbnail: {args.thumb_size}px")
    print(f"🖼️  Max Size: {args.max_size}px")
    print(f"💾 Backup: {'Sim' if args.backup else 'Não'}")
    print(f"🔍 Dry Run: {'Sim' if args.dry_run else 'Não'}")
    print("=" * 60)

    # Verifica diretórios
    if not DATA_STORAGE.exists():
        print(f"\n❌ Diretório de armazenamento não encontrado: {DATA_STORAGE}")
        print("💡 Crie a estrutura primeiro:")
        print("   mkdir -p data_storage/public/safras")
        print("   mkdir -p data_storage/public/perfil")
        print("   mkdir -p data_storage/private/comprovativos")
        print("   mkdir -p data_storage/private/documentos")
        sys.exit(1)

    # Processa diretórios
    if args.public_only:
        processar_diretorio(
            PUBLIC_FOLDER,
            quality=args.quality,
            max_size=args.max_size,
            criar_thumbnail=True,
            thumb_size=args.thumb_size,
            backup=args.backup,
            dry_run=args.dry_run
        )
    elif args.private_only:
        processar_diretorio(
            PRIVATE_FOLDER,
            quality=args.quality,
            max_size=args.max_size,
            criar_thumbnail=False,  # Não precisa thumbnail em privados
            backup=args.backup,
            dry_run=args.dry_run
        )
    else:
        # Processa ambos
        processar_diretorio(
            PUBLIC_FOLDER,
            quality=args.quality,
            max_size=args.max_size,
            criar_thumbnail=True,
            thumb_size=args.thumb_size,
            backup=args.backup,
            dry_run=args.dry_run
        )
        processar_diretorio(
            PRIVATE_FOLDER,
            quality=args.quality,
            max_size=args.max_size,
            criar_thumbnail=False,
            backup=args.backup,
            dry_run=args.dry_run
        )

    # Relatório final
    mostrar_relatorio()

    # Sucesso
    if stats['errors'] == 0:
        print("🎉 Conversão concluída com sucesso!")
        sys.exit(0)
    else:
        print(f"⚠️ Conversão concluída com {stats['errors']} erros")
        sys.exit(1)


if __name__ == '__main__':
    main()