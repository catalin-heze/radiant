import pygame
import sys
import asyncio

# This is still needed for the universal frame rate control
IS_WEB_BUILD = sys.platform in ("emscripten", "wasi")

async def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Minimal Test")
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

        # --- Drawing ---
        screen.fill((0, 0, 100)) # A dark blue background
        pygame.draw.circle(screen, (255, 255, 255), (400, 300), 50) # A white circle

        pygame.display.flip()

        # The universal game loop delay
        if IS_WEB_BUILD:
            await asyncio.sleep(0)
        else:
            clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    asyncio.run(main())