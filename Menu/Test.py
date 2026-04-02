import pygame
import sys

# Initialize Pygame
pygame.init()

# Screen setup
WIDTH, HEIGHT = 600, 400
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Button & Input Example")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
LIGHT_GRAY = (220, 220, 220)
BLUE = (0, 120, 215)
LIGHT_BLUE = (0, 150, 255)

# Fonts
FONT = pygame.font.Font(None, 32)

# Input box setup
input_box = pygame.Rect(50, 50, 200, 32)
input_color_inactive = GRAY
input_color_active = BLUE
input_color = input_color_inactive
active = False
text = ""

# Button setup
button_rect = pygame.Rect(50, 120, 150, 40)
button_color = LIGHT_GRAY
button_text = FONT.render("Click Me", True, BLACK)

# Clock
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Mouse click handling
        if event.type == pygame.MOUSEBUTTONDOWN:
            if input_box.collidepoint(event.pos):
                active = not active
            else:
                active = False
            input_color = input_color_active if active else input_color_inactive

            if button_rect.collidepoint(event.pos):
                print(f"Button clicked! Current input: '{text}'")

        # Keyboard handling
        if event.type == pygame.KEYDOWN and active:
            if event.key == pygame.K_RETURN:
                print(f"Entered text: {text}")
                text = ""
            elif event.key == pygame.K_BACKSPACE:
                text = text[:-1]
            else:
                # Only add printable characters
                if event.unicode.isprintable():
                    text += event.unicode

    # Mouse hover effect for button
    if button_rect.collidepoint(pygame.mouse.get_pos()):
        button_color = LIGHT_BLUE
    else:
        button_color = LIGHT_GRAY

    # Drawing
    screen.fill(WHITE)

    # Draw input box
    pygame.draw.rect(screen, input_color, input_box, border_radius=5)
    txt_surface = FONT.render(text, True, BLACK)
    screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
    input_box.w = max(200, txt_surface.get_width() + 10)

    # Draw button
    pygame.draw.rect(screen, button_color, button_rect, border_radius=5)
    screen.blit(button_text, (button_rect.x + 20, button_rect.y + 8))

    pygame.display.flip()
    clock.tick(30)
