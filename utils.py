
import pygame
import time
import pygame as pg
pg.init()


def resize_image(image, sf):
    "resizes pygame image to set scale factor"
    width = image.get_rect().width
    height = image.get_rect().height

    image = pygame.transform.scale(image, (width*sf, height*sf))

    return image


def get_price(craftList, craft):
    for element in craftList:
        if element[0] == craft:
            return element[1]


class Button():
    def __init__(self, x, y, image_path, hover_path, scale, sound_path=r"data\sounds\button_click.wav"):
        image = pygame.image.load(image_path)

        hover_image = pygame.image.load(hover_path)

        self.image_norm = resize_image(image, scale)
        self.hover_image = resize_image(hover_image, scale)

        self.image = self.image_norm

        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False

        self.click_sound = pygame.mixer.Sound(sound_path)

    def draw(self, surface):
        """Displays button on screen, records if it is clicked"""
        pos = pygame.mouse.get_pos()  # mouse position

        self.image = self.image_norm

        self.clicked = False
        if self.rect.collidepoint(pos):

            self.image = self.hover_image

            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:

                self.clicked = True
                pygame.mixer.Sound.play(self.click_sound)
                time.sleep(0.1)  # small delay so program doesn't feel too fast
        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        surface.blit(self.image, (self.rect.x, self.rect.y))

        return


COLOR_INACTIVE = pg.Color('lightskyblue3')
COLOR_ACTIVE = pg.Color('white')
FONT = pg.font.Font(None, 32)


class InputBox:

    def __init__(self, x, y, w, h, text=''):
        self.rect = pg.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False
        self.enter = False

    def handle_event(self, event):
        final_text = False
        if event.type == pg.MOUSEBUTTONDOWN:
            # If the user clicked on the input_box rect.
            if self.rect.collidepoint(event.pos):
                # Toggle the active variable.
                self.active = not self.active
            else:
                self.active = False
            # Change the current color of the input box.
            self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE
        if event.type == pg.KEYDOWN:
            if self.active:
                if event.key == pg.K_RETURN:
                    final_text = self.text
                    self.text = ''
                elif event.key == pg.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Re-render the text.
                self.txt_surface = FONT.render(self.text, True, self.color)

        return final_text

    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self, screen):
        # Blit the text.
        screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pg.draw.rect(screen, self.color, self.rect, 2)
