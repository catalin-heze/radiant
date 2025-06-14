import pygame
import random
import sys
import os
import asyncio
IS_WEB_BUILD = sys.platform in ("emscripten", "wasi")

# --- Control Center ---
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 800

# --- General ---
SIZE = 12
Q = 4
SPACE = 2 * SIZE
DIVIDER = SIZE / 3
INTERNAL_SPACE = SIZE + DIVIDER
NUM_COLS = Q
NUM_ROWS =  Q // 2 + Q // Q  # This evaluates to 3, which works for all levels
PLAYER_LIVES = 2
FONT_PATH = "ZenDots-Regular.ttf"
FONT_PATH_2 = "Exo2-VariableFont_wght.ttf"
ALPHA = int(255 * 0.26)

# COLORS
COLOR_1 = '#000000'
COLOR_2 = '#FFFFFF'
COLOR_3 = '#B9FA00'
COLOR_4 = '#FF0200'
COLOR_5 = 'cyan'

# --- Central Font Control Panel ---
FONT_CONFIG = {
    # 'key_name': ('font_file_variable', size, line_spacing_multiplier),
    'title':        (FONT_PATH, 28, 1.2),
    'score':        (FONT_PATH, 20, 1.0),
    'level_start':  (FONT_PATH, 24, 1.0),
    'screen_title': (FONT_PATH, 60, 1.0),
    'story':        (FONT_PATH_2, 24, 1.4),
    'prompt':       (FONT_PATH, 18, 1.0)
}
# --- font spacing settings ---
FONT_SPACING_MAP = {}

# SHIP
SHIP_MOVE_SPEED = 5
SHIP_PROJECTILE_SPEED = 10
SHIP_PROJECTILE_COLOR = COLOR_3

# DRONE
DRONE_WIDTH = 5 * SIZE + 4 * DIVIDER
DRONE_HEIGHT = 3 * SIZE + 2 * DIVIDER
DRONE_FIRE_CHANCE = 0.01
DRONE_PROJECTILE_SPEED = 4
DRONE_PROJECTILE_COLOR = COLOR_5

# BATTLESHIP
BATTLESHIP_PROJECTILE_COLOR = COLOR_4
BATTLESHIP_ACTIVE_SPEED_MULTIPLIER = 1.4
BATTLESHIP_FIRE_CHANCE = 0.025

# FLEET
FLEET_SPACING = SPACE
FLEET_MOVE_SPEED = 1
BATTLESHIP_FLEET_GAP = 2 * SIZE
DEPLOY_SPEED = 10


# --- Scoring System ---
MAX_DISPLAY_SCORE = 9999
DRONE_PART_POINTS = 10
DRONE_DESTROY_BONUS = 50
BATTLESHIP_PART_POINTS = 25
BATTLESHIP_DESTROY_BONUS = 500


# --- Font & Text Management ---
def load_fonts():
    """
    Reads FONT_CONFIG, loads pygame Font objects, and populates the
    global FONT_SPACING_MAP to link fonts to their line spacing settings.
    """
    # Clear the map to handle game restarts cleanly
    FONT_SPACING_MAP.clear()
    loaded_fonts = {}
    try:
        for key, (font_path, font_size, line_spacing) in FONT_CONFIG.items():
            font = pygame.font.Font(font_path, font_size)
            loaded_fonts[key] = font
            #  font's unique ID to store its spacing in the global map
            FONT_SPACING_MAP[id(font)] = line_spacing
        return loaded_fonts

    except pygame.error as e:
        print(f"Warning: Font loading error - {e}. Using default 'monospace' fonts for all text.")
        fallback_fonts = {}
        for key, (font_path, font_size, line_spacing) in FONT_CONFIG.items():
            font = pygame.font.SysFont("monospace", font_size)
            fallback_fonts[key] = font
            # fallback fonts
            FONT_SPACING_MAP[id(font)] = line_spacing
        return fallback_fonts


STORY_TEXTS ={'intro':
"""Stardate 61524.3

For centuries, the Federation of Planets
has enjoyed an era of unprecedented 
peace and exploration.

A decade ago, from the silent, uncharted depths 
of the vast  universe, a new terror has emerged.

A single, desperate transmission 
has reached the Federation from  a civilisation 
on the brink of extinction:

01010011 01100001 01110110 01100101
00100000 01101111 01110101 01110010 
00100000 01110011 01101111 01110101 
01101100 01110011
the Swarm are here!

- - -

Their message was a plea for help, 
a warning, and a data-packet containing 
the Swarm's terrifying deeds.

A relentless, biomechanical hive that 
consumes entire star systems, leaving 
only a silent void in its path.

- - -

In a combined effort of the Federation's 
greatest minds, a single countermeasure 
was built: the XA-101-02-934,
codename: The Radiant.

An experimental prototype, smaller,  faster, and 
more powerful than any ship in the history of 
the Federation, equipped with an untested
 radius energy core that makes it uniquely  
capable of facing the enemy head-on.

- - -

You are the pilot of the Radiant. 
You are their only hope.


I
I
I

(prepare)
"""
}


SCREEN_TEXT = {

    'level_1_complete': {
        'title': "Sector 1 Cleared",
        'story': [
        "You’ve broken through the",
        "outer edges of their defences.",
        "but the Swarm have upgraded.."
        ],
        'prompt': "Press [SPACE] or [ENTER] to continue"
    },
    'level_2_complete': {
        'title': "Sector 2 Cleared",
        'story': [
            "Their formations are becoming more complex.",
            "They are adapting. Maintain vigilance."
        ],
        'prompt': "Press [SPACE] or [ENTER] to continue"
    },
    'level_3_complete': {
        'title': "Sector 3 Cleared",
        'story': [
             "Their defences are shattered.",
        "Prepare to engage the Hive Nexus."
        ],
        'prompt': "Press [SPACE] or [ENTER] to continue"
    },
    'win': {
        'title': "VICTORY!",
        'story': [
        "The Hive Nexus is destroyed.",
        "",
        "The Radiant has triumphed."
        ],
        'prompt': "Press [ENTER] to play again or [ESC] to quit"
    },
    'game_over': {
        'title':
    """//ship_status:
[core_breached, imminent_failure]
atemporal_field_generated()
‘loading… success’
causality_loop(engaged)""",

        'story':
        """
    The Radiant core has been breached and the implosion has 
    caused an atemporal bubble to form around the ship.
    You can now go back in time and face them once again.
    """,

        'prompt': "Press [ENTER] for time travel or [ESC] to quit"
    }
}


