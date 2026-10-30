# 🧛 Mini Vampire Survivors

Un juego de supervivencia 2D estilo *Vampire Survivors* desarrollado en **Python + pygame** mediante **vibecoding guiado**: la IA (Claude) actuó como copiloto de programación y yo dirigí el desarrollo con prompts progresivos, iteré sobre los resultados y validé el comportamiento del código.

> **Actividad:** Vibecoding Guiado: Desarrollo de una Aplicación o Mini-Juego con IA como Copiloto
> **Curso:** AI for Developers Jr. 4 · KODIGO Academy · Semana 2
> **Autor:** Jonathan Alberto
> **IA de apoyo:** Claude (Anthropic)

---

## 📋 Tabla de contenido

1. [Descripción del juego](#-descripción-del-juego)
2. [Instalación y ejecución](#-instalación-y-ejecución)
3. [Controles](#-controles)
4. [Clases de personaje](#-clases-de-personaje)
5. [Estructura del proyecto](#-estructura-del-proyecto)
6. [Evidencia de vibecoding: prompts](#-evidencia-de-vibecoding-prompts)
7. [Iteración y mejora](#-iteración-y-mejora)
8. [Validación del resultado](#-validación-del-resultado)
9. [Partes clave del código](#-partes-clave-del-código)
10. [Reflexión final](#-reflexión-final)
11. [Mejoras futuras](#-mejoras-futuras)

---

## 🎮 Descripción del juego

Controlas a un personaje que **dispara automáticamente** al enemigo más cercano. Tu trabajo es moverte, esquivar a las hordas, recoger gemas de experiencia y elegir mejoras al subir de nivel. Sobrevive el mayor tiempo posible mientras los enemigos se vuelven más numerosos y resistentes.

**Características:**

- 🌍 **Terreno procedural infinito:** el mapa se genera con ruido por bloques (*chunks*), con tierra, pasto, bosques, árboles, rocas y arbustos. Cada partida usa una semilla nueva.
- 👾 **4 tipos de enemigos** con comportamientos distintos: zombi, murciélago, bruto y espectro.
- ⚔️ **Sistema de armas:** proyectil base más cuchillas orbitales, aura ardiente y rayo, mejorables hasta el nivel 5.
- 🧙 **3 clases de personaje** con estadísticas, arma inicial y pasiva propias.
- 🔊 **Sonido sintetizado por código:** efectos y música generados con ondas, sin archivos de audio.
- ⚡ **Optimizado a un máximo de 30 FPS**, con un contador de FPS opcional.

---

## 🚀 Instalación y ejecución

**Requisitos:** Python 3.9 o superior (desarrollado y probado con Python 3.12).

```bash
# 1. Entrar a la carpeta del proyecto
cd vampire_survival

# 2. Instalar la dependencia
pip install -r requirements.txt

# 3. Ejecutar
python main.py
```

Si tu equipo no tiene audio disponible, el juego avisa y continúa sin sonido.

---

## 🕹️ Controles

| Tecla | Acción |
|---|---|
| `WASD` / flechas | Mover al personaje |
| `1`, `2`, `3` (o clic) | Elegir clase en el menú / elegir mejora al subir de nivel |
| `M` | Silenciar o activar el sonido |
| `F` | Mostrar u ocultar el contador de FPS |
| `R` | Volver al menú de clases tras morir |
| `ESC` | Salir |

---

## 🧙 Clases de personaje

| Clase | Vida | Velocidad | Daño | Arma inicial | Pasiva |
|---|---|---|---|---|---|
| **Guerrero** | 120 | 225 | x1.15 | Cuchillas orbitales | Daño +15% |
| **Tanque** | 220 | 185 | x0.90 | Aura ardiente | -25% de daño recibido y regeneración de 0,8 vida/s |
| **Mago** | 75 | 235 | x1.00 | Rayo | +20% de experiencia, cadencia +30% e imán de gemas más amplio |

---

## 📁 Estructura del proyecto

```
vampire_survival/
├── main.py              # Versión final (v4)
├── requirements.txt     # Dependencias (pygame)
├── README.md            # Este documento
└── versiones/           # Historial de iteraciones
    ├── main_v1.py       # v1: juego base
    ├── main_v2.py       # v2: enemigos, armas, sonido y terreno
    └── main_v3.py       # v3: optimización a 30 FPS
```

Conservar cada versión permite comparar el código antes y después de cada prompt.

---

## 🧠 Evidencia de vibecoding: prompts

El desarrollo avanzó en **4 iteraciones**, cada una guiada por un prompt. Los prompts se transcriben tal como los escribí; solo se corrigieron ortografía, mayúsculas y puntuación. Para cada iteración documento qué se pidió, cómo se ajustó el enfoque y qué resultó.

---

### Iteración 1: Juego base

**Prompt:**
> Un Juego Estilo Vampire Survival.

**Qué se pidió a la IA:** una primera versión funcional del género. La IA la interpretó como un bucle de juego completo: movimiento con WASD, disparo automático al enemigo más cercano, enemigos que aparecen desde los bordes y persiguen al jugador, gemas de experiencia, menú de tres mejoras al subir de nivel y pantalla de game over con reinicio.

**Ajuste del prompt:** el prompt definía únicamente el *género*, sin controles, condiciones de derrota ni requisitos de calidad, por lo que la IA tuvo que decidir esos detalles por su cuenta. Un prompt más sólido habría fijado esos puntos desde el inicio. En la práctica lo compensé iterando: probé el resultado y pedí los cambios en los prompts siguientes.

**Resultado:** `versiones/main_v1.py`. Jugable, pero con enemigos y armas uniformes y sin sonido.

---

### Iteración 2: Variedad, sonido y mundo procedural

**Prompt:**
> No hay variedad de enemigos ni de armas, No hay sonido generemos variedad , ademas crear un terreno que se genere de manera aleatoria.

**Qué se pidió a la IA:** cuatro mejoras en una sola iteración: enemigos de distintos tipos, armas nuevas, sonido y un terreno generado aleatoriamente. La IA las resolvió con cuatro tipos de enemigos de aparición progresiva, tres armas mejorables hasta el nivel 5, sonido sintetizado por código y un mundo infinito generado por bloques con cámara.

**Ajuste del prompt:** este prompt ya nace de probar la versión anterior: identifica con claridad tres carencias reales (variedad, sonido, entorno). Lo que quedó abierto fueron los criterios de calidad: cuántos tipos de enemigos o armas se esperaban, si el terreno debía ser infinito o limitado y cómo debía comportarse el audio si el equipo no lo soportaba. La IA tomó esas decisiones y yo las validé después.

**Resultado:** `versiones/main_v2.py`. Cuatro enemigos, tres armas, ocho efectos de sonido más música y terreno infinito con cámara.

---

### Iteración 3: Optimización a 30 FPS

**Prompt:**
> Optimicemos la fluides de juego,  máximo 30 FPS.

**Qué se pidió a la IA:** limitar los cuadros por segundo y reducir el consumo de recursos sin cambiar el comportamiento del juego. La IA fijó el tope en 30 FPS, optimizó las colisiones con una cuadrícula espacial, revisó el riesgo de que los proyectiles atravesaran enemigos con menos cuadros, guardó en caché textos y superficies, y añadió un contador de FPS.

**Ajuste del prompt:** «optimizar» es una petición amplia. Un prompt más preciso habría indicado *qué medir* (tiempo por cuadro), *en qué escenario* (el peor caso, con muchos enemigos) y *qué riesgos revisar* (efectos de bajar los FPS en la física). Por eso verifiqué el resultado con mediciones y con una comparación entre 30 y 60 FPS.

**Resultado:** `versiones/main_v3.py`. Tope de 30 FPS, colisiones más eficientes y tecla `F` para ver los FPS.

---

### Iteración 4: Clases de personaje

**Prompt:**
> Agreguemos clases de personajes, como tanque/mago/guerrero.

**Qué se pidió a la IA:** un sistema de clases de personaje. La IA lo resolvió con un menú de selección al iniciar y tras morir, estadísticas distintas por clase, un arma inicial propia, una pasiva única y un aspecto visual diferenciado para cada una, con las clases definidas como datos editables.

**Ajuste del prompt:** el prompt da la idea y los nombres de las clases, pero deja abiertas decisiones de diseño importantes: cómo se elige la clase, qué diferencia a una de otra y cómo se comprueba que funcionan. Un prompt más sólido las habría especificado. Aquí lo compensé revisando los resultados con pruebas numéricas de las pasivas y con capturas del menú, donde detecté textos que se salían de las tarjetas.

**Resultado:** `main.py` (versión final). Tres clases con menú de selección, pasivas y diseño visual propio.

---

### 📝 Qué aprendí sobre escribir prompts

Mis prompts fueron cortos y dependieron de que la IA completara los detalles. Funcionaron porque iteré sobre cada respuesta, pero el análisis de cada iteración muestra un patrón claro de lo que mejoraría los resultados desde el primer intento:

1. **Rol y contexto:** indicar sobre qué código se trabaja.
2. **Requisitos concretos** en lugar de ideas generales.
3. **Restricciones:** qué no se debe romper.
4. **Criterios de aceptación** que se puedan comprobar.

---

## 🔄 Iteración y mejora

| Versión | Mejora solicitada | Impacto visible en el resultado |
|---|---|---|
| v1 → v2 | Más enemigos, armas, sonido y terreno | De círculos rojos sobre fondo liso a un mundo con árboles, rocas y cuatro tipos de enemigos con aspecto propio, más armas visibles (cuchillas, aura, rayo) y audio |
| v2 → v3 | Tope de 30 FPS | Contador de FPS y menor tiempo por cuadro en el peor caso (de unos 12,5 ms a unos 9,6 ms en las pruebas) |
| v3 → v4 | Clases de personaje | Menú inicial de selección, tres personajes con aspecto distinto y partidas que se sienten diferentes según la clase |

---

## ✅ Validación del resultado

### Cómo probé el código

Combiné **pruebas automatizadas** (ejecutadas con ayuda de la IA, sin ventana gráfica) y **pruebas manuales**.

**Pruebas automatizadas:**

- Simulación de partidas completas con un bot que se mueve y elige mejoras al azar, en las tres clases, sin errores.
- Prueba de estrés: 220 enemigos vivos, las tres armas al nivel 5 y 8 proyectiles. Peor caso de unos 9,6 ms por cuadro, frente a los 33 ms disponibles a 30 FPS.
- Comparación de 60 s de juego a 30 y a 60 FPS: mismo número de bajas (73), lo que indica que la física no depende de los FPS.
- Comprobación de que el terreno es **determinista**: la misma semilla y las mismas coordenadas generan exactamente la misma imagen.
- Pasivas verificadas con números: el Tanque recibe 7,5 de un golpe de 10, regenera vida y el Mago gana 1,2 de experiencia por cada gema.
- Entrada real: se simuló la tecla `3` en el bucle principal y arrancó la clase Mago.
- Capturas de pantalla del juego en cada versión para revisar la interfaz.

**Pruebas manuales** :

-  Jugué al menos 5 minutos con cada clase.
-  Comprobé el sonido y la tecla `M`.
-  Verifiqué que `F` muestra unos 30 FPS estables en mi equipo.
-  Probé la selección de clase con teclado y con mouse.

### Errores, limitaciones y ajustes encontrados

| Hallazgo | Tipo | Ajuste |
|---|---|---|
| El texto de las tarjetas del menú de mejoras quedaba justo al borde, y en el menú de clases algunas líneas se salían de la tarjeta | Error visual | Ensanché las tarjetas y acorté los textos; lo verifiqué con nuevas capturas |
| Al bajar a 30 FPS cada cuadro avanza más: se sospechó que los proyectiles podrían atravesar enemigos pequeños | Riesgo revisado | La prueba mostró que con los tamaños actuales no ocurría (26 px de ancho de impacto contra 15 px de avance); se mantuvo la colisión por segmento como margen de seguridad |
| Los enemigos se amontonan en un mismo punto al perseguir al jugador | Limitación conocida | Pendiente: añadir separación entre enemigos |
| En una prueba con bot, el Tanque duró casi el doble que las otras clases | Posible desequilibrio | Pendiente de confirmar jugando; las estadísticas están en el diccionario `CLASSES` y se ajustan fácilmente |

---

## 🔍 Partes clave del código

| Parte | Qué hace |
|---|---|
| **Bucle principal (`main`)** | Lee eventos, actualiza el juego con `dt` (tiempo entre cuadros) y dibuja. El `dt` hace que la velocidad no dependa de los FPS. |
| **`Game.update`** | Orquesta cada cuadro: movimiento, aparición de enemigos, armas, colisiones y recogida de gemas. |
| **`CLASSES` y `Player`** | Las clases son datos en un diccionario; `Player` aplica las estadísticas de la clase elegida. Añadir una clase nueva solo requiere una entrada nueva. |
| **`build_choices`** | Construye las opciones al subir de nivel: mejoras generales más armas nuevas o mejoras de armas según lo que ya se tenga. |
| **`Terrain`** | Genera el mapa por bloques de 512 px con ruido de valores y decoración aleatoria con semilla, y guarda en caché los bloques visibles. |
| **Colisiones** | Cuadrícula espacial para reducir comparaciones y colisión de proyectiles por segmento. |
| **`Audio`** | Sintetiza ondas (cuadrada, diente de sierra, ruido, seno) en memoria para generar efectos y música. |

---

## 💡 Reflexión final

### Qué aprendí usando IA para programar

Aprendí que la IA acelera mucho la fase de prototipado: pasé de una idea de una línea a un juego con terreno procedural, audio y clases en pocas iteraciones. También aprendí que **dirigir bien importa más que escribir código**: los resultados mejoraron cuando mis peticiones fueron concretas, cuando pedía cambios pequeños y cuando revisaba el resultado antes de pedir el siguiente. Además, ver el código generado me sirvió para aprender técnicas nuevas, como el ruido procedural, la cuadrícula espacial y la síntesis de audio.

### Ventajas y límites del vibecoding

**Ventajas:**
- Velocidad: ideas complejas se vuelven prototipos funcionales rápidamente.
- Aprendizaje: expone técnicas y patrones que quizá no conocía.
- Iteración ágil: cambiar el diseño cuesta una conversación, no una reescritura.

**Límites:**
- La IA puede producir código que parece correcto pero esconde problemas (desbordes de texto, posibles desequilibrios, supuestos no declarados), por lo que **hay que probar y validar siempre**.
- No puede juzgar cosas que dependen de jugar el juego, como el balance o si algo es divertido.
- Si acepto código sin entenderlo, pierdo el control de lo que estoy construyendo y me cuesta depurarlo o extenderlo.

### Qué partes del código comprendo y cuáles necesito reforzar

**Comprendo bien:**
- El bucle del juego y el uso de `dt`.
- La estructura de clases y entidades (`Player`, `Enemy`, `Projectile`, `Gem`).
- El sistema de mejoras y armas, y cómo `CLASSES` define a cada personaje.
- La lógica de aparición progresiva de enemigos y de subida de nivel.

**Necesito reforzar:**
- El ruido de valores y la generación procedural del terreno.
- La cuadrícula espacial y la colisión de proyectiles por segmento.
- La síntesis de audio (generación de ondas en memoria).
- Las técnicas de caché del renderizado.

---

## 🔮 Mejoras futuras

- Separación entre enemigos para evitar que se amontonen.
- Balance de clases tras más pruebas de juego.
- Nuevas clases, armas y jefes.
- Guardado de récords (tiempo y bajas).
- Sprites y animaciones en lugar de formas geométricas.

---

*Desarrollado con vibecoding guiado · KODIGO Academy*