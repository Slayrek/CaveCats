# ============================================================
#  cursor.py — кастомний курсор у вигляді котячої лапки
#
#  Використання:
#    cursor = PawCursor()
#    # У головному циклі, останнім перед display.flip():
#    cursor.draw(screen, pygame.mouse.get_pos())
# ============================================================

import pygame


class PawCursor:
    """
    Малює котячу лапку замість системного курсора.
    Системний курсор ховається у main.py через pygame.mouse.set_visible(False).
    """

    # Кольори лапки
    PAW_COLOR   = (255, 210, 170)   # персиковий
    PAW_BORDER  = (160, 100,  60)   # коричневий обідок
    PAW_PADDING = (220, 160, 130)   # подушечка

    def draw(self, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        x, y = pos
        self._draw_paw(surface, x, y)

    def _draw_paw(self, surface: pygame.Surface, x: int, y: int) -> None:
        # --- Долоня (велике коло трохи нижче точки кліку) ---
        palm_r = 10
        palm_cx, palm_cy = x, y + 5
        pygame.draw.circle(surface, self.PAW_COLOR,  (palm_cx, palm_cy), palm_r)
        pygame.draw.circle(surface, self.PAW_BORDER, (palm_cx, palm_cy), palm_r, 2)
        # Подушечка долоні
        pygame.draw.ellipse(surface, self.PAW_PADDING,
                            (palm_cx - 5, palm_cy - 4, 10, 8))

        # --- Чотири пальці (маленькі кола вгорі) ---
        toe_r = 5
        toe_positions = [
            (x - 10, y - 6),
            (x - 3,  y - 11),
            (x + 4,  y - 11),
            (x + 11, y - 6),
        ]
        for tx, ty in toe_positions:
            pygame.draw.circle(surface, self.PAW_COLOR,  (tx, ty), toe_r)
            pygame.draw.circle(surface, self.PAW_BORDER, (tx, ty), toe_r, 1)
            # Маленька подушечка пальця
            pygame.draw.circle(surface, self.PAW_PADDING, (tx, ty + 1), toe_r - 2)