def draw_text(screen, text, font, color, position, anchor="center"):
    # --- NEW: Check if the input text is a list or a string ---
    if isinstance(text, list):
        lines = text
    else:
        lines = text.splitlines()
    # --- End of change ---

    # Look up the font's unique ID in our global map to get its spacing
    line_spacing_multiplier = FONT_SPACING_MAP.get(id(font), 1.0)
    line_height = font.get_linesize() * line_spacing_multiplier

    # Calculate the total height for vertical centering if needed
    total_height = len(lines) * line_height
    start_y = position[1]

    # Adjust start_y based on the anchor
    if 'center' in anchor:
        start_y -= total_height / 2
    elif 'bottom' in anchor:
        start_y -= total_height

    for i, line in enumerate(lines):
        # NEW: Added .strip() to remove unwanted leading/trailing whitespace
        clean_line = line.strip()
        if not clean_line:  # Don't render empty lines, just advance the space
            continue

        text_surface = font.render(clean_line, True, color)
        text_rect = text_surface.get_rect()

        # We handle the y-positioning manually, but respect the x-anchor
        line_y_position = start_y + (i * line_height) + (line_height / 2)

        # Use a temporary anchor for each line, preserving the horizontal component
        line_anchor = anchor
        if 'top' in line_anchor: line_anchor = line_anchor.replace('top', 'mid')
        if 'bottom' in line_anchor: line_anchor = line_anchor.replace('bottom', 'mid')

        setattr(text_rect, line_anchor, (position[0], line_y_position))
        screen.blit(text_surface, text_rect)


async def run_scrolling_text_animation(screen, clock, fonts, text_lines, scroll_speed=1, player_info=None):
    """
    Displays a block of text that scrolls up the screen.
    Waits for a key press to end.
    Optionally displays player lives and score at the bottom.
    """
    line_height = fonts['story'].get_height() * 1.6
    total_height = int(len(text_lines) * line_height)
    text_surface = pygame.Surface((CANVAS_WIDTH, total_height), pygame.SRCALPHA)

    for i, line in enumerate(text_lines):
        text_render = fonts['level_start'].render(line, 1, COLOR_2)
        text_rect = text_render.get_rect(center=(CANVAS_WIDTH / 2, i * line_height + line_height / 2))
        text_surface.blit(text_render, text_rect)

    surface_y = CANVAS_HEIGHT
    scrolling = True
    while scrolling:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                scrolling = False

        surface_y -= scroll_speed
        if surface_y < -total_height:
            scrolling = False

        screen.fill(COLOR_1)
        screen.blit(text_surface, (0, surface_y))

        if player_info:

            draw_lives(screen, player_info['lives'])
            draw_score(screen, fonts['score'], player_info['score'], player_info['total_points'])

        pygame.display.flip()

        # universal frame rate control
        if IS_WEB_BUILD:
            await asyncio.sleep(0)
        else:
            clock.tick(30)

    if IS_WEB_BUILD:
        await asyncio.sleep(0.5)
    else:
        pygame.time.wait(500)


async def show_level_complete_screen(screen, clock, fonts, level_index, lives, score, total_points):
    key = f'level_{level_index}_complete'
    text_content = SCREEN_TEXT.get(key, {
        'title': f"Level {level_index} Complete",
        'story': [],
        'prompt': "Press [SPACE] or [ENTER] to continue"
    })

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    running = False # Exit the loop to return from the function

        screen.fill(COLOR_1)
        draw_text(screen, text_content['title'], fonts['title'], COLOR_4, (CANVAS_WIDTH / 2, 96))
        story_y_start = 350
        for i, line in enumerate(text_content['story']):
            draw_text(screen, line, fonts['story'], COLOR_2, (CANVAS_WIDTH / 2, story_y_start + i * 40))
        draw_text(screen, text_content['prompt'], fonts['prompt'], COLOR_3, (CANVAS_WIDTH / 2, CANVAS_HEIGHT - SIZE * 5))
        draw_lives(screen, lives)
        draw_score(screen, fonts['score'], score, total_points)

        pygame.display.flip()

        #universal frame rate control
        if IS_WEB_BUILD:
            await asyncio.sleep(0)
        else:
            clock.tick(60)


async def show_outro_screen(screen, clock, fonts, game_state, score, total_points):
    text_content = SCREEN_TEXT[game_state]
    final_display_score = int((score / total_points) * MAX_DISPLAY_SCORE) if total_points > 0 else 0
    final_display_score = min(final_display_score, MAX_DISPLAY_SCORE)
    score_text = f"Final Score: {final_display_score:04d}"

    # --- Variables for name entry ---
    player_name = ""
    cursor_visible = True
    last_cursor_toggle = pygame.time.get_ticks()

    # The main loop for the single, unified screen
    while True:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                # Pressing ESC always quits
                if event.key == pygame.K_ESCAPE:
                    return False  # Quit

                # Pressing RETURN confirms the name and restarts
                if event.key == pygame.K_RETURN:
                    # Use a default name if the player enters nothing
                    final_name = player_name if player_name else "USER"
                    print(f"Player: {final_name}, Score: {final_display_score}")
                    return True  # Restart

                # Handle name typing
                if event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]
                elif len(player_name) < 4 and event.unicode.isalnum():
                    player_name += event.unicode.upper()

        # --- Unified Drawing Logic ---
        screen.fill(COLOR_1)

        # 1. Draw Title at the top
        title_color = COLOR_3 if game_state == "win" else "red"
        draw_text(screen, text_content['title'], fonts['title'], title_color, (CANVAS_WIDTH / 2, CANVAS_HEIGHT * 0.2))

        # 2. Draw Final Score
        draw_text(screen, score_text, fonts['level_start'], COLOR_2, (CANVAS_WIDTH / 2, CANVAS_HEIGHT * 0.65 ))

        # 3. *** Draw the Story Text ***
        draw_text(screen, text_content['story'], fonts['story'], COLOR_2, (CANVAS_WIDTH / 2, CANVAS_HEIGHT * 0.45))

        # 4. Draw Name Entry Prompt
        draw_text(screen, "Enter Your Name:", fonts['story'], COLOR_2, (CANVAS_WIDTH / 2, CANVAS_HEIGHT * 0.71 ))

        # 4.1. Create and Draw the "_ _ _ _" input field
        display_chars = list(player_name)
        while len(display_chars) < 4:
            display_chars.append('_')
        name_display_text = " ".join(display_chars)
        draw_text(screen, name_display_text, fonts['level_start'], COLOR_2, (CANVAS_WIDTH / 2, CANVAS_HEIGHT * 0.75))

        # 5. Draw the final instructions at the bottom
        draw_text(screen, text_content['prompt'], fonts['prompt'], COLOR_3, (CANVAS_WIDTH / 2, CANVAS_HEIGHT - 6 * SIZE))

        # 6. Blinking cursor logic
        now = pygame.time.get_ticks()
        if now - last_cursor_toggle > 1000:  # Toggle every 500ms
            cursor_visible = not cursor_visible
            last_cursor_toggle = now

        if cursor_visible:
            # Calculate where the cursor should be
            base_text_width, _ = fonts['level_start'].size(name_display_text)
            char_widths = [fonts['level_start'].size(c)[0] for c in display_chars]

            # Position cursor after the last typed character
            cursor_pos_x_offset = sum(char_widths[:len(player_name)]) + (
                        fonts['level_start'].size(" ")[0] * len(player_name))

            # Center the whole text block first, then add the offset
            start_x = (CANVAS_WIDTH / 2) - (base_text_width / 2)
            cursor_x = start_x + cursor_pos_x_offset
            cursor_y = CANVAS_HEIGHT * 0.75

            cursor_rect = pygame.Rect(cursor_x - 2, cursor_y - 12, 4, 24)
            pygame.draw.rect(screen, COLOR_3, cursor_rect)

        pygame.display.flip()
        if IS_WEB_BUILD:
            await asyncio.sleep(0)
        else:
            clock.tick(60)

