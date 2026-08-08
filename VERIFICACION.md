# Verificación de entrega

Fecha: 2026-08-08. Entorno: Windows 11, Python 3.12 aislado mediante `uv`.

## Evidencia aprobada

- `pytest`: 18 pruebas aprobadas; cero fallos. Una advertencia deprecada de Starlette/httpx no afecta la ejecución.
- `compileall`: `app.py` y `core.py` compilan sin error.
- JavaScript: el bloque del dashboard compila con `new Function` en Node.
- API: health, ciclo completo de prospecto, autorización, validación, economía y dossier probados offline.
- Seguridad: comparación constante de clave, datos atómicos, traversal de dossier bloqueado, CSP, deny framing, nosniff, referrer y permisos restrictivos.
- Privacidad del frontend: la clave permanece solo en memoria de la pestaña; no usa `localStorage`.
- Responsive estático: viewport, breakpoints 980/580, barra inferior móvil, targets mínimos de 44 px, skip link, `aria-live` y movimiento reducido presentes.
- Escaneo de secretos: ninguna credencial real detectada; solo nombres de variables y valores ficticios de prueba.

## Evidencia pendiente

- Inspección visual real móvil/escritorio: el navegador integrado no logró adjuntar la vista local tras dos intentos. No se declara aceptación visual.
- Rendimiento 60 fps: la interfaz no usa animación continua ni WebGL, pero no se capturó traza de rendimiento.
- Validación comercial: precio, demanda, conversión y retención requieren clientes reales.

## Comandos reproducibles

```powershell
uv run --no-project --with-requirements requirements.txt python -m pytest -q
python -m compileall -q app.py core.py
.\package.ps1
```
