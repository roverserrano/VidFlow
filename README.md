# VidFlow

VidFlow es una app de escritorio para descargar video o audio desde:

- YouTube
- TikTok
- Facebook

Esta version ya incluye interfaz moderna y progreso en tiempo real.

## Descargas listas (usuario final)

Si solo quieres instalar y usar la app:

1. **Linux AppImage (recomendado):**  
   `dist/VidFlow-0.3.0.AppImage`
2. **Linux Debian/Ubuntu (.deb):**  
   `dist/vidflow_0.3.0_amd64.deb`
3. **Windows portable (.zip con .exe):**  
   `dist/VidFlow-Windows-Portable-0.3.0.zip`

### Importante para Windows

- Dentro del `.zip` abre: `win-unpacked/VidFlow.exe`
- No ejecutes el `.exe` pequeño `VidFlow Setup 0.3.0.exe` generado en Linux para distribucion final; para instalador NSIS real se recomienda build en Windows (o Linux con `wine` correctamente instalado).

## Instalacion para personas no tecnicas

### Linux (AppImage)

1. Descarga `VidFlow-0.3.0.AppImage`.
2. Dale permiso de ejecucion:
   ```bash
   chmod +x VidFlow-0.3.0.AppImage
   ```
3. Haz doble clic o ejecútalo.

### Linux (Debian/Ubuntu)

1. Descarga `vidflow_0.3.0_amd64.deb`.
2. Instala con doble clic o terminal:
   ```bash
   sudo apt install ./vidflow_0.3.0_amd64.deb
   ```

### Windows (Portable)

1. Descarga `VidFlow-Windows-Portable-0.3.0.zip`.
2. Extrae todo el contenido.
3. Entra a `win-unpacked`.
4. Ejecuta `VidFlow.exe`.

## Uso basico

1. Abre VidFlow.
2. Pega una URL de YouTube, TikTok o Facebook.
3. Pulsa **Pegar y analizar** o **Analizar**.
4. Elige formato:
   - Video (MP4)
   - Audio (MP3/M4A/OGG)
5. Pulsa **Descargar**.

## Estados y mensajes

- La barra de progreso muestra porcentaje, velocidad y tiempo restante.
- Al terminar, la app guarda en el historial.
- Si hay errores, muestra mensajes legibles para reintentar.

## Para desarrollo (equipo tecnico)

### Requisitos

- Python 3.11+
- Node.js 20+
- npm

### Ejecutar en local

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm install
npm run dev
```

### Tests

```bash
npm test
```

### Builds

Linux:

```bash
npm run package:linux
```

Windows (instalador NSIS):

```bash
npm run package:win
```

> En Linux, `package:win` requiere `wine` para completar instalador.

## Estructura del proyecto (resumen)

```text
electron/   -> proceso principal, preload e IPC
renderer/   -> interfaz React
backend/    -> API local FastAPI + yt-dlp
resources/  -> iconos, ffmpeg y backend embebido
dist/       -> artefactos listos para distribuir
```

