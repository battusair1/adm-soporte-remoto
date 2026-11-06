#!/usr/bin/env python3
"""Genera todos los íconos y el logo de adm Soporte Remoto desde un solo dibujo.

Ícono: el cuadro «AT» de Advising Monitor (fondo oscuro, borde neón cian, «AT» en Share Tech Mono).
Cabecera de la ventana (máx. 300x60 en Flutter): pulso + nombre del programa y, debajo, el sello
«AT · ADVISING TECHNOLOGY · Vendemos soluciones», igual que el menú lateral de AM.

Uso (desde la raíz del repo, con Pillow):  python3 adm/marca/generar_marca.py
"""
import base64
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RAIZ = Path(__file__).resolve().parents[2]
FUENTES = Path(__file__).resolve().parent / "fuentes"

NOMBRE = "adm Soporte Remoto"
FABRICANTE = "ADVISING TECHNOLOGY"
LEMA = "Vendemos soluciones"

CIAN = (34, 211, 238)
FONDO = (10, 14, 20)
FONDO2 = (14, 34, 46)
TEXTO = (230, 246, 250)
LINEA = (31, 45, 61)


def exo(tam, peso=800):
    f = ImageFont.truetype(str(FUENTES / "Exo2-Variable.ttf"), tam)
    f.set_variation_by_axes([peso])
    return f


def mono(tam):
    return ImageFont.truetype(str(FUENTES / "ShareTechMono-Regular.ttf"), tam)


def _cuadro(n, margen, borde, brillo, letra, trazo):
    """Dibuja el cuadro AT a n x n píxeles (n ya es el lienzo sobremuestreado)."""
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    m = margen
    r = int((n - 2 * m) / 4.2)
    caja = (m, m, n - 1 - m, n - 1 - m)
    if brillo:
        halo = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        ImageDraw.Draw(halo).rounded_rectangle(caja, r, outline=CIAN + (170,), width=int(n * 0.05))
        img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(n * 0.02)))
    # degradado a 135°: oscuro arriba a la izquierda, cian tenue abajo a la derecha
    deg = Image.new("RGBA", (n, n))
    dd = ImageDraw.Draw(deg)
    for i in range(0, 2 * n, 2):
        t = i / (2 * n)
        c = tuple(int(FONDO[k] * (1 - t) + FONDO2[k] * t) for k in range(3))
        dd.line([(i, 0), (0, i)], fill=c + (255,), width=3)
    mascara = Image.new("L", (n, n), 0)
    ImageDraw.Draw(mascara).rounded_rectangle(caja, r, fill=255)
    img.paste(deg, (0, 0), mascara)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(caja, r, outline=CIAN, width=max(1, int(n * borde)))
    d.text((n / 2, n / 2 + n * 0.015), "AT", font=mono(int(n * letra)), fill=CIAN, anchor="mm",
           stroke_width=max(1, int(n * trazo)), stroke_fill=CIAN)
    return img


def icono(lado):
    """El ícono a su tamaño final. Los tamaños chicos llevan menos margen, borde y letra más gruesos,
    sin halo, para que el «AT» se lea a 16 px."""
    sobre = 8
    n = lado * sobre
    if lado <= 24:
        img = _cuadro(n, margen=int(n * 0.0), borde=0.075, brillo=False, letra=0.60, trazo=0.03)
    elif lado <= 48:
        img = _cuadro(n, margen=int(n * 0.02), borde=0.05, brillo=False, letra=0.52, trazo=0.02)
    else:
        img = _cuadro(n, margen=int(n * 0.04), borde=0.028, brillo=True, letra=0.46, trazo=0.012)
    return img.resize((lado, lado), Image.LANCZOS)


def bandeja_mac(lado=44):
    """Plantilla monocroma para la barra de menús de macOS (negro con alfa; macOS la tiñe)."""
    n = lado * 8
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = int(n * 0.06)
    d.rounded_rectangle((m, m, n - 1 - m, n - 1 - m), int(n * 0.22), outline=(0, 0, 0, 255), width=int(n * 0.08))
    d.text((n / 2, n / 2 + n * 0.02), "AT", font=mono(int(n * 0.56)), fill=(0, 0, 0, 255), anchor="mm",
           stroke_width=int(n * 0.025), stroke_fill=(0, 0, 0, 255))
    return img.resize((lado, lado), Image.LANCZOS)


