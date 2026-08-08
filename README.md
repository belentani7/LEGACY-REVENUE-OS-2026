# Legacy Revenue OS 2026

Sistema local para vender y operar un servicio gestionado de recepción y calificación de leads. Prioridad inicial: inmobiliarias independientes de España, chat web y WhatsApp, derivación humana obligatoria.

## Qué entrega

- Pipeline: lead, calificado, demo, propuesta, piloto, activo, perdido.
- MRR activo, beneficio bruto, margen y pipeline ponderado.
- Gates comerciales visibles: 20 contactos, 3 demos, 1 propuesta, 1 piloto pagado, 3 clientes retenidos.
- Calculadora de economía unitaria sin precios de proveedor hardcodeados.
- Dossier de piloto: oferta, entrevista, baseline ROI, privacidad y pruebas.
- Persistencia JSON local y atómica.
- API administrativa opcionalmente protegida con comparación constante.
- Dashboard responsive, teclado, contraste y movimiento reducido.

## Inicio Windows

```powershell
cd C:\Users\USER\Videos\drive\LEGACY-REVENUE-OS-2026
Copy-Item .env.example .env
$env:ADMIN_API_KEY='usa-un-secreto-largo-distinto'
uv run --no-project --with-requirements requirements.txt python app.py
```

Abrir `http://127.0.0.1:8091`. Introducir la misma clave en el campo superior. La clave nunca se guarda en archivos ni en `localStorage`.

## Verificación

```powershell
uv run --no-project --with-requirements requirements.txt python -m pytest -q
python -m compileall -q app.py core.py
```

## Decisión comercial

Vender resultado: menos leads perdidos y más visitas calificadas. No vender “una IA”. Primer piloto: alcance de 14 días con baseline firmado. Los valores precargados 300 EUR piloto, 750 EUR alta y 399 EUR/mes son hipótesis de prueba, no precios de mercado confirmados.

## Límites de seguridad

- El sistema no negocia inmuebles, aprueba financiación ni responde cuestiones legales.
- Datos reales solo después de acordar finalidad, retención, acceso y borrado.
- Telefonía, modelos, mensajería y otros consumos se configuran y presupuestan aparte.
- No exponer el servidor a Internet sin TLS, autenticación, rate limiting y revisión operativa.
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
