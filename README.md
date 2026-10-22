# Legacy Revenue OS 2026

Sistema local para vender y operar un servicio gestionado de recepción y calificación de leads. Prioridad inicial: inmobiliarias independientes de España, chat web y WhatsApp, derivación humana obligatoria.

## Qué entrega

- Pipeline: lead, calificado, demo, propuesta, piloto, activo, perdido.
- MRR activo, beneficio bruto, margen y pipeline ponderado.
- Gates comerciales visibles: 20 contactos, 3 demos, 1 propuesta, 1 piloto pagado, 3 clientes retenidos.
- Calculadora de economía unitaria sin precios de proveedor hardcodeados.
- Dossier de piloto: oferta, entrevista, baseline ROI, privacidad y pruebas.
- Persistencia JSON local y atómica, operaciones CRM serializadas entre hilos y carpetas de pilotos con nombres únicos (evita colisiones del mismo segundo). El almacenamiento rechaza ficheros incompletos o corruptos sin borrar clientes; los expedientes de piloto se preparan en carpeta temporal y se publican solo cuando los seis archivos están completos.
- **API administrativa obligatoriamente protegida** con clave configurada y comparación constante. Sin `ADMIN_API_KEY`, las rutas de clientes responden HTTP 503; nunca queda un CRM abierto por omisión.
- Dashboard responsive, teclado, contraste y movimiento reducido.

## Inicio Windows

```powershell
cd C:\Users\USER\Videos\drive\LEGACY-REVENUE-OS-2026
Copy-Item .env.example .env
$env:ADMIN_API_KEY='usa-un-secreto-largo-distinto'
uv run --no-project --with-requirements requirements.txt python app.py
```

Abrir `http://127.0.0.1:8091`. Introducir la misma clave en el campo superior. La clave nunca se guarda en archivos ni en `localStorage`.

**Obligatorio:** exportar `ADMIN_API_KEY` antes de arrancar, preferiblemente con un secreto generado aleatoriamente de al menos 32 bytes. Copiar `.env.example` a `.env` no basta: este servidor no carga `.env` automáticamente. Nunca incluyas claves reales en Git, formularios de prueba compartidos, capturas o documentación.

## Verificación

```powershell
uv run --no-project --with-requirements requirements.txt python -m pytest -q
# Comprueba que la API SIN CLAVE devuelve 503 y no guarda leads; con clave, exige cabecera.
python -m compileall -q app.py core.py
```

## Decisión comercial

Vender resultado: menos leads perdidos y más visitas calificadas. No vender “una IA”. Primer piloto: alcance de 14 días con baseline firmado. Los valores precargados 300 EUR piloto, 750 EUR alta y 399 EUR/mes son hipótesis de prueba, no precios de mercado confirmados.

## Límites de seguridad

- El sistema no negocia inmuebles, aprueba financiación ni responde cuestiones legales.
- Datos reales solo después de acordar finalidad, retención, acceso y borrado.
- Telefonía, modelos, mensajería y otros consumos se configuran y presupuestan aparte.
- No exponer el servidor a Internet sin TLS, autenticación fuerte, límites de peticiones, controles CSRF/Origin, proxy y revisión operativa. La clave compartida está diseñada únicamente para administración local; no es una solución SaaS multiusuario.
- La protección de concurrencia es intra-proceso (hilos); no ejecutar múltiples workers sobre el mismo JSON sin una base de datos transaccional.
- No incluir `.env`, datos de clientes o carpetas `pilots/` en paquetes públicos.

## Estructura

```text
app.py                 API y servidor del dashboard
core.py                persistencia, pipeline, finanzas y dossier
dashboard/index.html   centro de comando móvil/escritorio
tests/                 pruebas offline
docs/                  oferta y sistema operativo comercial
data/                  datos locales excluidos del ZIP
pilots/                dossiers privados excluidos del ZIP
```
