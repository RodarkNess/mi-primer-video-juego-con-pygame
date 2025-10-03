import pygame

import pygame
from pygame.locals import *

# ------------------ Configuración básica ------------------
ANCHO, ALTO = 900, 520
FPS = 60

# Colores
NEGRO   = ( 20,  20,  20)
BLANCO  = (245, 245, 245)
GRIS    = (100, 100, 100)
AZUL    = ( 66, 135, 245)
VERDE   = ( 76, 187,  23)
ROJO    = (220,  50,  50)
AMARILLO= (250, 200,  50)
MORADO  = (140,  80, 190)

# Física
GRAVEDAD = 0.7
VEL_X = 4.2
SALTO = 12

# ------------------ Entidades ------------------
class Plataforma:
    """
    Plataforma rectangular. Soporta movimiento en eje 'x' o 'y'.
    - Si es móvil, oscila entre min_val y max_val a una velocidad dada.
    """
    def __init__(self, x, y, w, h, color=GRIS, movil=False, eje='x', min_val=0, max_val=0, vel=0):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.movil = movil
        self.eje = eje
        self.min_val = min_val
        self.max_val = max_val
        self.vel = vel
        self._dx = 0
        self._dy = 0

    def update(self):
        self._dx, self._dy = 0, 0
        if not self.movil or self.vel == 0:
            return

        if self.eje == 'x':
            new_x = self.rect.x + self.vel
            if new_x < self.min_val or new_x > self.max_val:
                self.vel *= -1
                new_x = self.rect.x + self.vel
            self._dx = new_x - self.rect.x
            self.rect.x = new_x

        elif self.eje == 'y':
            new_y = self.rect.y + self.vel
            if new_y < self.min_val or new_y > self.max_val:
                self.vel *= -1
                new_y = self.rect.y + self.vel
            self._dy = new_y - self.rect.y
            self.rect.y = new_y

    @property
    def delta(self):
        return self._dx, self._dy

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect)


class Enemigo:
    """
    Enemigo rectangular que patrulla horizontalmente entre min_x y max_x.
    """
    def __init__(self, x, y, w, h, min_x, max_x, vel=2.2, color=ROJO):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_x = min_x
        self.max_x = max_x
        self.vel = vel
        self.color = color

    def update(self):
        self.rect.x += self.vel
        if self.rect.left < self.min_x or self.rect.right > self.max_x:
            self.vel *= -1
            self.rect.x += self.vel  # Corrige pequeño solape tras invertir

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect)


class Jugador:
    def __init__(self, x, y, w=30, h=40, color=AZUL):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.vx = 0
        self.vy = 0
        self.en_piso = False
        self.plat_bajo = None  # referencia a plataforma donde está parado

    def manejar_input(self, keys):
        self.vx = 0
        if keys[K_a] or keys[K_LEFT]:
            self.vx = -VEL_X
        if keys[K_d] or keys[K_RIGHT]:
            self.vx = VEL_X
        # salto solo si está en el piso
        if (keys[K_SPACE] or keys[K_w] or keys[K_UP]) and self.en_piso:
            self.vy = -SALTO
            self.en_piso = False
            self.plat_bajo = None

    def aplicar_gravedad(self):
        self.vy += GRAVEDAD
        if self.vy > 20:
            self.vy = 20

    def mover_y_colisionar(self, plataformas):
        # Movimiento horizontal
        self.rect.x += self.vx
        for p in plataformas:
            if self.rect.colliderect(p.rect):
                if self.vx > 0:  # moviendo a la derecha
                    self.rect.right = p.rect.left
                elif self.vx < 0:  # izquierda
                    self.rect.left = p.rect.right

        # Movimiento vertical
        self.rect.y += self.vy
        self.en_piso = False
        self.plat_bajo = None
        for p in plataformas:
            if self.rect.colliderect(p.rect):
                if self.vy > 0:  # cayendo
                    self.rect.bottom = p.rect.top
                    self.vy = 0
                    self.en_piso = True
                    self.plat_bajo = p
                elif self.vy < 0:  # subiendo
                    self.rect.top = p.rect.bottom
                    self.vy = 0

        # Si está parado sobre plataforma móvil, se "arrastra" con su delta x
        if self.en_piso and isinstance(self.plat_bajo, Plataforma) and self.plat_bajo.movil:
            dx, dy = self.plat_bajo.delta
            self.rect.x += dx
            # si plataforma sube, acompaña solo si no genera clip
            if dy < 0:
                self.rect.y += dy

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect)


# ------------------ Nivel y lógica de juego ------------------
def crear_nivel():
    plataformas = []

    # Suelo y bases
    plataformas.append(Plataforma(0, ALTO - 40, ANCHO, 40, color=VERDE))
    plataformas.append(Plataforma(80, ALTO - 120, 120, 20))
    plataformas.append(Plataforma(260, ALTO - 180, 120, 20))
    plataformas.append(Plataforma(460, ALTO - 240, 120, 20))
    plataformas.append(Plataforma(700, ALTO - 300, 140, 20))

    # Plataformas móviles
    # Horizontal que ayuda a cruzar un hueco
    plataformas.append(Plataforma(
        x=180, y=ALTO - 90, w=100, h=18,
        color=AMARILLO, movil=True, eje='x', min_val=150, max_val=360, vel=2.5
    ))
    # Vertical cerca del final
    plataformas.append(Plataforma(
        x=620, y=ALTO - 170, w=90, h=18,
        color=AMARILLO, movil=True, eje='y', min_val=ALTO - 260, max_val=ALTO - 120, vel=2
    ))

    enemigos = []
    # Enemigo que patrulla sobre una plataforma intermedia
    enemigos.append(Enemigo(
        x=270, y=ALTO - 200, w=28, h=28,
        min_x=260, max_x=380, vel=2.1, color=ROJO
    ))
    # Enemigo cercano al final
    enemigos.append(Enemigo(
        x=710, y=ALTO - 328, w=28, h=28,
        min_x=700, max_x=840, vel=2.4, color=MORADO
    ))

    # Meta (rectángulo verde claro)
    meta = pygame.Rect(ANCHO - 60, ALTO - 80, 30, 40)

    return plataformas, enemigos, meta


