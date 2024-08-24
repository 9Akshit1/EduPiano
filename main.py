import pygame
import pygame.gfxdraw
import os
import tkinter as tk
from tkinter import filedialog
import shutil
from thiscode.annotate import runner

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 900
TOTAL_HEIGHT = 1500  # This will be our scrollable height
BACKGROUND_COLOR = (241, 239, 230)  # #F1EFE6
PRIMARY_COLOR = (58, 81, 153)  # #3A5199
SECONDARY_COLOR = (109, 133, 199)  # #6D85C7
ACCENT_COLOR = (255, 107, 107)  # #FF6B6B
TEXT_COLOR = (51, 51, 51)  # #333333

# Fonts
pygame.font.init()
FONT_PATH = "assets/Copernicus.ttf" 
heading_font = pygame.font.Font(FONT_PATH, 36)
subheading_font = pygame.font.Font(FONT_PATH, 24)
body_font = pygame.font.Font(None, 18)  
text_font = pygame.font.Font(None, 20) 
larger_body_font = pygame.font.Font(None, 22)  

# Initialize window
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("EduPo - Piano Fingering Generator & Teacher")

# Create a surface to draw on that's larger than the window
surface = pygame.Surface((WINDOW_WIDTH, TOTAL_HEIGHT))

# Scrolling variables
scroll_y = 0
scroll_speed = 20

# Parameters
parameters = [
    ("hand_size (str: XXS to XXL)", "M"),
    ("filename* (str)", ""),
    ("output_filename (str)", "output.xml"),
    ("total_measures (int)", "100"),
    ("start_measure (int)", "1"),
    ("depth_in_finger_generate (int)", "0"),
    ("dont_write_Rbeam (int: 0 or 1)", "0"),
    ("write_Lbeam (int: 0 or 1)", "1"),
    ("detailed_info_off (bool)", "False"),
    ("visualize_in_musescore (bool)", "False"),
    ("write_below_beam (bool)", "False"),
    ("with_2D_keyboard (bool)", "False"),
    ("speed_of_2D_keyboard (int)", "1.0"),
    ("finger_rotation (bool)", "True"),
    ("sound_off (bool)", "False"),
    ("left_hand_only (bool)", "False"),
    ("right_hand_only (bool)", "False"),
]

# Input fields
input_fields = ['' for _ in parameters]
active_field = None

def draw_rounded_rect(surface, rect, color, corner_radius):
    pygame.gfxdraw.box(surface, rect, color)
    pygame.gfxdraw.filled_circle(surface, rect.left + corner_radius, rect.top + corner_radius, corner_radius, color)
    pygame.gfxdraw.filled_circle(surface, rect.right - corner_radius - 1, rect.top + corner_radius, corner_radius, color)
    pygame.gfxdraw.filled_circle(surface, rect.left + corner_radius, rect.bottom - corner_radius - 1, corner_radius, color)
    pygame.gfxdraw.filled_circle(surface, rect.right - corner_radius - 1, rect.bottom - corner_radius - 1, corner_radius, color)

def draw_text(text, font, color, surface, x, y):
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)

def draw_button(surface, text, x, y, width, height, color, text_color, text_x, text_y):
    button_rect = pygame.Rect(x, y, width, height)
    draw_rounded_rect(surface, button_rect, color, 10)
    draw_text(text, larger_body_font, text_color, surface, text_x, text_y)
    return button_rect

def draw_input_field(surface, text, x, y, width, height, color, text_color, active):
    field_rect = pygame.Rect(x, y, width, height)
    border_color = ACCENT_COLOR if active else SECONDARY_COLOR
    pygame.draw.rect(surface, border_color, field_rect, 2, border_radius=5)
    draw_text(text, body_font, text_color, surface, x + 5, y + 5)
    return field_rect

