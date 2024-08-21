import pygame
import os
import tkinter as tk
from tkinter import filedialog
import shutil
import time  # For simulating function execution time
from thiscode.annotate import runner

# Initialize Pygame
pygame.init()

# Set up the window
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 800
global window
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("EduPo")

# Colors
global BLACK

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Fonts
font = pygame.font.Font(None, 32)
global small_font, big_font
small_font = pygame.font.Font(None, 20)
big_font = pygame.font.Font(None, 50)

# Parameters
parameters = [
    ("filename* (str)", ""),
    ("outputfile (str)", "output.xml"),
    ("n_measures (int)", "100"),
    ("start_measure (int)", "1"),
    ("depth (int)", "0"),
    ("rbeam (int)", "0"),
    ("lbeam (int)", "1"),
    ("quiet (bool)", "False"),
    ("musescore (bool)", "False"),
    ("below_beam (bool)", "False"),
    ("with_2D (bool)", "False"),
    ("speed_2D (int)", "0"),
    ("sound_off (bool)", "False"),
    ("left_only (bool)", "False"),
    ("right_only (bool)", "False"),
    ("hand_size (str)", "M")
]

# Input fields
input_fields = ['' for _ in parameters]
active_field = None

#called in annotate.py at the end of the runner function
def finish_window(result_fn, load_kb):
    print('here begin')
    go = True
    while go:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                print('quit auto')
                go = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                        go = False
        draw_text(f"Download the annotated file by going to this application's folder to see a new .xml file called '{result_fn}' and download that.", small_font, BLACK, window, 50, 550)
        draw_text("To visualize annotated score with fingering type, right click on the file in the file explorer and select \"Open with\" and select MuseScore 4.", small_font, BLACK, window, 50, 575)
        if load_kb:
            draw_text("2D Keyboard Display will be loaded after this window closes.", small_font, BLACK, window, 50, 600)
        draw_text("THANKS FOR USING EduPo!", big_font, BLACK, window, WINDOW_WIDTH / 2 - 100, 650)
        draw_text("Note: Projection Piano in Development!", small_font, BLACK, window, 50, 710)
        if load_kb:
            draw_text("You can press Esc to quit this application now and see the 2D keyboard! Bye!", small_font, BLACK, window, 50, 740)
        else: 
            draw_text("You can press Esc to quit this application now! Bye!", small_font, BLACK, window, 50, 770)
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()

def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, 1, color)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

def draw_input_box(surface, x, y, w, h, text, active):
    color = RED if active else BLACK
    pygame.draw.rect(surface, color, (x, y, w, h), 2)
    txt_surface = small_font.render(text, True, BLACK)
    surface.blit(txt_surface, (x + 5, y + 5))

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
        input_fields[0] = filename
        return f"File uploaded: {filename}"
    return "No file selected"

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
            if 50 <= event.pos[0] <= 200 and 140 <= event.pos[1] <= 180:
                message = upload_file()
            elif WINDOW_WIDTH / 2 - 60 <= event.pos[0] <= WINDOW_WIDTH / 2 - 60 + 100 and 500 <= event.pos[1] <= 500 + 40:
                # Run button clicked
                global params
                params = {param: value for (param, _), value in zip(parameters, input_fields)}
                global result_fn, with_2D, start_measure, xmlfn, rh, lh, sound_off, speed_2D
                result_fn, with_2D, start_measure, xmlfn, rh, lh, sound_off, speed_2D  = runner(list(params.values()))
                show_result = True
            for i, (param, _) in enumerate(parameters):
                col = i % 4
                row = i // 4
                if 50 + col * 235 <= event.pos[0] <= 200 + col * 235 and 220 + row * 70 <= event.pos[1] <= 250 + row * 70 + 20:
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

    window.fill((220, 99, 71))   #TOMATO

    # Draw title and instructions
    draw_text("Welcome to EduPo, the Piano Fingering Generator & Teacher!", font, BLACK, window, 50, 50)
    draw_text("Upload your sheet music file (.xml, working on .pig, .mxl, .midi!) and enter the parameters you want.", small_font, BLACK, window, 50, 80)

    # Draw upload button
    pygame.draw.rect(window, GRAY, (50, 140, 150, 40))
    draw_text("Upload File (.xml)", small_font, BLACK, window, 70, 150)

    # Draw upload message
    draw_text(message, small_font, BLACK, window, 220, 150)

    # Draw parameter input fields in a grid
    for i, (param, default) in enumerate(parameters):
        col = i % 4
        row = i // 4
        x = 50 + col * 235
        y = 220 + row * 70
        draw_text(param, small_font, BLACK, window, x, y)
        draw_input_box(window, x, y + 20, 150, 30, input_fields[i], i == active_field)
        if i == 0:  # Add red asterisk for filename
            draw_text("*", small_font, RED, window, x + 160, y)
        if default:
            draw_text(f"Default: {default}", small_font, GRAY, window, x, y + 50)

    # Draw run button
    pygame.draw.rect(window, GREEN, (WINDOW_WIDTH / 2 - 60, 500, 100, 40))
    draw_text("Run", font, BLACK, window, WINDOW_WIDTH / 2  - 60 + 26, 500 + 10)

    # Draw result part
    draw_text("THANKS FOR USING EduPo!", big_font, BLACK, window, WINDOW_WIDTH / 2 - 300, 625)
    draw_text("Note: Projection Piano in Development!", small_font, BLACK, window, WINDOW_WIDTH / 2 - 100, 680)
    draw_text("You can press Esc to quit this application now! Bye!", small_font, BLACK, window, WINDOW_WIDTH / 2 - 300, 705)
    if show_result:
        draw_text(f"Download the annotated file by going to this application's folder to see a new .xml file called '{result_fn}' and download that.", small_font, BLACK, window, 50, 550)
        draw_text("To visualize annotated score with fingering type, right click on the file in the file explorer and select \"Open with\" and select MuseScore 4.", small_font, BLACK, window, 50, 575)
        if with_2D:
            draw_text("2D Keyboard Display will be loaded after this window closes.", small_font, BLACK, window, 50, 600)
        draw_text("THANKS FOR USING EduPo!", big_font, BLACK, window, WINDOW_WIDTH / 2 - 100, 650)
        draw_text("Note: Projection Piano in Development!", small_font, BLACK, window, 50, 710)
        if with_2D:
            draw_text("You can press Esc to quit this application now and see the 2D keyboard! Bye!", small_font, BLACK, window, 50, 740)
        else: 
            draw_text("You can press Esc to quit this application now! Bye!", small_font, BLACK, window, 50, 770)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

if with_2D:
    from thiscode.keyboard import VisualizeKeyboard

    if start_measure != 1:
        print('Sorry, start_measure must be set to 1 when -v option is used. Exit.')
        exit()

    kb = VisualizeKeyboard(songname=xmlfn)

    if rh != []:
        kb.build_RH(rh)
    if lh != []:
        kb.build_LH(lh)

    if sound_off:
        kb.playsounds = False

    kb.speedfactor = speed_2D        #note sound speed factor
    kb.play()