async def show_cover_screen(screen, clock, cover_image, duration_seconds):
    """
    Displays a cover image for a set duration or until a key is pressed.

    Args:
        screen: The main pygame screen surface.
        clock: The pygame Clock object.
        cover_image: The loaded and scaled pygame surface for the cover image.
        duration_seconds: The maximum time in seconds to display the image.
    """
    start_time = pygame.time.get_ticks()
    duration_ms = duration_seconds * 1000

    running = True
    while running:
        # Check for events
        for event in pygame.event.get():
            # Allow the user to quit the game at any time
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            # Check if the required keys are pressed to skip the cover
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    running = False # Exit the loop

        # Check if the timer has run out
        if pygame.time.get_ticks() - start_time >= duration_ms:
            running = False # Exit the loop

        # Drawing
        screen.blit(cover_image, (0, 0))
        pygame.display.flip()
        if IS_WEB_BUILD:
            await asyncio.sleep(0)
        else:
            clock.tick(60)


# --- Drone Shape Definitions ---
DRONE_SHAPES = {
    'one': [
        {'offset': (0, 0), 'wing': 'left'}, {'offset': (0, 1), 'wing': 'left'}, {'offset': (0, 2), 'wing': 'left'},
        {'offset': (2, 1), 'wing': 'core'},
        {'offset': (4, 0), 'wing': 'right'}, {'offset': (4, 1), 'wing': 'right'}, {'offset': (4, 2), 'wing': 'right'}

    ],
    'two': [
        {'offset': (0, 0), 'wing': 'left'}, {'offset': (0, 1), 'wing': 'left'}, {'offset': (1, 2), 'wing': 'left'},
        {'offset': (2, 0), 'wing': 'core'},
        {'offset': (3, 2), 'wing': 'right'},
        {'offset': (4, 0), 'wing': 'right'}, {'offset': (4, 1), 'wing': 'right'}
    ],
    'three': [
        {'offset': (0, 0), 'wing': 'left'}, {'offset': (0, 1), 'wing': 'left'}, {'offset': (0, 2), 'wing': 'left'},
        {'offset': (1, 2), 'wing': 'left'},
        {'offset': (2, 0), 'wing': 'core'},
        {'offset': (2, 2), 'wing': 'body'},
        {'offset': (3, 2), 'wing': 'right'},
        {'offset': (4, 0), 'wing': 'right'}, {'offset': (4, 1), 'wing': 'right'}, {'offset': (4, 2), 'wing': 'right'}
    ]
}


# --- Level 4 Fleet Layout ---
level_4_fleet_layout = {
    1: ['three', 'three', 'three', 'three'],
    2: ['two', 'two', 'two', 'two'],
    3: ['one', 'one', 'one', 'one']

}


# --- Level 4 Boss Shape Definition ---
level4_boss_shape = [
    # Body - Right wing
    (8,5), (9,5), (10,5), (11,5), (12,5), (13,5), (14,5),
    (8,6), (9,6), (10,6), (11,6), (12,6), (13,6), (14,6),
    (8,7), (9,7), (10,7), (11,7), (12,7),         (14,7),

    (8,8),         (10,8),        (12,8),         (14,8),
    (8,9),


    # Body - Left wing
    (0,5), (1,5), (2,5), (3,5), (4,5), (5,5), (6,5),
    (0,6), (1,6), (2,6), (3,6), (4,6), (5,6), (6,6),
    (0,7),        (2,7), (3,7), (4,7), (5,7), (6,7),
    (0,8),        (2,8),        (4,8),        (6,8),
                                              (6,9),

    # middle
    (7, 5),(7, 6),(7, 7),(7, 8),(7, 9),(7, 10),
    # battleship

    (5, 1), (5, 2), (5, 3),
    (6, 2), (6, 3),
             (7, 2), (7, 3),
    (8, 2), (8, 3),
    (9, 1), (9, 2), (9, 3),

    #core
    (7, 1)
]


# --- Level Configurations ---
LEVEL_CONFIGS = [
    # {
    #     'level_number': 4,
    #     'num_rows': 3,
    #     'fleet_move_speed': FLEET_MOVE_SPEED,
    #     'fleet_layout': level_4_fleet_layout,
    #     'battleship_shape_offsets': level4_boss_shape,
    #     'battleship_core_offset': (7, 1)
    # },
    {
        'level_number': 1,
        'num_rows': NUM_ROWS,
        'fleet_move_speed': FLEET_MOVE_SPEED,
        'drone_shape_offsets': DRONE_SHAPES['one']
    },
    {
        'level_number': 2,
        'num_rows': NUM_ROWS,
        'fleet_move_speed': FLEET_MOVE_SPEED * 1.5,
        'drone_shape_offsets': DRONE_SHAPES['two']
    },
    {
        'level_number': 3,
        'num_rows': NUM_ROWS,
        'fleet_move_speed': FLEET_MOVE_SPEED * 2.0,
        'drone_shape_offsets': DRONE_SHAPES['three'],
        'battleship_shape_offsets': [
            (0, 1), (0, 2), (0, 3),
            (1, 2), (1, 3),
            (2, 1), (2, 2), (2, 3),
            (3, 2), (3, 3),
            (4, 1), (4, 2), (4, 3)
        ],
        'battleship_core_offset': (2, 1)
    },
    {
        'level_number': 4,
        'num_rows': 3,
        'fleet_move_speed': FLEET_MOVE_SPEED,
        'fleet_layout': level_4_fleet_layout,
        'battleship_shape_offsets': level4_boss_shape,
        'battleship_core_offset': (7, 1)
    }
]


# --- Drawing Functions ---
def draw_square(screen, x, y, color):
    rect = pygame.Rect(x, y, SIZE, SIZE)
    pygame.draw.rect(screen, color, rect)


def draw_ship(screen, x, y):
    color = COLOR_2
    ship_shape = [(0, 2), (0, 3), (2, 0), (2, 1), (2, 2), (2, 3), (4, 2), (4, 3)]
    for part in ship_shape:
        draw_square(screen, x + part[0] * SIZE, y + part[1] * SIZE, color)