def _pulso(d, x, y, alto, color, ancho):
    # mismo trazo que el ícono Activity de lucide (caja de 24)
    puntos = [(22, 12), (18, 12), (15, 21), (9, 3), (6, 12), (2, 12)]
    s = alto / 24
    d.line([(x + px * s, y + py * s) for px, py in puntos], fill=color, width=ancho, joint="curve")


def cabecera(escala=2):
    """Logo de la ventana: 300x60 lógicos, guardado a 600x120 (pantallas HiDPI)."""
    e = escala
    sobre = 3
    k = e * sobre
    w, h = 300 * k, 60 * k
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 12 * k, fill=FONDO)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 12 * k, outline=CIAN + (110,), width=k)
    _pulso(d, 10 * k, 5 * k, 20 * k, CIAN, int(2.2 * k))
    d.text((36 * k, 15 * k), NOMBRE, font=exo(17 * k), fill=CIAN, anchor="lm")
    d.line((10 * k, 29 * k, w - 10 * k, 29 * k), fill=LINEA, width=k)
    sello = _cuadro(22 * k * 2, margen=2, borde=0.05, brillo=False, letra=0.5, trazo=0.02).resize((22 * k, 22 * k), Image.LANCZOS)
    img.alpha_composite(sello, (10 * k, 33 * k))
    d.text((38 * k, 39 * k), FABRICANTE, font=exo(11 * k, 800), fill=TEXTO, anchor="lm")
    d.text((38 * k, 50 * k), LEMA, font=mono(10 * k), fill=CIAN, anchor="lm")
    return img.resize((300 * e, 60 * e), Image.LANCZOS)


def svg_con_png(png):
    b = io.BytesIO()
    png.save(b, "PNG", optimize=True)
    datos = base64.b64encode(b.getvalue()).decode()
    return ('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="256" '
            'height="256" viewBox="0 0 256 256"><image width="256" height="256" '
            f'xlink:href="data:image/png;base64,{datos}"/></svg>')


def guardar_ico(ruta, tamanos):
    grandes = max(tamanos)
    base = icono(grandes)
    # Pillow arma el ICO desde una imagen; append_images da cada tamaño ya dibujado a mano.
    base.save(ruta, format="ICO", sizes=[(s, s) for s in tamanos],
              append_images=[icono(s) for s in tamanos if s != grandes])


def main():
    r = RAIZ
    tamanos_app = [16, 20, 24, 32, 40, 48, 64, 128, 256]
    guardar_ico(r / "res/icon.ico", tamanos_app)
    guardar_ico(r / "flutter/windows/runner/resources/app_icon.ico", tamanos_app)
    guardar_ico(r / "res/tray-icon.ico", [16, 20, 24, 32, 48])

    i256 = icono(256)
    for p in ("res/icon.png", "res/128x128@2x.png", "flutter/assets/icon.png"):
        i256.save(r / p, optimize=True)
    for lado, p in ((32, "res/32x32.png"), (64, "res/64x64.png"), (128, "res/128x128.png")):
        icono(lado).save(r / p, optimize=True)
    i1024 = icono(1024)
    i1024.save(r / "res/mac-icon.png", optimize=True)
    i1024.save(r / "flutter/macos/Runner/AppIcon.icns", format="ICNS",
               append_images=[icono(s) for s in (16, 32, 64, 128, 256, 512)])
    t = bandeja_mac()
    t.save(r / "res/mac-tray-dark-x2.png", optimize=True)
    t.save(r / "res/mac-tray-light-x2.png", optimize=True)

    svg = svg_con_png(i256)
    (r / "res/scalable.svg").write_text(svg)
    (r / "flutter/assets/icon.svg").write_text(svg)

    cab = cabecera()
    for p in ("flutter/assets/logo.png", "flutter/assets/logo_light.png", "flutter/assets/logo_dark.png"):
        cab.save(r / p, optimize=True)
    print("Marca regenerada.")


if __name__ == "__main__":
    main()