def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Plataformas Rectangulares - Microjuego")
    reloj = pygame.time.Clock()
    fuente = pygame.font.SysFont("consolas", 22)
    fuente_titulo = pygame.font.SysFont("consolas", 36, bold=True)

    estado = "inicio"  # "inicio" | "jugando" | "ganaste"
    muertes = 0

    # Arranque de nivel
    plataformas, enemigos, meta = crear_nivel()
    jugador_spawn = (40, ALTO - 100)
    jugador = Jugador(*jugador_spawn)

    def reiniciar():
        nonlocal plataformas, enemigos, meta, jugador
        plataformas, enemigos, meta = crear_nivel()
        jugador = Jugador(*jugador_spawn)
        return jugador

    corriendo = True
    while corriendo:
        dt = reloj.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == QUIT:
                corriendo = False
            if event.type == KEYDOWN:
                if estado == "inicio" and event.key in (K_RETURN, K_SPACE):
                    estado = "jugando"
                elif estado == "ganaste" and event.key in (K_RETURN, K_r):
                    muertes = 0
                    jugador = reiniciar()
                    estado = "jugando"
                elif estado == "jugando" and event.key == K_r:
                    jugador = reiniciar()

        if estado == "inicio":
            pantalla.fill(NEGRO)
            titulo = fuente_titulo.render("PLATAFORMAS RECTANGULARES", True, BLANCO)
            subt = fuente.render("Usa A/D o ←/→ para moverte, SPACE/W/↑ para saltar.", True, BLANCO)
            subt2 = fuente.render("Plataformas móviles, enemigos y contador de muertes.", True, BLANCO)
            start = fuente.render("Presiona ENTER para comenzar", True, AMARILLO)

            # Dibujitos rectangulares de ejemplo
            pygame.draw.rect(pantalla, AZUL, pygame.Rect(120, 320, 40, 50))
            pygame.draw.rect(pantalla, GRIS, pygame.Rect(80, 380, 200, 20))
            pygame.draw.rect(pantalla, AMARILLO, pygame.Rect(300, 360, 120, 18))
            pygame.draw.rect(pantalla, ROJO, pygame.Rect(460, 352, 28, 28))

            pantalla.blit(titulo, (ANCHO//2 - titulo.get_width()//2, 80))
            pantalla.blit(subt, (ANCHO//2 - subt.get_width()//2, 140))
            pantalla.blit(subt2, (ANCHO//2 - subt2.get_width()//2, 170))
            pantalla.blit(start, (ANCHO//2 - start.get_width()//2, 230))

            pygame.display.flip()
            continue

        # ------------------ Actualización (jugando o ganaste) ------------------
        if estado in ("jugando", "ganaste"):
            keys = pygame.key.get_pressed()

            if estado == "jugando":
                # Actualizar plataformas (para obtener sus deltas)
                for p in plataformas:
                    p.update()

                # Input, física y colisiones del jugador
                jugador.manejar_input(keys)
                jugador.aplicar_gravedad()
                jugador.mover_y_colisionar(plataformas)

                # Actualizar enemigos
                for e in enemigos:
                    e.update()

                # Muere si cae fuera de la pantalla
                if jugador.rect.top > ALTO + 60:
                    muertes += 1
                    jugador = Jugador(*jugador_spawn)

                # Muere si toca enemigo
                for e in enemigos:
                    if jugador.rect.colliderect(e.rect):
                        muertes += 1
                        jugador = Jugador(*jugador_spawn)
                        break

                # Gana si llega a la meta
                if jugador.rect.colliderect(meta):
                    estado = "ganaste"

            # ------------------ Dibujo ------------------
            pantalla.fill(NEGRO)

            # Dibujar meta (rectángulo)
            pygame.draw.rect(pantalla, (120, 230, 120), meta)

            # Dibujar plataformas
            for p in plataformas:
                p.draw(pantalla)

            # Dibujar enemigos
            for e in enemigos:
                e.draw(pantalla)

            # Dibujar jugador
            jugador.draw(pantalla)

            # UI: contador de muertes y estado
            texto_muertes = fuente.render(f"Muertes: {muertes}", True, BLANCO)
            pantalla.blit(texto_muertes, (12, 10))

            if estado == "ganaste":
                msg = fuente_titulo.render("¡GANASTE!", True, AMARILLO)
                hint = fuente.render("ENTER o R para reiniciar", True, BLANCO)
                box_w, box_h = msg.get_width()+60, msg.get_height()+60
                box = pygame.Rect(ANCHO//2 - box_w//2, 80, box_w, box_h)
                pygame.draw.rect(pantalla, (30,30,30), box)
                pygame.draw.rect(pantalla, (80,80,80), box, 2)
                pantalla.blit(msg, (ANCHO//2 - msg.get_width()//2, 95))
                pantalla.blit(hint, (ANCHO//2 - hint.get_width()//2, 145))

            # Tips
            hint2 = fuente.render("R: reiniciar nivel | ESC para salir", True, GRIS)
            pantalla.blit(hint2, (ANCHO - hint2.get_width() - 12, 10))

            pygame.display.flip()

        # Salida con ESC
        if pygame.key.get_pressed()[K_ESCAPE]:
            corriendo = False

    pygame.quit()


if __name__ == "__main__":
    main()