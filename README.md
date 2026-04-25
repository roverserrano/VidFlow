# VidFlow

VidFlow es una aplicacion desktop para descargar video y audio desde YouTube, TikTok y Facebook. La nueva arquitectura separa Electron/React para la interfaz y FastAPI + `yt-dlp` para el backend local.

## Estado

MVP en refactor completo:

- Electron controla ventana, IPC seguro, dialogos del sistema y notificaciones nativas.
- React renderiza descarga, historial, ajustes, toasts y barra de estado.
- FastAPI expone metadata, descargas, progreso SSE, historial y configuracion persistente.
- `yt-dlp` y `ffmpeg` son la base de descarga, fusion y extraccion.
- `electron-builder` queda preparado para NSIS en Windows y AppImage/.deb en Linux.

## Estructura

```text
VidFlow/
├── electron/
│   ├── main.js
│   ├── preload.js
│   ├── ipc/
│   └── services/
├── renderer/
│   ├── index.html
│   ├── vite.config.js
│   └── src/
├── backend/
│   ├── main.py
│   ├── api/
│   ├── downloader/
│   ├── models/
│   ├── services/
│   └── utils/
├── resources/
│   ├── bin/
│   ├── icons/
│   └── python/
├── tests/
├── package.json
├── electron-builder.json
├── pyproject.toml
└── requirements.txt
```

## Desarrollo

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm install
npm run dev
```

El comando `npm run dev` levanta Vite y abre Electron. Electron inicia el backend FastAPI local en `127.0.0.1:8716`.

Para ejecutar solo el backend:

```bash
.venv/bin/python main.py
```

## Flujo De Descarga

1. El usuario pega una URL y pulsa `Pegar y analizar` o `Analizar`.
2. La UI llama al backend local por IPC/HTTP.
3. El backend detecta plataforma y usa el downloader correspondiente.
4. `yt-dlp` obtiene metadata, miniatura, duracion y formatos.
5. El usuario elige video o audio y calidad/formato.
6. El backend descarga con `yt-dlp`, fusiona con `ffmpeg` y emite progreso por SSE.
7. La UI actualiza porcentaje, velocidad, ETA y estado.
8. Al completar, se registra historial y Electron muestra notificacion nativa.

## Empaquetado

```bash
npm run package:linux
npm run package:win
```

`package:linux` genera primero el backend embebido con PyInstaller y luego crea AppImage + `.deb`. El backend queda en `resources/python/linux/vidflow-backend` y Electron lo usa automaticamente cuando la app esta empaquetada.

Para Windows, ejecuta `npm run package:win` desde Windows para generar NSIS. Desde Linux se requiere `wine` para completar el instalador NSIS.

`electron-builder` incluye `resources/bin` y `resources/python` como recursos extra. Para builds finales de cada plataforma coloca ahi los binarios correspondientes de `ffmpeg` y el backend Python embebido.

## Pruebas

```bash
npm run test:backend
npm run test:renderer
```

## Configuracion Persistente

La configuracion se guarda como JSON en el directorio de usuario mediante `platformdirs`. Incluye carpeta de destino, tema, formato de audio y nivel de logs.
