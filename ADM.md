# adm Soporte Remoto

Cliente de soporte remoto de **ADVISING TECHNOLOGY S.A.S.** (Medellín) para la mesa de ayuda de Advising Monitor (adm).
Es una compilación de [RustDesk](https://github.com/rustdesk/rustdesk) **1.5.0** con la marca propia y el servidor
propio. Se distribuye bajo la misma licencia, **AGPL-3.0** (`LICENCE`); este repositorio es su código fuente completo.

## Qué cambia frente a RustDesk 1.5.0

El primer commit importa RustDesk 1.5.0 sin cambios (etiqueta `1.5.0`, commit `fada664`) y `hbb_common` en el commit
`229b904508364c8997aad0fb5af57effac859f60`, que en el original es un submódulo. Todo lo demás está en los commits
siguientes. Nota: al importar, la regla `*png` del `.gitignore` original dejó fuera 120 archivos (imágenes, SVG de la
interfaz y otros ignorados); el commit «Restaura los archivos de RustDesk 1.5.0…» los trae tal cual desde la etiqueta
`1.5.0`, salvo el ícono de respaldo (`flutter/assets/icon.svg`, `res/icon.png`), que es el propio.


- Nombre interno `adm-Soporte-Remoto` (rutas, servicio y registro de Windows); se muestra «adm Soporte Remoto».
- Servidor `rd.atasesorias.com` y su llave **pública**, por defecto (`libs/hbb_common/src/config.rs`).
- Íconos y logo de Advising Technology (`res/`, `flutter/assets/`, `flutter/windows/runner/resources/`), y
  metadatos del ejecutable.
- Sin la leyenda «Powered by RustDesk» en la ventana principal (`hide-powered-by-me`); la atribución y la licencia de
  RustDesk siguen en «Acerca de».
- Compilación solo para Windows x64 (`.github/workflows/build-windows.yml`). Se quitaron los flujos de las demás
  plataformas y no se incluye el controlador de impresora remota.

Por tener nombre propio, el cliente no se actualiza solo a la versión oficial de RustDesk.

## Sacar una versión

1. Etiqueta `adm-vX.Y.Z` (por ejemplo `adm-v1.5.0-1`) y `git push --tags`.
2. El flujo publica un Release con `adm-soporte-remoto-X.Y.Z-x86_64.exe` y su `.sha256`.
3. Advising Monitor descarga el ejecutable, verifica la huella y lo firma antes de entregarlo a los equipos.

Este repositorio no contiene código de Advising Monitor, llaves privadas ni datos de clientes.
