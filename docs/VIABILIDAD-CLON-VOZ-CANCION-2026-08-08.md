# Viabilidad: clonar mi voz y generar una cancion

Fecha: 2026-08-08
Decision: viable. La prueba debe separar composicion, voz guia, conversion cantada y mezcla.

## Evidencia local

- GPU: Intel UHD Graphics 620, 1 GB reportado; NVIDIA no disponible.
- Disco C: aproximadamente 28.8 GB libres.
- Disponibles: FFmpeg 8.1.2, FFprobe, Git, Node y Python 3.14.
- No instalados: ACE-Step, Seed-VC, RVC, Applio o pipeline equivalente.
- No se encontraron muestras de voz fuera de material BELENTANI/JUDAS excluido.

Conclusion: no instalar modelos grandes en este PC para la primera prueba. Usar servicio musical y conversion alojada, o GPU remota efimera.

## Ruta seleccionada: prueba inmediata

1. Crear instrumental y voz guia con ACE-Step 1.5 o ACE Music.
2. Grabar una referencia limpia de la voz propia.
3. Crear clon instantaneo en Kits AI Starter.
4. Convertir la voz guia cantada al clon.
5. Exportar stems, alinear, mezclar y normalizar con FFmpeg/DAW.
6. Comparar tres variantes ciegas antes de conservar el clon.

Coste publicado de Kits AI Starter: USD 10/mes, dos ranuras de voz y 15 minutos de descarga. ACE-Step es MIT y su repositorio enlaza una opcion web gratuita. Precio, impuestos y disponibilidad deben reconfirmarse antes de pagar.

Ventaja: primer resultado en una sesion. Riesgo: la clonacion instantanea puede perder identidad en agudos, vibrato o consonantes.

## Ruta privada y controlable

1. ACE-Step 1.5 en GPU remota para composicion, edicion y stems.
2. Seed-VC `seed-uvit-whisper-base`, 44.1 kHz, para conversion de canto.
3. Referencia de voz de 1 a 30 segundos para zero-shot; ajustar con datos propios solo si la prueba falla.
4. Destruir el worker y volumen remoto al terminar.

Seed-VC usa GPL-3.0. ACE-Step usa MIT. Si el codigo se distribuye dentro de un producto, revisar obligaciones GPL antes de integrarlo; como herramienta interna aislada, mantenerlo como proceso separado.

La documentacion de ACE-Step pide Python 3.11-3.12, unos 10 GB y recomienda al menos 4 GB VRAM. En CPU funciona, pero es significativamente mas lento. Este equipo no es objetivo adecuado para produccion local.

## OpenAI

La API actual permite crear voz personalizada con muestra y grabacion de consentimiento, pero solo para clientes elegibles. Es TTS/Realtime; no existe evidencia oficial consultada de que sea un motor de clonacion de canto. Utilidad: intro hablada, tags o narracion. No usar como motor vocal principal de la cancion.

## Material necesario

Crear muestras nuevas, privadas y sin musica:

- `voice_reference.wav`: 60-90 segundos hablando natural, mono, 44.1 o 48 kHz.
- `singing_reference.wav`: 30-60 segundos con notas sostenidas, frase suave y frase intensa.
- `guide_vocal.wav`: melodia y letra completas, seca y afinada de forma natural.
- `CONSENTIMIENTO.txt`: nombre, fecha, uso privado y autorizacion para clonar la voz propia.

No usar master, stems, letra o audio JUDAS mientras siga sellado.

## Gates de calidad

- Identidad: dos de tres oyentes reconocen la voz sin pista visual.
- Letra: 95% de palabras inteligibles.
- Afinacion: sin saltos artificiales o formantes metalicos dominantes.
- Artefactos: sin clicks, silencios anormales o respiraciones duplicadas.
- Mezcla: pico maximo menor de -1 dBTP; sin clipping; version WAV y MP3.
- Privacidad: muestra y clon borrables; nada subido a Git; proveedor y retencion documentados.
- Legal: solo voz propia, composicion original y participacion de IA declarada si se publica.

## Criterio de parada

Producir primero un fragmento de 30-45 segundos. Continuar a cancion completa solo si identidad, diccion y artefactos pasan. Si Kits falla, ejecutar Seed-VC en GPU remota. No entrenar un modelo propio antes de superar el zero-shot.

## Fuentes verificadas

- ACE-Step 1.5: https://github.com/ace-step/ACE-Step-1.5
- Instalacion ACE-Step: https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INSTALL.md
- Seed-VC: https://github.com/Plachtaa/seed-vc
- Kits Voice Changer: https://help.kits.ai/hc/en-us/articles/45057016270611-Voice-Changer-Kits-Studio
- Kits precios: https://www.kits.ai/es/pricing
- OpenAI Audio API: https://developers.openai.com/api/reference/resources/audio
