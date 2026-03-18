"""
Teste rapido do file_validator sem pytest
"""
from io import BytesIO
from app.utils.file_validator import validar_mime_type, validar_extensao

print("=" * 50)
print("Testando file_validator.py")
print("=" * 50)

# Teste 1: JPEG
jpeg_data = BytesIO(b'\xFF\xD8\xFF\xE0\x00\x10JFIF')
valido, mime = validar_mime_type(jpeg_data)
print(f"\n1. JPEG: valido={valido}, mime={mime}")
assert valido is True and mime == 'image/jpeg', "Falhou JPEG"

# Teste 2: PNG
png_data = BytesIO(b'\x89PNG\r\n\x1a\n')
valido, mime = validar_mime_type(png_data)
print(f"2. PNG: valido={valido}, mime={mime}")
assert valido is True and mime == 'image/png', "Falhou PNG"

# Teste 3: PDF
pdf_data = BytesIO(b'%PDF-1.4\n1 0 obj')
valido, mime = validar_mime_type(pdf_data)
print(f"3. PDF: valido={valido}, mime={mime}")
assert valido is True and mime == 'application/pdf', "Falhou PDF"

# Teste 4: WebP
# WebP: RIFF + 4 bytes tamanho + WEBP (total 12 bytes minimos)
webp_data = BytesIO(b'RIFF\x24\x00\x00\x00WEBPVP8 ')
valido, mime = validar_mime_type(webp_data)
print(f"4. WebP: valido={valido}, mime={mime}")
assert valido is True and mime == 'image/webp', "Falhou WebP"

# Teste 5: Invalido
invalid_data = BytesIO(b'dados aleatorios')
valido, mime = validar_mime_type(invalid_data)
print(f"5. Invalido: valido={valido}, mime={mime}")
assert valido is False, "Falhou invalido"

# Teste 6: Extensao
print(f"\n6. Extensao .jpg: {validar_extensao('teste.jpg', {'jpg', 'png'})}")
assert validar_extensao('teste.jpg', {'jpg', 'png'}) is True

print(f"7. Extensao .exe: {validar_extensao('malware.exe', {'jpg', 'png'})}")
assert validar_extensao('malware.exe', {'jpg', 'png'}) is False

print("\n" + "=" * 50)
print("TODOS OS TESTES PASSARAM!")
print("=" * 50)
