# analysis-artifacts — reto «Planet X and SPHEREx» (Space Apps 2026)

Carpeta de análisis del equipo: documenta el challenge oficial de la NASA
([planet-x-and-spherex](https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/)),
el inventario real del bucket público de datos SPHEREx y las pruebas de renderizado.
Todo el contenido está en español; los nombres propios y las coordenadas se conservan
en su forma original en inglés.

## El reto en 30 segundos

Construir una herramienta web pública donde la persona usuaria introduce ascensión recta
y declinación, y la herramienta muestra imágenes SPHEREx de esa zona del cielo a modo de
pequeño vídeo temporal, para detectar objetos en movimiento (asteroides, cometas,
enanas marrones, un posible Planeta X).

| Dato | Valor |
| --- | --- |
| Evento | NASA Space Apps Challenge 2026 |
| Categoría | Advanced (avanzado) |
| Habilidades sugeridas | Astrophysics, Planets & Moons, Software |
| Publicación / actualización | 2026-09-17 / 2026-10-28 |
| Recursos oficiales | «Resources will be available on Friday, November 13» |

## Contenido de la carpeta

| Archivo | Qué es |
| --- | --- |
| `README.md` (este archivo) | Ficha completa del challenge + índice |
| [spikes/spherex-satellite-architecture.md](spikes/spherex-satellite-architecture.md) | Arquitectura de la misión, instrumentación y repositorio AWS |
| [inventario-bucket-spherex-qr2-qr3.md](inventario-bucket-spherex-qr2-qr3.md) | Inventario observado del bucket: estructura, QR2 vs QR3, calibraciones |
| [spikes/spherex-D1-image-preview.png](spikes/spherex-D1-image-preview.png) | Primer render de un FITS real (detector 1, QR3) |

## Resumen del challenge

Desde 2025, la misión SPHEREx de la NASA cartografía el cielo entero cada seis meses en
102 bandas de luz infrarroja cercana, devolviendo imágenes de más de mil millones de objetos.
Cometas, asteroides, estrellas, enanas marrones e incluso planetas nuevos se revelan al
desplazar su posición entre imágenes, pero ninguna persona puede revisar todos esos datos en
solitario. El reto consiste en crear una herramienta web pública que muestre imágenes del cielo
de la misión SPHEREx y facilite ver cómo cambian con el tiempo.

## Antecedentes

Los asteroides y cometas orbitan alrededor del Sol. Las estrellas cercanas surcan el cielo
a medida que orbitan alrededor de la Galaxia. La Tierra también orbita el Sol, lo que hace que
los objetos próximos a nosotros cambien su posición aparente. Observar estos movimientos nos
ayuda a descubrir nuevos objetos astronómicos y a medir sus distancias. Por ejemplo, el planeta
enano Plutón se descubrió cuando un astrónomo comparó dos imágenes del cielo tomadas en
momentos distintos y reconoció que un punto de luz se había desplazado entre ambas.

Más recientemente, la astronomía ha lanzado búsquedas masivas de objetos cercanos con ayuda
del público siguiendo este mismo procedimiento. Cientos de miles de personas voluntarias han
usado esta técnica para descubrir asteroides, cometas, estrellas y enanas marrones (bolas de
gas demasiado masivas para considerarse planetas pero sin masa suficiente para brillar como
estrellas). De hecho, la mayoría de los cometas y enanas marrones conocidos fueron descubiertos
por voluntariado de este modo, a través de proyectos como
[Backyard Worlds](https://backyardworlds.org).

Desde mayo de 2025, la nueva misión SPHEREx de la NASA devuelve datos únicos que pueden dar
lugar a nuevos descubrimientos. SPHEREx cartografía todo el cielo una vez cada seis meses en
102 bandas de luz infrarroja cercana, lo que la hace especialmente sensible a objetos ricos en
hidrógeno, agua, dióxido de carbono, monóxido de carbono y muchas otras moléculas. Habrá
demasiados datos para que una sola persona —o incluso un programa informático— los comprenda
por completo: imágenes de más de mil millones de objetos (enanas marrones, cuásares, cometas,
asteroides, estrellas, supernovas y galaxias) que a menudo se solapan o varían en brillo.
Se necesitan herramientas nuevas y creativas para aprovechar este tesoro y ayudar a que el
mayor número posible de personas contribuya a los descubrimientos.

## Objetivo

Crear una herramienta web pública que muestre imágenes del cielo de la misión SPHEREx y
facilite ver rápidamente cómo cambian con el tiempo. La persona usuaria introducirá las
coordenadas de una zona del cielo (ascensión recta y declinación) y la herramienta mostrará
una serie de imágenes de esa zona a modo de pequeño vídeo, para detectar con facilidad los
objetos en movimiento.

### Objetos de prueba propuestos

| Objeto | Tipo | Notas |
| --- | --- | --- |
| Estrella de Barnard | Estrella de alta movilidad propia | Desplazamiento rápido entre épocas |
| Epsilon Indi B | Pareja de enanas marrones orbitando una estrella | Sistema múltiple cercano |
| WISE 0855 | Enana marrón de movimiento rápido (AR 08h 55m 10,83s, Dec −07° 14′ 42,5″) | Objeto muy frío y cercano |
| RW Aurigae | Estrella variable | Prueba de variabilidad fotométrica |
| R Draconis | Estrella variable | Prueba de variabilidad fotométrica |

## Consideraciones potenciales (opcionales)

El enunciado aclara que los siguientes puntos pueden tenerse en cuenta, pero no son obligatorios:

* Los nuevos datos de SPHEREx llegan rápido: diseñar una herramienta fácil de actualizar con
  cada nueva entrega de datos.
* Pensar con creatividad cómo mostrar las 102 bandas infrarrojas para que las personas
  usuarias aprovechen su potencial de descubrimiento. Por ejemplo, puede tener sentido sumar
  por separado todos los datos de cada uno de los seis detectores para mejorar la relación
  señal-ruido de las imágenes mostradas. Puntos extra si la herramienta genera espectros al vuelo.
* Ofrecer opciones de sumar o restar imágenes tomadas en momentos distintos para facilitar
  la detección de objetos en movimiento.
* Permitir elegir el campo de visión: campos más amplios permiten seguir fuentes más rápidas,
  a costa de tiempos de transferencia de datos más largos.
* Ofrecer la opción de superponer datos astronómicos de otros telescopios, como la misión
  Gaia o la misión WISE.
* Permitir consultar la herramienta incluyendo las coordenadas en la URL, para incrustarla
  fácilmente en otros sitios y proyectos.
* Mostrar metadatos útiles, como indicadores de contaminación (*contamination flags*).
* Valorar herramientas públicas existentes para manejar datos astronómicos (en el original
  figura como «Astrophy tools», presumiblemente [Astropy](https://www.astropy.org)) y para
  visualizarlos, como [Aladin](https://aladin.cds.unistra.fr/) del Centro de Datos
  Astronómicos de Estrasburgo (CDS).
* Para datos y recursos del challenge, consultar la pestaña *Resources* de la página oficial;
  podrían añadirse más recursos antes del hackatón.

## Fuente

* Página oficial del challenge:
  [planet-x-and-spherex](https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/)
  (imagen destacada:
  [spherex_4.3.jpg](https://assets.spaceappschallenge.org/media/original_images/spherex_4.3.jpg)).
* Contenido extraído el 2026-10-29 del HTML servido por la página (datos embebidos de Next.js)
  y traducido al español.
