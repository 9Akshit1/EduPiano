from vedo import printc
from thiscode.common import nameof
import thiscode.common as common
import thiscode.piano_lists as pl
import sys
import numpy as np
import music21
import wave
import os

try:
    import simpleaudio
    has_simpleaudio=True
except:
    print("Cannot find simpleaudio package. Not installed?")
    print('Try:\n(sudo) pip install --upgrade simpleaudio')
    has_simpleaudio=False
import threading

import pygame
import time

import math
import wave
import struct

def play_wav(file_path, duration):
    wave_obj = simpleaudio.WaveObject.from_wave_file(file_path)
    play_obj = wave_obj.play()
    time.sleep(duration)
    play_obj.stop()  # Wait until the sound has finished playing

def playHands(notes_list, durations):
    note_threads = []
    for i in range(len(notes_list)):
        note_thread = threading.Thread(target=play_wav, args=(f"assets/notes/{notes_list[i]}.wav", durations[i]))
        note_threads.append(note_thread)
    for thread in note_threads:
        thread.start()
    for thread in note_threads:
        thread.join()

#playHands(['C4', 'E4', 'G4', 'A#4', 'C6', 'G5'], [1, 0.25, 0.5, 2, 0.5, 0.5, 3.25, 0.6])   #testign purposes


