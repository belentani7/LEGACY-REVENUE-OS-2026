# Plan de revision por zonas criticas

Fecha: 2026-08-08
Objetivo: elevar calidad sin duplicar trabajo ni interferir con agentes activos.

## Mapa de propiedad

| Zona | Estado observado | Regla de trabajo |
|---|---|---|
| `Desktop/BELENTANI-JUDAS-ERA-FULLSTACK` | Otro agente; cambios recientes | Solo lectura. No editar, instalar ni ejecutar procesos persistentes. |
| `Videos/drive/voice-ai-agency` | Rama con trabajo local no comprometido | Congelada hasta reconciliar propietario y diff. |
| `Videos/drive/voice-bot-full` | Git incompleto; base secundaria | Solo auditoria. No usar como base de producto. |
| Sesiones `ciclo_es`, `ciclo_en`, `ciclo_multi`, organizacion cloud | Activas bajo `C:\Users\USER` | No escribir en sus carpetas. |
| `Videos/drive/LEGACY-REVENUE-OS-2026` | Git limpio; zona propia | Documentacion y herramientas de libertad financiera. |

Antes de cada bloque de trabajo:

1. Consultar agentes y sesiones recientes.
2. Ejecutar `git status --short`, rama, HEAD y buscar `index.lock`.
3. Revisar archivos modificados en las ultimas dos horas.
4. Declarar una sola carpeta y entregable como zona propia.
5. Registrar resultado verificable antes de cambiar de zona.

## Orden de revision

### P0. Integridad y no duplicacion

- Propietario, rama y entregable visibles por zona.
- Secretos fuera de Git; muestras de voz fuera del repositorio.
- Nada de reset, limpieza o publicacion remota.
- Diferenciar implementado, probado localmente y publicado.

Gate: cero colisiones detectadas; diff limitado a zona declarada.

### P0. Camino de ingreso

- Una oferta: recepcionista IA gestionado para inmobiliarias independientes.
- Un flujo: capturar, calificar, agendar, resumir y derivar.
- Una metrica primaria: visitas o llamadas calificadas agendadas.
- Un piloto pagado antes de multitenancy o nuevas verticales.

Gate comercial: 20 contactos, 5 conversaciones, 3 demos y 1 propuesta. Dia 30: 1 piloto pagado.

### P0. Seguridad y privacidad

- Consentimiento explicito para voz y datos personales.
- Retencion, borrado y acceso definidos.
- Handoff humano para excepciones.
- Limite de gasto, timeout y log de errores sin datos sensibles.

Gate: 100% de excepciones derivadas; ningun secreto o audio privado versionado.

### P1. Fiabilidad

- Unitarias: calificacion, estados, limites de coste y validadores.
- Integracion: calendario, mensajeria, persistencia y recuperacion de fallos.
- Contrato: payloads de proveedores y webhooks.
- E2E: lead nuevo, cita, derivacion, rechazo y proveedor caido.

Gate: 20 escenarios E2E; 95% de conversaciones sin fallo; respuesta mediana menor de 60 segundos; coste variable menor del 20% del ingreso.

### P1. Frontend

- Mobile 360, 390, 768 y desktop 1440.
- Teclado, foco, contraste WCAG AA y `prefers-reduced-motion`.
- Performance: animacion medida, degradacion ECO y presupuesto de recursos.
- Prueba visual real; build y HTTP 200 no cuentan como aceptacion visual.

Gate: cero bloqueos de teclado, overflow horizontal o errores de consola en rutas criticas.

### P2. Excelencia visual

- Aplicar despues de validar el flujo comercial.
- Mantener identidad cinematografica sin aumentar abandono o tiempo de carga.
- Cada efecto debe tener proposito, fallback y medicion.

## Cadencia

- Bloque 1: mapa de propiedad y estado.
- Bloque 2: una zona P0 y su prueba.
- Bloque 3: correccion de fallos.
- Bloque 4: captura de evidencia y commit local.
- Siguiente zona solo cuando el gate anterior este cerrado.

## Estado actual

- Zona segura establecida: este repositorio.
- BELENTANI reservado al agente de la web.
- Proyectos de voz existentes preservados sin cambios.
- Proxima implementacion permitida: prueba privada de voz en carpeta aislada, despues de recibir muestras nuevas y consentimiento.
