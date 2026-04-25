# VidFlow

VidFlow es una app de escritorio para descargar video o audio desde:

- YouTube
- TikTok
- Facebook

Esta version ya incluye interfaz moderna y progreso en tiempo real.

## Descargas listas (usuario final)

Si solo quieres instalar y usar la app, descarga uno de estos archivos:

1. **Windows (.exe):**  
   [Descargar VidFlow.exe](https://github.com/roverserrano/VidFlow/releases/latest/download/VidFlow.exe)
2. **Linux Debian/Ubuntu (.deb):**  
   [Descargar VidFlow.deb](https://github.com/roverserrano/VidFlow/releases/latest/download/VidFlow.deb)
3. **Linux AppImage (portatil):**  
   [Descargar VidFlow.AppImage](https://github.com/roverserrano/VidFlow/releases/latest/download/VidFlow.AppImage)
4. **Windows portable (.zip con .exe):**  
   [Descargar VidFlow-Windows-Portable-0.3.0.zip](https://github.com/roverserrano/VidFlow/releases/latest/download/VidFlow-Windows-Portable-0.3.0.zip)

> Nota: estos enlaces funcionan cuando los archivos fueron subidos como **assets** en GitHub Releases con esos mismos nombres.

### Publicar archivos de descarga (mantenedor)

1. Ve a `GitHub > VidFlow > Releases > Draft a new release`.
2. Crea un tag (ejemplo: `v0.3.1`).
3. Arrastra y suelta estos archivos:
   - `VidFlow.exe`
   - `VidFlow.deb`
   - `VidFlow.AppImage`
   - `VidFlow-Windows-Portable-0.3.0.zip`
4. Publica el release.

Desde ese momento, los enlaces de arriba descargarán directamente los instaladores.

### Importante para Windows

- Si descargaste `VidFlow.exe`, ejecuta ese archivo para instalar.
- Si descargaste el `.zip`, extrae y abre `win-unpacked/VidFlow.exe`.

## Instalacion para personas no tecnicas

### Linux (AppImage)

1. Descarga `VidFlow.AppImage`.
2. Dale permiso de ejecucion:
   ```bash
   chmod +x VidFlow.AppImage
   ```
3. Haz doble clic o ejecútalo.

### Linux (Debian/Ubuntu)

1. Descarga `VidFlow.deb`.
2. Instala con doble clic o terminal:
   ```bash
   sudo apt install ./VidFlow.deb
   ```

### Windows (Portable)

1. Descarga `VidFlow-Windows-Portable-0.3.0.zip`.
2. Extrae todo el contenido.
3. Entra a `win-unpacked`.
4. Ejecuta `VidFlow.exe`.

### Windows (Instalador .exe)

1. Descarga `VidFlow.exe`.
2. Haz doble clic en `VidFlow.exe`.
3. Sigue el asistente de instalacion.

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
