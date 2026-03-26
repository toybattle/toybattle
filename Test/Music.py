import pygame
import sys
import os

def main():
    # Initialize Pygame
    pygame.init()
    pygame.mixer.init()

    # Create a simple window
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Pygame Background Music Example")

    # Path to your music file (MP3, OGG, WAV supported)
    music_file = "assets/sound/bg.mp3"  # Replace with your file path

    # Validate file existence
    if not os.path.isfile(music_file):
        print(f"Error: Music file '{music_file}' not found.")
        pygame.quit()
        sys.exit(1)

    try:
        # Load and play music in a loop (-1 means infinite loop)
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.set_volume(0.5)  # Volume: 0.0 to 1.0
        pygame.mixer.music.play(-1)
    except pygame.error as e:
        print(f"Error loading music: {e}")
        pygame.quit()
        sys.exit(1)

    # Main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:  # Pause
                    pygame.mixer.music.pause()
                elif event.key == pygame.K_r:  # Resume
                    pygame.mixer.music.unpause()
                elif event.key == pygame.K_s:  # Stop
                    pygame.mixer.music.stop()

        screen.fill((30, 30, 30))
        pygame.display.flip()

    # Cleanup
    pygame.mixer.music.stop()
    pygame.quit()

if __name__ == "__main__":
    main()