def _draw_life_ship(screen, x, y):
    color = COLOR_2
    scaled_size = SIZE / 2
    ship_shape = [(0, 2), (0, 3), (2, 0), (2, 1), (2, 2), (2, 3), (4, 2), (4, 3)]
    for part in ship_shape:
        rect = pygame.Rect(x + part[0] * scaled_size, y + part[1] * scaled_size, scaled_size, scaled_size)
        pygame.draw.rect(screen, color, rect)


def draw_lives(screen, lives):
    if lives <= 0: return
    life_ship_height = 4 * (SIZE / 2)
    life_ship_width = 5 * (SIZE / 2)
    base_x = SIZE
    base_y = CANVAS_HEIGHT - SIZE - life_ship_height
    for i in range(lives):
        _draw_life_ship(screen, base_x + i * (life_ship_width + SIZE), base_y)


def draw_score(screen, score_font, raw_score, total_game_points):
    display_score = int((raw_score / total_game_points) * MAX_DISPLAY_SCORE) if total_game_points > 0 else 0
    display_score = min(display_score, MAX_DISPLAY_SCORE)
    score_text = f"{display_score:04d}"
    score_label = score_font.render(score_text, 1, COLOR_2)
    score_rect = score_label.get_rect(bottomright=(CANVAS_WIDTH - SIZE, CANVAS_HEIGHT - SIZE))
    screen.blit(score_label, score_rect)


def draw_entity_part(screen, base_x, base_y, part_data, is_level_4_boss=False):
    if is_level_4_boss:
        offset_to_use = part_data['visual_offset']
    else:
        offset_to_use = part_data['offset']

    part_x = base_x + offset_to_use[0] * INTERNAL_SPACE
    part_y = base_y + offset_to_use[1] * INTERNAL_SPACE

    if part_data['status'] == 'alive':
        rect = pygame.Rect(part_x, part_y, SIZE, SIZE)
        pygame.draw.rect(screen, COLOR_2, rect)
    elif part_data['status'] == 'destroyed' and not is_level_4_boss:
        s = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
        s.fill((255, 255, 255, ALPHA))
        screen.blit(s, (part_x, part_y))


def draw_drone(screen, drone_data):
    drone_base_x = drone_data['x']
    drone_base_y = drone_data['y']
    for part_data in drone_data['parts']:
        draw_entity_part(screen, drone_base_x, drone_base_y, part_data)


def draw_battleship(screen, battleship_data, is_level_4_boss=False):
    if battleship_data['status'] == 'destroyed': return
    base_x = battleship_data['x']
    base_y = battleship_data['y']
    for part_data in battleship_data['parts']:
        draw_entity_part(screen, base_x, base_y, part_data, is_level_4_boss)


def draw_fleet(screen, fleet):
    for drone_data in fleet:
        if drone_data['status'] == 'alive':
            draw_drone(screen, drone_data)



# --- State Creation Functions ---
def create_fleet(level_config):
    fleet_ships = []
    num_rows = level_config.get('num_rows', 0)
    fleet_layout = level_config.get('fleet_layout')

    # This is a helper function we'll define inside create_fleet
    def is_core_protected(parts):
        core_part = next((p for p in parts if p.get('wing') == 'core'), None)
        if not core_part:
            return False
        core_x, core_y = core_part['offset']
        # Check if any 'body' part is directly in front of (same x, greater y) the core
        return any(p['wing'] == 'body' and p['offset'][0] == core_x and p['offset'][1] > core_y for p in parts)

    if num_rows == 0 and not fleet_layout:
        return fleet_ships

    create_drone = lambda row, col, parts: {
        'row': row, 'col': col, 'status': 'alive', 'parts': parts,
        'x': 0, 'y': 0,
        'hit_count': 0,
        'hits_on_left_wing': 0,
        'hits_on_right_wing': 0,
        'is_core_protected': is_core_protected(parts)
    }

    if fleet_layout:
        for row_num, drone_types_in_row in fleet_layout.items():
            for col_num, drone_type_key in enumerate(drone_types_in_row):
                if drone_type_key not in DRONE_SHAPES:
                    print(f"Warning: Drone type '{drone_type_key}' not found in DRONE_SHAPES. Skipping.")
                    continue

                new_drone_parts = [{'offset': d['offset'], 'wing': d['wing'], 'status': 'alive'} for d in DRONE_SHAPES[drone_type_key]]
                fleet_ships.append(create_drone(row_num - 1, col_num, new_drone_parts))
        return fleet_ships

    drone_shape_offsets = level_config.get('drone_shape_offsets')
    if drone_shape_offsets:
        for row in range(num_rows):
            for col in range(NUM_COLS):
                new_drone_parts = [{'offset': d['offset'], 'wing': d['wing'], 'status': 'alive'} for d in drone_shape_offsets]
                fleet_ships.append(create_drone(row, col, new_drone_parts))

    return fleet_ships


def create_battleship(level_config):
    parts = []
    default_shape = [(0, 1), (0, 2), (0, 3), (1, 3), (2, 1), (2, 2), (2, 3), (3, 3), (4, 1), (4, 2), (4, 3)]
    shape_offsets = level_config.get('battleship_shape_offsets', default_shape)
    core_offset = level_config.get('battleship_core_offset', (2, 1))
    is_level_4_boss = level_config.get('level_number') == 4

    # This check is to prevent crashing on levels without a defined battleship
    if not shape_offsets:
        return {'status': 'destroyed', 'parts': [], 'width': 0, 'height': 0}

    for offset in shape_offsets:
        is_core = (offset == core_offset)
        part_data = {'offset': offset, 'is_core': is_core, 'status': 'alive'}
        if is_level_4_boss:
            part_data['visual_offset'] = list(offset)
            part_data['target_offset'] = list(offset)
        parts.append(part_data)

    if parts and not any(p['is_core'] for p in parts):
        print(f"Warning: No core for battleship in level {level_config['level_number']}. Assigning first part as core.")
        parts[0]['is_core'] = True

    max_x = max(p['offset'][0] for p in parts) if parts else 0
    max_y = max(p['offset'][1] for p in parts) if parts else 0

    battleship = {
        'status': 'passive', 'x': 0, 'y': 0, 'dx': 0,
        'width': (max_x * INTERNAL_SPACE) + SIZE,
        'height': (max_y * INTERNAL_SPACE) + SIZE,
        'parts': parts
    }
    return battleship


def setup_level(level_idx):
    config = LEVEL_CONFIGS[level_idx]
    fleet = create_fleet(config)
    battleship = create_battleship(config)
    initial_fleet_width = NUM_COLS * (DRONE_WIDTH + FLEET_SPACING) - FLEET_SPACING
    battleship['y'] = SIZE
    fleet_state = {
        'x': (CANVAS_WIDTH - initial_fleet_width) / 2,
        'y': battleship['y'] + battleship['height'] + BATTLESHIP_FLEET_GAP,
        'dx': -config.get('fleet_move_speed', FLEET_MOVE_SPEED)
    }
    battleship['x'] = (CANVAS_WIDTH - battleship['width']) / 2
    return fleet, battleship, fleet_state