def upload_file():
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    file_path = filedialog.askopenfilename(filetypes=[("XML files", "*.xml")])
    if file_path:
        if not os.path.exists('scores'):
            os.makedirs('scores')
        filename = os.path.basename(file_path)
        destination = os.path.join('scores', filename)
        shutil.copy2(file_path, destination)
        input_fields[1] = filename
        return f"File uploaded: {filename}"
    return "No file selected"

def draw_hand_size_field(surface, text, x, y, width, height, color, text_color, active):
    draw_text("hand_size (str: XXS to XXL)", body_font, TEXT_COLOR, surface, x, y - 20)
    field_rect = draw_input_field(surface, text, x, y, width, height, color, text_color, active)
    draw_text("Default: M", body_font, SECONDARY_COLOR, surface, x, y + 30)
    return field_rect

# Main game loop
clock = pygame.time.Clock()
running = True
message = ""
result = ""
show_result = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Scroll up
                scroll_y = max(scroll_y - scroll_speed, 0)
            elif event.button == 5:  # Scroll down
                scroll_y = min(scroll_y + scroll_speed, TOTAL_HEIGHT - WINDOW_HEIGHT)
            elif upload_button.collidepoint(event.pos[0], event.pos[1] + scroll_y):
                message = upload_file()
            elif run_button.collidepoint(event.pos[0], event.pos[1] + scroll_y):
                params = {param: value for (param, _), value in zip(parameters, input_fields)}
                params_list = list(params.values())
                # Move the first element (hand_size) to the end. i did this bcuz in runner(), i made the hand_size the last value
                hand_size_element = params_list.pop(0)
                params_list.append(hand_size_element)
                result_fn, with_2D, start_measure, xmlfn, rh, lh, sound_off, speed_2D, f_rot = runner(params_list)
                show_result = True
            for i, field in enumerate(input_field_rects):
                if field.collidepoint(event.pos[0], event.pos[1] + scroll_y):
                    active_field = i
                    break
            else:
                active_field = None
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if active_field is not None:
                if event.key == pygame.K_RETURN:
                    active_field = None
                elif event.key == pygame.K_BACKSPACE:
                    input_fields[active_field] = input_fields[active_field][:-1]
                else:
                    input_fields[active_field] += event.unicode

    surface.fill(BACKGROUND_COLOR)

    # Draw header
    draw_text("EduPiano: ", heading_font, PRIMARY_COLOR, surface, 50, 100)
    draw_text("Piano Fingering Generator & Teacher", subheading_font, SECONDARY_COLOR, surface, 260, 110)

    # Draw placeholder section
    placeholder_rect = pygame.Rect(50, 150, WINDOW_WIDTH - 100, 210)
    draw_rounded_rect(surface, placeholder_rect, SECONDARY_COLOR, 10)
    draw_text("BEFORE RUNNING, TAKE OUT AN .XML FILE OUT OF THE SCORES FOLDER FOR UPLOADING. ALSO, FOLLOW THE DEMO VIDEO AND INSTRUCTION PROVIDED.", text_font, (255, 255, 255), surface, 60, 160)
    draw_text("The project generates the 'best' fingering for a piece based on the user's hand size and other parameters, annotating them directly onto the sheet music. It then uses a ", text_font, (255, 255, 255), surface, 60, 185)
    draw_text("2D keyboard in Pygame to show the fingering and hand positions. Finally, after setting up the projection light on your piano/keyboard, it teaches the user step by step ", text_font, (255, 255, 255), surface, 60, 210)
    draw_text("what notes to play and which fingers to use. While it may not be 100% accurate, it provides a solid foundation for users to build on.", text_font, (255, 255, 255), surface, 60, 235)
    draw_text("This project is quite complex because it has to read/translate all the notes of the sheet music files. Then, it has to generate the most common fingering by trying out ", text_font, (255, 255, 255), surface, 60, 260)
    draw_text("all combination, yet time-efficiently. I would've used ML if I could, but there is no data on this at all. Furthurmore, but playing chords is actually very complex.", text_font, (255, 255, 255), surface, 60, 285)
    draw_text("I had to learn Fast Fourier Transform of sounds (& sine waves) to understand how our ear hears chords. I tried many methods to apply it, and finally it worked.", text_font, (255, 255, 255), surface, 60, 310)
    draw_text("Overall, I believe this project is an essential tool for musicians (pianists like myself) in the future. I hope it reaches out to others by winning GIA Hacks 2.", text_font, (255, 255, 255), surface, 60, 335)

    # Draw parameter sections
    param_section = pygame.Rect(50, 400, WINDOW_WIDTH - 100, 800)
    draw_rounded_rect(surface, param_section, (255, 255, 255), 10)
    draw_text("Parameters", subheading_font, PRIMARY_COLOR, surface, 60, 410)

    # Draw upload button and message
    upload_button = draw_button(surface, "Upload File (.xml)", 60, 450, 150, 40, PRIMARY_COLOR, (255, 255, 255), 72, 462)
    draw_text(message, body_font, TEXT_COLOR, surface, 220, 460)

    # Draw hand_size input field
    hand_size_rect = draw_hand_size_field(surface, input_fields[0], WINDOW_WIDTH - 300, 450, 230, 30, (255, 255, 255), TEXT_COLOR, 0 == active_field)
    input_field_rects = [hand_size_rect]

    # Draw parameter input fields in a grid
    for i, (param, default) in enumerate(parameters[1:], start=1):  # Start from index 1
        col = (i - 1) % 4  # Subtract 1 from i
        row = (i - 1) // 4  # Subtract 1 from i
        x = 60 + col * 280
        y = 505 + row * 75
        draw_text(param, body_font, TEXT_COLOR, surface, x, y)
        field_rect = draw_input_field(surface, input_fields[i], x, y + 20, 230, 30, (255, 255, 255), TEXT_COLOR, i == active_field)
        input_field_rects.append(field_rect)
        if i == 1:  # Add red asterisk for filename (now at index 1)
            draw_text("*", body_font, ACCENT_COLOR, surface, x + 260, y)
        if default:
            draw_text(f"Default: {default}", body_font, SECONDARY_COLOR, surface, x, y + 50)

    # Draw run button
    run_button = draw_button(surface, "RUN", WINDOW_WIDTH // 2 - 50, 812, 100, 40, ACCENT_COLOR, (255, 255, 255), WINDOW_WIDTH // 2 - 16, 825)

    # Draw result part
    if show_result:
        result_section = pygame.Rect(50, 860, WINDOW_WIDTH - 100, 200)
        draw_rounded_rect(surface, result_section, (255, 255, 255), 10)
        draw_text(f"Download the annotated file: '{result_fn}  To visualize: Open with MuseScore 4'", larger_body_font, TEXT_COLOR, surface, 60, 890)
        if with_2D:
            draw_text("2D Keyboard Display will load after closing this window (press esc)", larger_body_font, TEXT_COLOR, surface, 60, 920)
        draw_text("THANKS FOR USING EduPo!", subheading_font, PRIMARY_COLOR, surface, WINDOW_WIDTH // 2 - 200, 970)
        draw_text("Note: Projection Piano in Development!", larger_body_font, SECONDARY_COLOR, surface, WINDOW_WIDTH // 2 - 160, 1005)

    # Draw the visible portion of the surface to the window
    window.blit(surface, (0, 0), (0, scroll_y, WINDOW_WIDTH, WINDOW_HEIGHT))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

if with_2D:
    from thiscode.keyboard import VisualizeKeyboard

    if start_measure != 1:
        print('Sorry, start_measure must be set to 1 when 2D keyboard is used. Exit.')
        exit()

    kb = VisualizeKeyboard(songname=xmlfn)
    
    if rh:
        kb.build_RH(rh)
    if lh:
        kb.build_LH(lh)

    kb.playsounds = not sound_off
    kb.speedfactor = speed_2D
    kb.f_rot = f_rot
    kb.play()
