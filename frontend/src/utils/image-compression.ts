import imageCompression from 'browser-image-compression';

/**
 * Comprime imagens antes do upload para poupar dados móveis
 * Reduz fotos de 5MB para ~200KB
 */
export async function compressImage(file: File): Promise<File> {
  const options = {
    maxSizeMB: 0.2, // 200KB
    maxWidthOrHeight: 1200,
    useWebWorker: true,
    fileType: 'image/webp'
  };

  try {
    const compressedFile = await imageCompression(file, options);
    return compressedFile;
  } catch (error) {
    console.error('Erro ao comprimir imagem:', error);
    return file; // Retorna original se falhar
  }
}