# --- Logic and Collision Functions ---
def fire_projectile(owner_x, owner_y, owner_width, owner_height, direction, owner_id=None):
    proj_x = owner_x + (owner_width / 2) - (SIZE / 4)
    proj_y = owner_y if direction == 'up' else owner_y + owner_height
    rect = pygame.Rect(proj_x, proj_y, SIZE / 2, SIZE)
    return {'rect': rect, 'direction': direction, 'owner': owner_id}


def calculate_fleet_bounds(fleet):
    alive_drones = [d for d in fleet if d['status'] == 'alive']
    if not alive_drones: return 0, 0
    left_x = min(d['x'] for d in alive_drones)
    right_x = max(d['x'] + DRONE_WIDTH for d in alive_drones)
    return left_x, right_x - left_x


def calculate_drone_score(drone):
    """Calculates the score for a destroyed drone based on how it was destroyed."""
    max_possible_score = len(drone['parts']) * DRONE_PART_POINTS + DRONE_DESTROY_BONUS

    # Rule 1 & 2: Perfect Kill (Core Shot)
    if any(p['wing'] == 'core' and p['status'] == 'destroyed' for p in drone['parts']):
        if not drone['is_core_protected'] and drone['hit_count'] == 1:
            return max_possible_score
        if drone['is_core_protected'] and drone['hit_count'] == 2:
            return max_possible_score

    # Rule 3 & 4: Wing Destruction Kill & Score Degradation
    base_score = sum(DRONE_PART_POINTS for p in drone['parts'] if p['status'] == 'destroyed') + DRONE_DESTROY_BONUS

    efficiency_bonus = 0
    left_wing_destroyed = all(p['status'] == 'destroyed' for p in drone['parts'] if p['wing'] == 'left')
    right_wing_destroyed = all(p['status'] == 'destroyed' for p in drone['parts'] if p['wing'] == 'right')

    if left_wing_destroyed and drone['hits_on_right_wing'] == 0:
        efficiency_bonus = sum(
            DRONE_PART_POINTS for p in drone['parts'] if p['wing'] == 'right' and p['status'] == 'alive') // 2
    elif right_wing_destroyed and drone['hits_on_left_wing'] == 0:
        efficiency_bonus = sum(
            DRONE_PART_POINTS for p in drone['parts'] if p['wing'] == 'left' and p['status'] == 'alive') // 2

    final_score = base_score + efficiency_bonus

    # --- MODIFIED SECTION ---
    left_wing_parts = sum(1 for p in drone['parts'] if p['wing'] == 'left')
    right_wing_parts = sum(1 for p in drone['parts'] if p['wing'] == 'right')

    # Consider only wings that actually exist
    wing_part_counts = [count for count in [left_wing_parts, right_wing_parts] if count > 0]

    # If there are wings, find the smallest wing. Otherwise, default to a high number.
    min_hits_for_wing_kill = min(wing_part_counts) if wing_part_counts else 999
    # --- END MODIFIED SECTION ---

    min_hits_for_wing_kill = min(
        sum(1 for p in drone['parts'] if p['wing'] == 'left'),
        sum(1 for p in drone['parts'] if p['wing'] == 'right')
    )

    min_hits_needed = min_hits_for_wing_kill
    if drone['is_core_protected']:
        min_hits_needed = 2
    else:
        min_hits_needed = 1

    wasted_hits = drone['hit_count'] - min_hits_needed
    penalty = wasted_hits * DRONE_PART_POINTS * 2

    return max(0, final_score - penalty)


def handle_fleet_collisions(projectiles, fleet):
    score_earned = 0
    for proj in projectiles[:]:
        if proj['direction'] != 'up': continue
        hit = False
        for drone in fleet:
            if drone['status'] != 'alive': continue

            if proj['rect'].colliderect(pygame.Rect(drone['x'], drone['y'], DRONE_WIDTH, DRONE_HEIGHT)):
                for part in drone['parts']:
                    if part['status'] == 'alive':
                        part_rect = pygame.Rect(drone['x'] + part['offset'][0] * INTERNAL_SPACE,
                                                drone['y'] + part['offset'][1] * INTERNAL_SPACE, SIZE, SIZE)
                        if proj['rect'].colliderect(part_rect):
                            part['status'] = 'destroyed'
                            projectiles.remove(proj)
                            hit = True

                            drone['hit_count'] += 1
                            if part['wing'] == 'left':
                                drone['hits_on_left_wing'] += 1
                            elif part['wing'] == 'right':
                                drone['hits_on_right_wing'] += 1

                            core_destroyed = (part['wing'] == 'core')
                            left_wing_destroyed = all(
                                p['status'] == 'destroyed' for p in drone['parts'] if p['wing'] == 'left')
                            right_wing_destroyed = all(
                                p['status'] == 'destroyed' for p in drone['parts'] if p['wing'] == 'right')

                            if core_destroyed or left_wing_destroyed or right_wing_destroyed:
                                drone['status'] = 'destroyed'
                                score_earned += calculate_drone_score(drone)
                            else:
                                score_earned += DRONE_PART_POINTS

                            break
            if hit:
                break
    return score_earned


def draw_static_blueprint(screen, boss_x, boss_y, original_shape_offsets, ghost_offset, color_with_alpha):
    """
    Draws a static, non-interactive 'blueprint' of the boss.
    This shape is unchanging and simply moves with the boss's main coordinates.
    """
    # Blueprint's base position is the boss's position plus the desired offset
    blueprint_base_x = boss_x + ghost_offset[0]
    blueprint_base_y = boss_y + ghost_offset[1]

    # To draw with transparency
    part_surface = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
    part_surface.fill(color_with_alpha)

    for part_offset in original_shape_offsets:
        part_x = blueprint_base_x + part_offset[0] * INTERNAL_SPACE
        part_y = blueprint_base_y + part_offset[1] * INTERNAL_SPACE

        # Blit the pre-made transparent surface onto the main screen for each part
        screen.blit(part_surface, (part_x, part_y))


def animate_boss_parts(battleship):
    pixel_speed = FLEET_MOVE_SPEED * 2
    grid_speed = pixel_speed / INTERNAL_SPACE

    for part in battleship['parts']:
        is_moving = abs(part['visual_offset'][0] - part['target_offset'][0]) > 0.01 or \
                    abs(part['visual_offset'][1] - part['target_offset'][1]) > 0.01

        if is_moving:
            target_x, target_y = part['target_offset']
            visual_x, visual_y = part['visual_offset']

            dir_x = target_x - visual_x
            dir_y = target_y - visual_y
            distance = (dir_x ** 2 + dir_y ** 2) ** 0.5

            if distance < grid_speed:
                part['visual_offset'] = list(part['target_offset'])
                part['offset'] = tuple(part['target_offset'])
            else:
                norm_x = dir_x / distance
                norm_y = dir_y / distance
                part['visual_offset'][0] += norm_x * grid_speed
                part['visual_offset'][1] += norm_y * grid_speed


