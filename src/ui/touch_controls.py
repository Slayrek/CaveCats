import pygame
import math
from src.core.settings import WIDTH, HEIGHT

class TouchController:
    def __init__(self):
        self.active = True
        self.joystick_base = (120, HEIGHT - 120)
        self.joystick_radius = 60
        self.stick_radius = 25
        self.stick_pos = list(self.joystick_base)
        self.joystick_active = False
        self.joystick_finger = None

        self.buttons = {
            "jump": {"rect": pygame.Rect(WIDTH - 120, HEIGHT - 100, 80, 80), "pressed": False, "finger": None, "color": (100, 200, 100)},
            "zoom_in": {"rect": pygame.Rect(WIDTH - 70, 20, 50, 50), "pressed": False, "finger": None, "color": (200, 200, 200), "text": "+"},
            "zoom_out": {"rect": pygame.Rect(WIDTH - 140, 20, 50, 50), "pressed": False, "finger": None, "color": (200, 200, 200), "text": "-"},
            "inv": {"rect": pygame.Rect(WIDTH - 210, 20, 50, 50), "pressed": False, "finger": None, "color": (200, 200, 200), "text": "E"},
            "menu": {"rect": pygame.Rect(10, 10, 80, 40), "pressed": False, "finger": None, "color": (100, 150, 200), "text": "MENU"}
        }

        # Dynamic interact button, appears only when near functional block
        self.interact_btn = {"rect": pygame.Rect(WIDTH - 220, HEIGHT - 100, 80, 80), "pressed": False, "finger": None, "visible": False}

        self.left_pressed = False
        self.right_pressed = False
        self.jump_pressed = False
        self.interact_pressed = False
        
        self.zoom_in_clicked = False
        self.zoom_out_clicked = False
        self.inv_clicked = False
        self.menu_clicked = False

        # Action (mining/placing) happens via a tap anywhere outside UI
        self.action_tap = None      # (x, y) of tap down
        self.action_hold = None     # (x, y) if holding
        self.action_finger = None

    def update_resolution(self, w, h):
        self.joystick_base = (120, h - 120)
        self.buttons["jump"]["rect"].bottomright = (w - 40, h - 40)
        self.buttons["zoom_in"]["rect"].topright = (w - 20, 20)
        self.buttons["zoom_out"]["rect"].topright = (w - 80, 20)
        self.buttons["inv"]["rect"].topright = (w - 140, 20)
        self.interact_btn["rect"].bottomright = (w - 140, h - 40)
        if not self.joystick_active:
            self.stick_pos = list(self.joystick_base)

    def handle_event(self, event, ui_is_open=False):
        if not self.active: return False
        
        # We assume pygame 2+ finger events or mouse events emulating touch
        # For PC testing, we use MOUSEBUTTONDOWN as well
        
        pos = None
        finger_id = -1
        is_down = False
        is_up = False
        is_motion = False

        if event.type == pygame.FINGERDOWN:
            pos = (event.x * WIDTH, event.y * HEIGHT) # Will need actual screen w/h
            finger_id = event.finger_id
            is_down = True
        elif event.type == pygame.FINGERUP:
            pos = (event.x * WIDTH, event.y * HEIGHT)
            finger_id = event.finger_id
            is_up = True
        elif event.type == pygame.FINGERMOTION:
            pos = (event.x * WIDTH, event.y * HEIGHT)
            finger_id = event.finger_id
            is_motion = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            finger_id = 'mouse'
            is_down = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            pos = event.pos
            finger_id = 'mouse'
            is_up = True
        elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
            pos = event.pos
            finger_id = 'mouse'
            is_motion = True

        if not pos:
            return False

        handled = False

        if is_down:
            # Check joystick
            dx = pos[0] - self.joystick_base[0]
            dy = pos[1] - self.joystick_base[1]
            if math.hypot(dx, dy) <= self.joystick_radius * 1.5:
                self.joystick_active = True
                self.joystick_finger = finger_id
                self._update_stick(pos)
                handled = True
            
            # Check buttons
            for name, btn in self.buttons.items():
                if btn["rect"].collidepoint(pos):
                    btn["pressed"] = True
                    btn["finger"] = finger_id
                    if name == "zoom_in": self.zoom_in_clicked = True
                    if name == "zoom_out": self.zoom_out_clicked = True
                    if name == "inv": self.inv_clicked = True
                    if name == "menu": self.menu_clicked = True
                    handled = True

            # Check interact
            if self.interact_btn["visible"] and self.interact_btn["rect"].collidepoint(pos):
                self.interact_btn["pressed"] = True
                self.interact_btn["finger"] = finger_id
                self.interact_pressed = True
                handled = True

            # If not UI, it's an action tap, but ONLY if no game UI is open
            if not handled and not ui_is_open:
                self.action_finger = finger_id
                self.action_tap = pos
                self.action_hold = pos
                handled = True

        elif is_motion:
            if self.joystick_active and finger_id == self.joystick_finger:
                self._update_stick(pos)
                handled = True
            if finger_id == self.action_finger:
                self.action_hold = pos
                handled = True

        elif is_up:
            if finger_id == self.joystick_finger:
                self.joystick_active = False
                self.joystick_finger = None
                self.stick_pos = list(self.joystick_base)
                self.left_pressed = False
                self.right_pressed = False
                handled = True
            
            for btn in self.buttons.values():
                if finger_id == btn["finger"]:
                    btn["pressed"] = False
                    btn["finger"] = None
                    handled = True
                    
            if finger_id == self.interact_btn["finger"]:
                self.interact_btn["pressed"] = False
                self.interact_btn["finger"] = None
                handled = True

            if finger_id == self.action_finger:
                self.action_finger = None
                self.action_hold = None
                handled = True

        self._update_states()
        return handled

    def _update_stick(self, pos):
        dx = pos[0] - self.joystick_base[0]
        dy = pos[1] - self.joystick_base[1]
        dist = math.hypot(dx, dy)
        if dist > self.joystick_radius:
            dx = (dx / dist) * self.joystick_radius
            dy = (dy / dist) * self.joystick_radius
        self.stick_pos = [self.joystick_base[0] + dx, self.joystick_base[1] + dy]

    def _update_states(self):
        # Update directional presses based on stick position
        if self.joystick_active:
            dx = self.stick_pos[0] - self.joystick_base[0]
            if dx < -15:
                self.left_pressed = True
                self.right_pressed = False
            elif dx > 15:
                self.right_pressed = True
                self.left_pressed = False
            else:
                self.left_pressed = False
                self.right_pressed = False
        else:
            self.left_pressed = False
            self.right_pressed = False

        self.jump_pressed = self.buttons["jump"]["pressed"]

    def set_interact_visible(self, visible: bool):
        self.interact_btn["visible"] = visible
        if not visible:
            self.interact_btn["pressed"] = False

    def draw(self, surface: pygame.Surface):
        if not self.active: return

        # Draw Joystick
        pygame.draw.circle(surface, (100, 100, 100, 128), self.joystick_base, self.joystick_radius, 2)
        pygame.draw.circle(surface, (200, 200, 200, 180), (int(self.stick_pos[0]), int(self.stick_pos[1])), self.stick_radius)

        # Draw Buttons
        font = pygame.font.SysFont(None, 36)
        for name, btn in self.buttons.items():
            color = (150, 255, 150, 180) if btn["pressed"] else (btn["color"][0], btn["color"][1], btn["color"][2], 128)
            rect = btn["rect"]
            pygame.draw.rect(surface, color, rect, border_radius=15)
            pygame.draw.rect(surface, (255, 255, 255, 200), rect, 2, border_radius=15)
            if "text" in btn:
                txt = font.render(btn["text"], True, (0,0,0))
                surface.blit(txt, txt.get_rect(center=rect.center))

        # Draw Interact Button
        if self.interact_btn["visible"]:
            color = (255, 200, 50, 180) if self.interact_btn["pressed"] else (200, 150, 30, 128)
            rect = self.interact_btn["rect"]
            pygame.draw.rect(surface, color, rect, border_radius=15)
            pygame.draw.rect(surface, (255, 255, 255, 200), rect, 2, border_radius=15)
            # Draw a simple hand/gear icon or text
            font = pygame.font.SysFont(None, 24)
            txt = font.render("USE", True, (0,0,0))
            surface.blit(txt, txt.get_rect(center=rect.center))
