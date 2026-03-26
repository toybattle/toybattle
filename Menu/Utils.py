import gc
import pygame
import os

def cleanup(screen, ressources, sound):
    try:
        sound.stop()
    except Exception:
        pass

    for ressource in ressources.keys():
        ressources[ressource] = None

    gc.collect()
    screen.fill((0, 0, 0))
    pygame.display.flip()
    return ressources


def load_path(path, file_name):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    file_path = os.path.join(project_root, path, file_name)
    return file_path