def update_boss_shape(destroyed_part_offset, battleship):
    destroyed_x, destroyed_y = destroyed_part_offset
    left_wing_cols, right_wing_cols, middle_col = range(0, 7), range(8, 15), 7

    # Get all parts in the same row using their target_offset and a tolerance for floats
    row_parts = [p for p in battleship['parts'] if abs(p['target_offset'][1] - destroyed_y) < 0.1]

    # --- Case 1: A part on the LEFT wing was destroyed ---
    if destroyed_x in left_wing_cols:
        # Get remaining parts on the left wing, sorted from center-outwards
        wing_parts = sorted([p for p in row_parts if p['target_offset'][0] in left_wing_cols],
                            key=lambda p: p['target_offset'][0], reverse=True)
        # Re-assign their target positions to collapse the gap
        for i, part in enumerate(wing_parts):
            part['target_offset'] = [float((middle_col - 1) - i), float(destroyed_y)]

    # --- Case 2: A part on the RIGHT wing was destroyed ---
    elif destroyed_x in right_wing_cols:
        # Get remaining parts on the right wing, sorted from center-outwards
        wing_parts = sorted([p for p in row_parts if p['target_offset'][0] in right_wing_cols],
                            key=lambda p: p['target_offset'][0])
        # Re-assign their target positions to collapse the gap
        for i, part in enumerate(wing_parts):
            part['target_offset'] = [float((middle_col + 1) + i), float(destroyed_y)]

    # --- Case 3: A part in the MIDDLE column was destroyed ---
    elif int(destroyed_x) == middle_col:
        left_wing = [p for p in row_parts if p['target_offset'][0] < middle_col]
        right_wing = [p for p in row_parts if p['target_offset'][0] > middle_col]
        if not left_wing and not right_wing: return

        # Decide which wing should move to fill the gap
        move_left = random.choice([True, False]) if len(left_wing) == len(right_wing) else len(left_wing) > len(
            right_wing)

        wing_to_shift = left_wing if move_left else right_wing
        shift_direction = 1 if move_left else -1  # 1 for right, -1 for left

        # Shift all parts in the chosen wing by one unit
        for part in wing_to_shift:
            part['target_offset'][0] += shift_direction


def handle_level4_boss_collisions(projectiles, battleship):
    if battleship['status'] == 'destroyed': return False, 0
    score_earned = 0
    hit_registered = False

    for proj in projectiles[:]:
        if proj['direction'] == 'up':
            for part in battleship['parts'][:]:
                if part['status'] != 'alive': continue
                part_rect = pygame.Rect(battleship['x'] + part['visual_offset'][0] * INTERNAL_SPACE,
                                        battleship['y'] + part['visual_offset'][1] * INTERNAL_SPACE, SIZE, SIZE)

                if proj['rect'].colliderect(part_rect):
                    hit_registered = True
                    score_earned += BATTLESHIP_PART_POINTS

                    if part['is_core']:
                        battleship['status'] = 'destroyed'
                        score_earned += BATTLESHIP_DESTROY_BONUS
                        break

                    projectiles.remove(proj)
                    # Use the part's up-to-date target position instead of its old one
                    part_target_offset = tuple(part['target_offset'])
                    battleship['parts'].remove(part)
                    update_boss_shape(part_target_offset, battleship)
                    break

            if battleship['status'] == 'destroyed': break
    return hit_registered, score_earned


def handle_battleship_collisions(projectiles, battleship):
    if battleship['status'] == 'destroyed': return False, 0
    hit_registered = False
    score_earned = 0
    for proj in projectiles[:]:
        if proj['direction'] == 'up':
            for part in battleship['parts']:
                if part['status'] == 'alive':
                    part_rect = pygame.Rect(battleship['x'] + part['offset'][0] * INTERNAL_SPACE,
                                            battleship['y'] + part['offset'][1] * INTERNAL_SPACE, SIZE, SIZE)
                    if proj['rect'].colliderect(part_rect):
                        part['status'] = 'destroyed'
                        score_earned += BATTLESHIP_PART_POINTS
                        projectiles.remove(proj)
                        hit_registered = True
                        if part['is_core']:
                            battleship['status'] = 'destroyed'
                            score_earned += BATTLESHIP_DESTROY_BONUS
                        break
            if hit_registered: break
    return hit_registered, score_earned


def handle_ship_collision(projectiles, ship_rect):
    for proj in projectiles[:]:
        if proj['direction'] == 'down' and ship_rect.colliderect(proj['rect']):
            projectiles.remove(proj)
            return True
    return False


def handle_projectile_collisions(projectiles):
    player_projs = [p for p in projectiles if p['direction'] == 'up']
    enemy_projs = [p for p in projectiles if p['direction'] == 'down']
    for p_proj in player_projs[:]:
        for e_proj in enemy_projs[:]:
            if p_proj in projectiles and e_proj in projectiles and p_proj['rect'].colliderect(e_proj['rect']):
                projectiles.remove(p_proj)
                projectiles.remove(e_proj)
                break


def update_battleship_status(battleship, fleet, hit_by_projectile, fleet_dx):
    if battleship['status'] == 'passive':
        alive_drones_exist = any(d['status'] == 'alive' for d in fleet)
        if not alive_drones_exist:
            battleship['status'] = 'active'
            battleship['dx'] = FLEET_MOVE_SPEED * BATTLESHIP_ACTIVE_SPEED_MULTIPLIER
        else:
            alive_top_row_count = sum(1 for d in fleet if d['status'] == 'alive' and d['row'] == 0)
            if hit_by_projectile or (alive_top_row_count < NUM_COLS):
                battleship['status'] = 'active'
                battleship['dx'] = fleet_dx * BATTLESHIP_ACTIVE_SPEED_MULTIPLIER


async def _draw_animation_frame(screen, clock, battleship, ship_x, ship_y, drones_to_draw, moving_drone=None, is_level_4=False):
    screen.fill(COLOR_1)
    draw_battleship(screen, battleship, is_level_4)
    draw_ship(screen, ship_x, ship_y)
    for drone in drones_to_draw:
        draw_drone(screen, drone)
    if moving_drone:
        draw_drone(screen, moving_drone)
    pygame.display.flip()

    if IS_WEB_BUILD:
        await asyncio.sleep(0)
    else:
        clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()