###########################################################
class VisualizeKeyboard:

    def __init__(self, songname=''):

        pygame.init()
        pygame.mixer.set_num_channels(50)

        self.screen_width = 52 * 35
        self.screen_height = 400
        self.screen = pygame.display.set_mode([self.screen_width, self.screen_height])
        self.fps = 60
        self.timer = pygame.time.Clock()

        #self.piano_notes = pl.piano_notes
        self.white_notes = pl.white_notes
        self.black_notes = pl.black_notes

        self.normal_font = pygame.font.Font('assets/Terserah.ttf', 36)  
        self.small_font = pygame.font.Font('assets/Terserah.ttf', 16)
        self.real_small_font = pygame.font.Font('assets/Terserah.ttf', 10)

        pygame.display.set_caption("2D Keyboard")

        self.KB = dict()
        self.pyg = None                   #pygame plotter
        self.rightHand = None
        self.leftHand  = None
        self.pygRH = None
        self.pygLH = None
        self.playsounds = True
        self.verbose = True
        self.songname = songname
        self.t0 = 0 # keep track of how many seconds to play
        self.dt = 0.4
        self.speedfactor = 1        #note sound speed factor
        self.f_rot = True          #allow finger rotation
        self.engagedfingersR = [False]*6 # element 0 is dummy
        self.engagedfingersL = [False]*6
        self.engagedkeysR    = []
        self.engagedkeysL    = []
        self.build_keyboard()

    ################################################################################
    def makeHandActor(self, x, y, color, f=1):
        hand_components = []
        
        # Palm (Ellipsoid)
        if x == 23 * self.key_width:    #meanign its right hand
            palm = pygame.Rect(x + self.key_width, y - 60, self.key_width*5*f, 200*f)
        else:
            palm = pygame.Rect(x, y - 60, self.key_width*5*f, 200*f)
        hand_components.append(["ellipse", palm, color])

        # Wrist (Box)
        wrist = pygame.Rect(x + 30, y + 160, self.key_width*3.5*f, 50*f)
        hand_components.append(["wrist_rect", wrist, color])

        # Fingers (Cylinders)
        self.finger_indent_side = 5*f
        self.finger_width = self.key_width - 2*self.finger_indent_side
        self.finger_positions = [(0 - self.key_width + self.finger_indent_side, y-90*f), (self.finger_indent_side, y-160*f), (self.key_width + self.finger_indent_side, y-200*f), (2*self.key_width + self.finger_indent_side, y-175*f), (3*self.key_width + self.finger_indent_side, y-90*f)]   #remember the xy values are the tips of the fingers
        self.finger_heights = [90*f, 160*f, 200*f, 175*f, 90*f]

        for i, pos in enumerate(self.finger_positions):
            finger = pygame.Rect(x + pos[0], y - self.finger_heights[i], self.finger_width, self.finger_heights[i])
            hand_components.append(["rect", finger, color, ['type_rect']])

        return hand_components

    def build_RH(self, hand): #########################Build Right Hand
        self.rightHand = hand
        self.fingerY = 350
        f = common.handSizeFactor(hand.size)
        self.pygRH = self.makeHandActor(23 * self.key_width, self.fingerY, (139, 0, 0), f=f)   #x = 23 * self.key_width because right hand normally starts there at C4

    def build_LH(self, hand): ########################Build Left Hand
        self.leftHand = hand
        self.fingerY = 350
        f = common.handSizeFactor(hand.size)
        self.pygLH = self.makeHandActor(15 * self.key_width, self.fingerY, (0, 0, 255), f=f)   #x = 15 * self.key_width because right hand normally starts there at C3

    #######################################################Build Keyboard
    def build_keyboard(self):
        text_surface = self.normal_font.render(f'Playing {self.songname}', True, (0, 0, 0))
        self.screen.blit(text_surface, (self.screen_width / 2, 50))
        text_surface = self.normal_font.render('Press: Esc to quit, Space to play/pause, Left/Right to go forward/backward, Up/Down to change speed, S to on/off sound, and R to restart', True, (0, 0, 0))
        self.screen.blit(text_surface, (20 , 75))

        self.key_width = 35

        for i in range(52):
            rect = pygame.draw.rect(self.screen, 'white', [i * self.key_width, self.screen_height - 300, self.key_width, 300], 0, 2)    #wdith 35, height 300 for key
            self.KB.update({self.white_notes[i]: [rect, (255, 255, 255)]})
            pygame.draw.rect(self.screen, 'black', [i * self.key_width, self.screen_height - 300, self.key_width, 300], 2, 2)     
            key_label = self.small_font.render(self.white_notes[i], True, 'black')
            self.screen.blit(key_label, (i * self.key_width + 3, self.screen_height - 20))

        skip_count = 0
        last_skip = 2
        skip_track = 2
        for i in range(36):
            rect = pygame.draw.rect(self.screen, 'black', [23 + (i * self.key_width) + (skip_count * self.key_width), self.screen_height - 300, 24, 200], 0, 2)
            key_label = self.real_small_font.render(self.black_notes[i][1], True, 'white')   #uses sharps
            self.screen.blit(key_label, (25 + (i * self.key_width) + (skip_count * self.key_width), self.screen_height - 120))
            self.KB.update({self.black_notes[i][1]: [rect, (0, 0, 0)]})

            skip_track += 1
            if last_skip == 2 and skip_track == 3:
                last_skip = 3
                skip_track = 0
                skip_count += 1
            elif last_skip == 3 and skip_track == 2:
                last_skip = 2
                skip_track = 0
                skip_count += 1


    #####################################################################
    def play(self):

        printc('Press Space to start.')
        printc('Press Esc to exit.')

        if self.rightHand:
            self.engagedkeysR    = [False]*len(self.rightHand.noteseq)
            self.engagedfingersR = [False]*6  # element 0 is dummy
        if self.leftHand:
            self.engagedkeysL    = [False]*len(self.leftHand.noteseq)
            self.engagedfingersL = [False]*6

        pause = False
        t=0.0
        run = True
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        run = False
                        pygame.quit()
                        sys.exit()
                    elif event.key == pygame.K_UP:
                        self.speedfactor = self.speedfactor * 2       #shorten notes
                        print('Speedfactor = ', self.speedfactor)
                    elif event.key == pygame.K_DOWN: 
                        self.speedfactor = self.speedfactor / 2       #lengtehn notes 
                        print('Speedfactor = ', self.speedfactor)
                    elif event.key == pygame.K_s:
                        self.playsounds = not self.playsounds
                        print('playsounds = ', self.playsounds)
                    elif event.key == pygame.K_r:
                        t = 0.0
                        print('t = ', t)
                    elif event.key == pygame.K_RIGHT:
                        t -= 1
                        print('t = ', t)
                    elif event.key == pygame.K_LEFT:
                        t += 1
                        print('t = ', t)                     # absolute time flows
                    elif event.key == pygame.K_SPACE:
                        pause = not pause
            self.timer.tick(self.fps)
            if pause:
                #print(t)   #testing purposes
                self.play_notes = [[], []]
                if self.rightHand: self._moveHand( 1, t)
                if self.leftHand:  self._moveHand(-1, t)
                self.draw_n_sound()
                if t > 1000: 
                    run = False
                    break
                t += self.dt
        
            

        if self.verbose: printc('End of note sequence reached.')

        restart = str(input('Restart? (y/n)'))
        if restart == 'y':
            self.play()
        else:
            sys.exit()

    ###################################################################
    def _moveHand(self, side, t):############# runs inside play() loop
        if side == 1:
            c1, c2         = (220, 99, 71), (255, 165, 0)  #'tomato', 'orange'
            engagedkeys    = self.engagedkeysR
            engagedfingers = self.engagedfingersR
            H              = self.rightHand
            pygH            = self.pygRH
        else:
            c1, c2         = (128, 0, 128), (147, 112, 219)  #'purple', 'mediumpurple'
            engagedkeys    = self.engagedkeysL
            engagedfingers = self.engagedfingersL
            H              = self.leftHand
            pygH            = self.pygLH
        
        stop_search = False
        for i, n in enumerate(H.noteseq):#####################
            if side == 1:
                start, stop, f = n.time, n.time+n.duration, n.fingering
            else:
                start, stop, f = n.time, n.time+n.duration, 6-n.fingering
            if isinstance(f, str): continue
            if (f) and (stop <= t <= stop+self.dt) and (engagedkeys[i]): #release key: True, ___, True
                stop_search = True
                engagedkeys[i]    = False
                engagedfingers[f] = False
                name = nameof(n)

                if side == 1:     #right hand
                    colorF = (139, 0, 0)     #dark red
                else:             #left hand
                    colorF = (0, 0, 255)     #blue
                if len(name) == 2:   #white keys
                    colorK = (255, 255, 255)
                else:    #black keys   
                    colorK = (0, 0, 0)
                
                if pygH[f+1][3][0] == 'type_surface':
                    pygH[f+1][3] = ['type_rect']
                
                pygH[f+1][1] = pygame.draw.rect(self.screen, colorF, pygH[f+1][1])  #finger up, we use f+1 becasue there are 2 things before the fingers
                self.KB[name][0] = pygame.draw.rect(self.screen, colorK, self.KB[name][0])  #key released 
                #pygame.display.update()
                pygH[f+1][2] = colorF
                self.KB[name][1] = colorK
            else:
                if stop_search:
                    break
        
        stop_search = False
        for i, n in enumerate(H.noteseq):####################
            if side == 1:
                start, stop, f = n.time, n.time+n.duration, n.fingering
            else:
                start, stop, f = n.time, n.time+n.duration, 6-n.fingering
            if isinstance(f, str):
                print('Warning: cannot understand lyrics:',f, 'skip note',i)
                continue
            if (f) and (start <= t < stop) and (not engagedkeys[i]) and (not engagedfingers[f]):    #press key: True, ___, True, True
                stop_search = True
                # press key
                if i >= len(H.fingerseq): return
                engagedkeys[i]    = True
                engagedfingers[f] = True
                name = nameof(n)
                
                if t > self.t0:
                    self.t0 = t

                self.play_notes[0].append(name)
                self.play_notes[1].append(round(n.duration / self.speedfactor, 3))

                # Assuming the rotation is based on the difference in x-values. 
                # #we use f+1 becasue there are 2 things before the fingers
                # Angle in radians, then convert to degrees
                rotate_angle = np.degrees(np.arctan2((pygH[f+1][1].x + self.finger_width) - self.KB[name][0].centerx, (pygH[f+1][1].y + pygH[f+1][1].height) - self.KB[name][0].centery))     #prob the correect calculation, a little goofy but wahtev
                #rotate_angle = np.degrees(np.arctan2(self.KB[name][0].x - pygH[f+1][1].x, self.KB[name][0].y - pygH[f+1][1].y))  
                max_angles = [65, 45, 30, 20, 50]
                # If the absolute value of the angle is within the threshold, rotate the rect
                if (self.f_rot) and (abs(rotate_angle) <= max_angles[f-1]): 
                    rect_surface = pygame.Surface(pygH[f+1][1].size)
                    rect_surface.fill(c1)
                    rect_surface.set_colorkey('yellow')
                    rect0 = rect_surface.get_rect()
                    rect0.center = pygH[f+1][1].center

                    rotated_surface = pygame.transform.rotate(rect_surface, rotate_angle)
                    rotated_rect = rotated_surface.get_rect() 
                    rotated_rect.center = rect0.center
                    self.screen.blit(rotated_surface, rotated_rect)

                    pygH[f+1][3] = ['type_surface', rotated_surface, rotated_rect, rotate_angle, rect_surface]
                else:
                    # Just move all fingers by the movement for the finger to key
                    delta_x_move =  self.KB[name][0].x - pygH[f+1][1].x
                    for i in [2,3,4,5,6]:     #figner indexes
                        if pygH[i][3][0] == 'type_surface':
                            pygH[i][3][2].x += delta_x_move
                        pygH[i][1].x += delta_x_move
                    if side == 1:  #rigth hand
                        pygH[0][1].x = pygH[3][1].x - 2*self.finger_indent_side   #index 0 is palm, put it where index finger is. palm is part of arm
                    else:    #left hand
                        pygH[0][1].x = pygH[2][1].x   #index 0 is palm, put it where pinky finger is. palm is part of arm
                    pygH[1][1].x = pygH[4][1].x   #index 0 is wrist, put it where middle finger is. wrist is part of arm
                    pygH[f+1][1] = pygame.draw.rect(self.screen, c1, pygH[f+1][1])  #finger down

                self.KB[name][0] = pygame.draw.rect(self.screen, c2, self.KB[name][0])  #key pressed
                #pygame.display.update()
                pygH[f+1][2] = c1
                self.KB[name][1] = c2

                #if self.verbose:
                #    msg = 'meas.'+str(n.measure)+' t='+str(round(t,2))
                #    if side==1: printc(msg,'\t\t\t\tRH.finger', f, 'hit', name, c='b')
                #    else:       printc(msg,      '\tLH.finger', f, 'hit', name, c='m')
                
                if side == 1:
                    self.pygRH = pygH
                else:
                    self.pygLH = pygH
            else:
                if stop_search:
                    break
    
    def draw_n_sound(self):
        self.screen.fill('gray')

        text_surface = self.small_font.render(f'Playing {self.songname}', True, (0, 0, 0))
        self.screen.blit(text_surface, (self.screen_width / 2 - 140, 5))
        text_surface = self.small_font.render('Esc to quit, Space to play/pause, Left/Right to go forward/backward,', True, (0, 0, 0))
        self.screen.blit(text_surface, (self.screen_width / 2 - 230, 45))
        text_surface = self.small_font.render('Up/Down to speed up/slow down, S to toggle sound, R to restart', True, (0, 0, 0))
        self.screen.blit(text_surface, (self.screen_width / 2 - 230, 80))
        for i, k_name in enumerate(self.KB.keys()):
            if i < 52:     #white keys
                pygame.draw.rect(self.screen, self.KB[k_name][1], self.KB[k_name][0], 0, 2)
                pygame.draw.rect(self.screen, 'black', [i * self.key_width, self.screen_height - 300, self.key_width, 300], 2, 2)    #a small black space between the keys
                key_label = self.small_font.render(k_name, True, 'black')
                self.screen.blit(key_label, (i * self.key_width + 3, self.screen_height - 20))
            elif i == 52:     #first black key
                skip_count = 0
                last_skip = 2
                skip_track = 2
                pygame.draw.rect(self.screen, self.KB[k_name][1], self.KB[k_name][0], 0, 2)
                key_label = self.real_small_font.render(k_name, True, 'white')   #uses sharps
                self.screen.blit(key_label, (25 + (i * self.key_width) + (skip_count * self.key_width), self.screen_height - 120))
            else:      #next black keys     
                skip_track += 1
                if last_skip == 2 and skip_track == 3:
                    last_skip = 3
                    skip_track = 0
                    skip_count += 1
                elif last_skip == 3 and skip_track == 2:
                    last_skip = 2
                    skip_track = 0
                    skip_count += 1
                pygame.draw.rect(self.screen, self.KB[k_name][1], self.KB[k_name][0], 0, 2)
                key_label = self.real_small_font.render(k_name, True, 'white')   #uses sharps
                self.screen.blit(key_label, (25 + (i * self.key_width) + (skip_count * self.key_width), self.screen_height - 120))
        self.finger_labels = ['t', 'i', 'm', 'r', 'p']
        if self.pygRH:
            i = 0
            for component in self.pygRH:
                if component[0] == 'rect':    #fingers
                    if component[3][0] == 'type_surface':
                        self.screen.blit(component[3][1], component[3][2].topleft)
                    else:
                        pygame.draw.rect(self.screen, component[2], component[1])
                    key_label = self.small_font.render(self.finger_labels[i-2], True, 'black')  
                    self.screen.blit(key_label, (component[1].centerx - 6, component[1].centery - 6))
                elif component[0] == 'wrist_rect':     #wrist
                    pygame.draw.rect(self.screen, component[2], component[1])
                elif component[0] == 'ellipse':      #palm
                    pygame.draw.ellipse(self.screen, component[2], component[1])
                    key_label = self.normal_font.render('RH', True, 'black')  
                    self.screen.blit(key_label, (component[1].centerx - 20, component[1].centery - 30))
                i += 1
        if self.pygLH:
            i = 0
            for component in self.pygLH:
                if component[0] == 'rect':    #fingers
                    if component[3][0] == 'type_surface':
                        self.screen.blit(component[3][1], component[3][2].topleft)
                    else:
                        pygame.draw.rect(self.screen, component[2], component[1])
                    key_label = self.small_font.render(self.finger_labels[::-1][i-2], True, 'black')  
                    self.screen.blit(key_label, (component[1].centerx - 6, component[1].centery - 6))
                elif component[0] == 'wrist_rect':     #wrist
                    pygame.draw.rect(self.screen, component[2], component[1])
                elif component[0] == 'ellipse':      #palm
                    pygame.draw.ellipse(self.screen, component[2], component[1])
                    key_label = self.normal_font.render('LH', True, 'black')  
                    self.screen.blit(key_label, (component[1].centerx - 20, component[1].centery - 30))
                i += 1
        pygame.display.flip()
        if self.playsounds and self.play_notes[0]!=[] and self.play_notes[1]!=[]:
            playHands(self.play_notes[0], self.play_notes[1])
        else:
            time.sleep(max(self.play_notes[1]))    #wait for the longest note to finish, which means all the notes finish