async def run_deployment_animation(screen, clock, fleet, battleship, ship_x, ship_y, fleet_state, level_config):
    if not fleet and not battleship.get('parts'):
        await _draw_animation_frame(screen, clock, battleship, ship_x, ship_y, [], None, level_config['level_number'] == 4)
        if IS_WEB_BUILD: await asyncio.sleep(1.5)
        else: pygame.time.wait(1500)
        return

    is_level_4 = level_config['level_number'] == 4
    num_rows_in_level = level_config.get('num_rows', NUM_ROWS)
    deployed_drones = []
    animation_move_speed = DEPLOY_SPEED
    gap_width = DRONE_WIDTH + FLEET_SPACING
    deployment_y_start = fleet_state['y'] + DRONE_HEIGHT + FLEET_SPACING

    final_drone_positions = {}
    for drone in fleet:
        col = drone['col']
        final_x = fleet_state['x'] + col * gap_width - (gap_width / 2) if col < NUM_COLS / 2 else \
            fleet_state['x'] + col * gap_width + (gap_width / 2)
        final_y = deployment_y_start + drone['row'] * (DRONE_HEIGHT + FLEET_SPACING)
        final_drone_positions[(drone['row'], drone['col'])] = (final_x, final_y)

    cols_order = []
    left, right = list(range(NUM_COLS // 2)), list(range(NUM_COLS - 1, (NUM_COLS // 2) - 1, -1))
    for i in range(len(left)):
        cols_order.extend([left[i], right[i]])
    if NUM_COLS % 2 != 0: cols_order.append(NUM_COLS // 2)

    for row in range(num_rows_in_level - 1, -1, -1):
        for col in cols_order:
            drone_to_deploy_list = [d for d in fleet if d['row'] == row and d['col'] == col]
            if not drone_to_deploy_list: continue

            drone_to_deploy = drone_to_deploy_list[0]
            start_pos_y = battleship['y'] + battleship['height'] + SIZE
            center_x = CANVAS_WIDTH / 2 - DRONE_WIDTH / 2
            target_x, target_y = final_drone_positions[(row, col)]
            moving_drone = {'x': center_x, 'y': start_pos_y, 'parts': drone_to_deploy['parts'], 'status': 'alive'}

            while moving_drone['y'] < target_y:
                moving_drone['y'] = min(target_y, moving_drone['y'] + animation_move_speed)
                await _draw_animation_frame(screen, clock, battleship, ship_x, ship_y, deployed_drones, moving_drone, is_level_4)

            move_dir = 1 if target_x > moving_drone['x'] else -1
            while (target_x - moving_drone['x']) * move_dir > 0:
                moving_drone['x'] += animation_move_speed * move_dir
                if (target_x - moving_drone['x']) * move_dir <= 0: moving_drone['x'] = target_x
                await _draw_animation_frame(screen, clock, battleship, ship_x, ship_y, deployed_drones, moving_drone, is_level_4)

            drone_to_deploy['x'], drone_to_deploy['y'] = target_x, target_y
            deployed_drones.append(drone_to_deploy)

    if fleet:
        for i in range(30):
            for drone in fleet:
                drone['x'] += (gap_width / 60) if drone['col'] < NUM_COLS / 2 else -(gap_width / 60)
            await _draw_animation_frame(screen, clock, battleship, ship_x, ship_y, fleet, None, is_level_4=is_level_4)

        fleet_state['x'] = fleet[0]['x'] - fleet[0]['col'] * (DRONE_WIDTH + FLEET_SPACING)
        final_combat_y = battleship['y'] + battleship['height'] + BATTLESHIP_FLEET_GAP
        current_fleet_y = fleet[0]['y']

        while current_fleet_y > final_combat_y:
            y_change = -2
            current_fleet_y += y_change
            for drone in fleet: drone['y'] += y_change
            await _draw_animation_frame(screen, clock, battleship, ship_x, ship_y, fleet, None, is_level_4=is_level_4)

        y_correction = final_combat_y - current_fleet_y
        for drone in fleet: drone['y'] += y_correction
        if fleet:
            fleet_state['y'] = fleet[0]['y'] - fleet[0]['row'] * (DRONE_HEIGHT + FLEET_SPACING)


# --- Main Game ---
async def main():
    pygame.init()
    screen = pygame.display.set_mode((CANVAS_WIDTH, CANVAS_HEIGHT))
    pygame.display.set_caption("RADIANT")
    clock = pygame.time.Clock()
    fonts = load_fonts()

    cover_image_surface = None
    try:
        # Load the image from the file
        loaded_image = pygame.image.load("cover_image.png").convert()
        # Scale it to fit the screen perfectly
        cover_image_surface = pygame.transform.scale(loaded_image, (CANVAS_WIDTH, CANVAS_HEIGHT))
    except pygame.error as e:
        print(f"Warning: Could not load cover_image.png. Skipping cover screen. Error: {e}")

    # 2. Show the cover screen if the image was loaded successfully
    if cover_image_surface:
        # Show for a maximum of 5 seconds or until a key is pressed
        await show_cover_screen(screen, clock, cover_image_surface, 5)

    await run_scrolling_text_animation(screen, clock, fonts, STORY_TEXTS['intro'].splitlines())
    total_game_points = 0
    for config in LEVEL_CONFIGS:
        temp_fleet = create_fleet(config)
        temp_battleship = create_battleship(config)
        for drone in temp_fleet:

            total_game_points += len(drone['parts']) * DRONE_PART_POINTS + DRONE_DESTROY_BONUS
        if temp_battleship and temp_battleship.get('parts'):

            total_game_points += len(temp_battleship['parts']) * BATTLESHIP_PART_POINTS + BATTLESHIP_DESTROY_BONUS

    while True:
        raw_score = 0
        current_level_index = 0
        player_lives = PLAYER_LIVES
        game_state = "intro"  # Start with the intro screen
        projectiles = []

        fleet, battleship, fleet_state = setup_level(current_level_index)
        ship_width, ship_height = 5 * SIZE, 4 * SIZE
        ship_x, ship_y = (CANVAS_WIDTH - ship_width) / 2, CANVAS_HEIGHT - (4 * SIZE) - ship_height

        running = True
        while running:
            # --- State Machine Logic ---
            if game_state == "intro":
                game_state = "playing"
                await run_deployment_animation(screen, clock, fleet, battleship, ship_x, ship_y, fleet_state,
                                         LEVEL_CONFIGS[current_level_index])

            elif game_state == "level_complete":
                # Check if the level we just finished is the last one in our list
                is_last_level = (current_level_index == len(LEVEL_CONFIGS) - 1)

                if is_last_level:
                    # If it's the last level, go directly to the win screen
                    game_state = "win"

                else:
                    # Otherwise, for any other level, show the complete screen
                    await show_level_complete_screen(screen, clock, fonts, current_level_index + 1, player_lives, raw_score, total_game_points)
                    current_level_index += 1
                    # Set up the next level to play
                    fleet, battleship, fleet_state = setup_level(current_level_index)
                    projectiles.clear()
                    ship_x = (CANVAS_WIDTH - ship_width) / 2
                    game_state = "playing"
                    await run_deployment_animation(screen, clock, fleet, battleship, ship_x, ship_y, fleet_state, LEVEL_CONFIGS[current_level_index])

            elif game_state in ["win", "game_over"]:
                if await show_outro_screen(screen, clock, fonts, game_state, raw_score, total_game_points):
                    running = False  # Break from inner loop to restart game
                else:
                    pygame.quit()  # Quit entirely
                    sys.exit()

            elif game_state == "playing":
                # --- Original Game Logic (restored) ---
                current_level_config = LEVEL_CONFIGS[current_level_index]
                is_level_4 = current_level_config['level_number'] == 4

                if is_level_4:
                    animate_boss_parts(battleship)

                player_can_fire = not any(p['direction'] == 'up' for p in projectiles)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    # Using K_UP as per original code
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_UP and player_can_fire:
                        projectiles.append(fire_projectile(ship_x, ship_y, ship_width, ship_height, 'up', 'player'))

                keys = pygame.key.get_pressed()
                ship_x += (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * SHIP_MOVE_SPEED

                if fleet and fleet_state['dx'] != 0:
                    fleet_state['x'] += fleet_state['dx']
                    for drone in fleet:
                        drone['x'] = fleet_state['x'] + drone['col'] * (DRONE_WIDTH + FLEET_SPACING)
                        drone['y'] = fleet_state['y'] + drone['row'] * (DRONE_HEIGHT + FLEET_SPACING)
                    fleet_left_edge, current_fleet_width = calculate_fleet_bounds(fleet)
                    if current_fleet_width > 0 and (
                            fleet_left_edge <= SPACE or (
                            fleet_left_edge + current_fleet_width) >= CANVAS_WIDTH - SPACE):
                        fleet_state['dx'] *= -1

                if is_level_4:
                    battleship_was_hit, score_from_battleship = handle_level4_boss_collisions(projectiles, battleship)
                else:
                    battleship_was_hit, score_from_battleship = handle_battleship_collisions(projectiles, battleship)

                raw_score += score_from_battleship
                raw_score += handle_fleet_collisions(projectiles, fleet)
                update_battleship_status(battleship, fleet, battleship_was_hit, fleet_state['dx'])
                handle_projectile_collisions(projectiles)

                if handle_ship_collision(projectiles, pygame.Rect(ship_x, ship_y, ship_width, ship_height)):
                    player_lives -= 1
                    if player_lives < 0:
                        game_state = "game_over"
                    else:
                        ship_x = (CANVAS_WIDTH - ship_width) / 2
                        projectiles = [p for p in projectiles if p['direction'] == 'up']
                        screen.fill(COLOR_1)
                        draw_fleet(screen, fleet)
                        draw_battleship(screen, battleship, is_level_4)
                        draw_lives(screen, player_lives)
                        draw_score(screen, fonts['score'], raw_score, total_game_points)
                        for proj in projectiles: pygame.draw.rect(screen, SHIP_PROJECTILE_COLOR, proj['rect'])
                        pygame.display.flip()
                        pygame.time.wait(1500)


                fleet_left_edge, current_fleet_width = calculate_fleet_bounds(fleet)
                if battleship['status'] == 'passive' and current_fleet_width > 0:
                    battleship['x'] = fleet_left_edge + (current_fleet_width / 2) - (battleship['width'] / 2)
                else:
                    battleship['x'] += battleship.get('dx', 0)

                for proj in projectiles[:]:
                    proj['rect'].y += -SHIP_PROJECTILE_SPEED if proj['direction'] == 'up' else DRONE_PROJECTILE_SPEED
                    if not (0 < proj['rect'].bottom and proj['rect'].top < CANVAS_HEIGHT):
                        projectiles.remove(proj)

                ship_x = max(SPACE / 2, min(ship_x, CANVAS_WIDTH - ship_width - SPACE / 2))

                alive_drones = [d for d in fleet if d['status'] == 'alive']
                if alive_drones:
                    bottom_drones = {col: max(d['row'] for d in alive_drones if d['col'] == col) for col in
                                     {d['col'] for d in alive_drones}}
                    for drone in alive_drones:
                        if drone['row'] == bottom_drones.get(drone['col']) and random.random() < DRONE_FIRE_CHANCE:
                            if not any(p['owner'] == (drone['row'], drone['col']) for p in projectiles):
                                projectiles.append(
                                    fire_projectile(drone['x'], drone['y'], DRONE_WIDTH, DRONE_HEIGHT, 'down',
                                                    (drone['row'], drone['col'])))

                if battleship['status'] == 'active' and battleship[
                    'status'] != 'destroyed' and random.random() < BATTLESHIP_FIRE_CHANCE:
                    projectiles.append(
                        fire_projectile(battleship['x'], battleship['y'], battleship['width'], battleship['height'],
                                        'down',
                                        'battleship'))

                if battleship['status'] == 'active':
                    if battleship['x'] > CANVAS_WIDTH:
                        battleship['x'] = -battleship['width']
                    elif battleship['x'] + battleship['width'] < 0:
                        battleship['x'] = CANVAS_WIDTH

                all_parts_gone = not any(p['status'] == 'alive' for p in battleship.get('parts', []))
                core_destroyed = battleship['status'] == 'destroyed'
                boss_defeated = all_parts_gone or core_destroyed

                if all(d.get('status', 'destroyed') == 'destroyed' for d in fleet) and boss_defeated:
                    game_state = "level_complete"

                # --- Drawing for "playing" state ---
                screen.fill(COLOR_1)
                draw_fleet(screen, fleet)

                if is_level_4:
                    # Define the offset and color for the blueprint
                    blueprint_offset = (0, 0)
                    # A dim, white blueprint is often effective. (R, G, B, Alpha)
                    blueprint_color = (255, 255, 255, 40)

                    # Call the function to draw the blueprint on every frame
                    draw_static_blueprint(screen, battleship['x'], battleship['y'], level4_boss_shape,
                                          blueprint_offset, blueprint_color)

                draw_battleship(screen, battleship, is_level_4)
                draw_ship(screen, ship_x, ship_y)
                draw_lives(screen, player_lives)
                draw_score(screen, fonts['score'], raw_score, total_game_points)
                for proj in projectiles:
                    color = SHIP_PROJECTILE_COLOR if proj['direction'] == 'up' else (
                        BATTLESHIP_PROJECTILE_COLOR if proj['owner'] == 'battleship' else DRONE_PROJECTILE_COLOR)
                    pygame.draw.rect(screen, color, proj['rect'])

            # This call handles updating the display for all states
            pygame.display.flip()
            if IS_WEB_BUILD:
                await asyncio.sleep(0)
            else:
                clock.tick(60)


if __name__ == '__main__':
    asyncio.run(main())
