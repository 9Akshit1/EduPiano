from vedo import printc
from thiscode.common import nameof
import thiscode.common as common
import sys
import numpy as np
import music21
import wave

try:
    import simpleaudio
    has_simpleaudio=True
except:
    print("Cannot find simpleaudio package. Not installed?")
    print('Try:\n(sudo) pip install --upgrade simpleaudio')
    has_simpleaudio=False

import pygame
import thiscode.piano_lists as pl
from pygame import mixer
import time

#####################################################################
def soundof(notes, duration=1, volume=0.75, fading=750, wait=True):      #play notes for a duration
    if not has_simpleaudio:
        return

    sample_rate = 44100
    fade_in  = np.arange(0, 1,  1/fading)
    fade_out = np.arange(1, 0, -1/fading)
    timepoints = int(duration*sample_rate)

    intensity = np.zeros(timepoints)
    for n in notes:
        if isinstance(n, (int,float)): # user gives n in Hz
            freq = n
        else:
            if isinstance(n, str):
                n = music21.note.Note(n)
            if isinstance(n, music21.note.Note):
                n21 = n
            else:
                n21 = n.note21
            if hasattr(n21, 'pitch'):
                freq = n21.pitch.frequency
            else:
                freq = n21.frequency

        # get timesteps for each sample, duration is note duration in seconds
        t = np.linspace(0, duration, timepoints, False)

        # generate sine wave notes
        note_intensity = np.sin(freq * 2*np.pi * t)
        if len(intensity) > fading:
            note_intensity[:fading]  *= fade_in
            note_intensity[-fading:] *= fade_out
        intensity += note_intensity

    # normalize to 16-bit range
    audio = intensity * (32767 / np.max(np.abs(intensity)) * float(volume))

    # start playback
    play_obj = simpleaudio.play_buffer(audio.astype(np.int16), 1, 2, sample_rate)

    # wait for playback to finish before exiting
    if wait:
        play_obj.wait_done()
    return play_obj

# Function to load and combine multiple .wav files for a chord
def load_chord(note_sequence):
    combined_audio = None
    sample_rate = None

    for note in note_sequence:
        with wave.open(f"assets/notes/{note}.wav", 'rb') as wav_file:
            if sample_rate is None:
                sample_rate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            audio_data = np.frombuffer(wav_file.readframes(n_frames), dtype=np.int16)

            # Combine audio data (sum the waveforms)
            if combined_audio is None:
                combined_audio = audio_data
            else:
                # Make sure to match lengths by padding with zeros if necessary
                if len(audio_data) > len(combined_audio):
                    combined_audio = np.pad(combined_audio, (0, len(audio_data) - len(combined_audio)), 'constant')
                elif len(audio_data) < len(combined_audio):
                    audio_data = np.pad(audio_data, (0, len(combined_audio) - len(audio_data)), 'constant')

                combined_audio += audio_data
    combined_audio = np.clip(combined_audio, -32768, 32767)

    return combined_audio, sample_rate

def playNote(note_sequence, duration):      #play notes for a duration
    if not has_simpleaudio:
        return 
    
    if len(note_sequence) == 1:    #jsut oen note
        wave_obj = simpleaudio.WaveObject.from_wave_file(f"assets/notes/{note_sequence[0]}.wav")
    else:     #chord
        combined_audio, sample_rate = load_chord(note_sequence)
        #combined_audio = combined_audio.astype(np.int16).tobytes()
        #wave_obj = simpleaudio.WaveObject(combined_audio, 1, 2, sample_rate)  # 1 channel (mono), 2 bytes per sample
        if combined_audio is not None:  # Check if combined_audio is valid
            # Save combined audio to a .wav file
            wav_filename = "chord.wav"
            with wave.open("chord.wav", 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 2 bytes for int16
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(combined_audio.tobytes())

            # Play the saved .wav file
            wave_obj = simpleaudio.WaveObject.from_wave_file(wav_filename)
        else:
            print("No audio data to play. Please check the note files.")
    
    play_obj = wave_obj.play()
    # Wait for the duration 
    time.sleep(duration)  
    # Stop the playback (optional, in case you want to cut the sound)
    play_obj.stop()


#######################################################
def playSound(n, speedfactor=1.0, wait=True):            #play notes using speed
    if has_simpleaudio:
        soundof([n], n.duration/speedfactor, wait)
    else:
        try:
            s = music21.stream.Stream()
            if n.isChord:
                n = n.chord21
            else:
                s.append(n.note21)
            sp = music21.midi.realtime.StreamPlayer(s)
            sp.play()
        except:
            print('Unable to play sounds, add -z option')
            print('pygame not installed?')
        return


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
        self.dt = 0.1
        self.speedfactor = 1        #note sound speed factor
        self.engagedfingersR = [False]*6 # element 0 is dummy
        self.engagedfingersL = [False]*6
        self.engagedkeysR    = []
        self.engagedkeysL    = []
        self.build_keyboard()

    ################################################################################
    def makeHandActor(self, x, y, color, f=1):
        hand_components = []
        
        # Palm (Ellipsoid)
        palm = pygame.Rect(x, y - 60, self.key_width*5*f, 200*f)
        hand_components.append(["ellipse", palm, color])

        # Wrist (Box)
        wrist = pygame.Rect(x + 30, y + 160, self.key_width*3.5*f, 50*f)
        hand_components.append(["wrist_rect", wrist, color])

        # Fingers (Cylinders)
        self.finger_indent_side = 5*f
        self.finger_width = self.key_width - 2*self.finger_indent_side
        self.finger_positions = [(x - self.key_width + self.finger_indent_side, y-90*f), (x + self.finger_indent_side, y-160*f), (x + self.key_width + self.finger_indent_side, y-200*f), (x + 2*self.key_width + self.finger_indent_side, y-175*f), (x + 3*self.key_width + self.finger_indent_side, y-90*f)]   #remember the xy values are the tips of the fingers
        self.finger_heights = [90*f, 160*f, 200*f, 175*f, 90*f]

        for i, pos in enumerate(self.finger_positions):
            finger = pygame.Rect(pos[0], y - self.finger_heights[i], self.finger_width, self.finger_heights[i])
            hand_components.append(["rect", finger, color, ['type_rect']])

        return hand_components

    def build_RH(self, hand): #########################Build Right Hand
        self.rightHand = hand
        f = common.handSizeFactor(hand.size)
        self.pygRH = self.makeHandActor(23 * self.key_width, 350, (139, 0, 0), f=f)   #x = 23 * self.key_width because right hand normally starts there at C4

    def build_LH(self, hand): ########################Build Left Hand
        self.leftHand = hand
        f = common.handSizeFactor(hand.size)
        self.pygLH = self.makeHandActor(15 * self.key_width, 350, (0, 0, 255), f=f)   #x = 15 * self.key_width because right hand normally starts there at C3

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
        while True:
            self.timer.tick(self.fps)
            if pause:
                if self.rightHand: self._moveHand( 1, t)
                if self.leftHand:  self._moveHand(-1, t)
                self.draw()
                if t > 1000: break
                t += self.dt

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
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
                        t -= self.dt*10 
                        print('t = ', t)
                    elif event.key == pygame.K_LEFT:
                        t += self.dt*10 
                        print('t = ', t)                     # absolute time flows
                    elif event.key == pygame.K_SPACE:
                        pause = not pause

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

        for i, n in enumerate(H.noteseq):#####################
            start, stop, f = n.time, n.time+n.duration, n.fingering
            if isinstance(f, str): continue
            if f and stop <= t <= stop+self.dt and engagedkeys[i]: #release key
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
                    # Create a new surface of the same size as the original
                    #pygH[f+1][3][4].fill(colorF)
                    un_rotated_surface = pygame.transform.rotate(pygH[f+1][3][4], -pygH[f+1][3][3])
                    un_rotated_rect = un_rotated_surface.get_rect(center=pygH[f+1][3][2].center)
                    pygH[f+1][3] = ['type_rect']
                    pygH[f+1][1] = un_rotated_rect
                    pygH[f+1][1].width, pygH[f+1][1].height = self.finger_width, self.finger_heights[f-1]
                
                pygH[f+1][1] = pygame.draw.rect(self.screen, colorF, pygH[f+1][1])  #finger up, we use f+1 becasue there are 2 things before the fingers
                self.KB[name][0] = pygame.draw.rect(self.screen, colorK, self.KB[name][0])  #key released 
                pygame.display.update()
                pygH[f+1][2] = colorF
                self.KB[name][1] = colorK

        self.chord_notes = [[], 0] #name(s), duration
        self.chord_is_on = False
        for i, n in enumerate(H.noteseq):####################
            start, stop, f = n.time, n.time+n.duration, n.fingering
            if isinstance(f, str):
                print('Warning: cannot understand lyrics:',f, 'skip note',i)
                continue
            if f and start <= t < stop and not engagedkeys[i] and not engagedfingers[f]:
                # press key
                if i >= len(H.fingerseq): return
                engagedkeys[i]    = True
                engagedfingers[f] = True
                name = nameof(n)
       
                if t > self.t0:
                    self.t0 = t
                
                if n.isChord:
                    self.chord_notes[0].append(n) 
                    #print('hey appeneded: ', self.chord_notes[0])   #for testign purposes
                    self.chord_notes[1] = n.duration / self.speedfactor
                    self.chord_is_on = True

                    try:
                        next_item = H.noteseq[i+1]
                        next_start, next_stop, next_f = next_item.time, next_item.time + next_item.duration, next_item.fingering
                        if not (next_f and next_start <= t < next_stop and not engagedkeys[i+1] and not engagedfingers[f]):     #meanign this is the last note in instance
                            #print('play chord and section is done')    #for testing purposes
                            playNote(self.chord_notes[0], self.chord_notes[1])
                            #soundof(self.chord_notes[0], duration=self.chord_notes[1], wait=True)  #another method of playing notes
                    except Exception:
                        pass         #should never go here unless its the very last ntoe of the piece
                else:       #not chord
                    self.chord_is_on = False
                    #print("chord_notes length = ", len(self.chord_notes[0]))   #for testign purposes
                    if len(self.chord_notes[0]) > 0:
                        #print('play chord first then continue with the single note')   #for testign purposes
                        playNote(self.chord_notes[0], self.chord_notes[1])
                        #soundof(self.chord_notes[0], duration=self.chord_notes[1], wait=True) #another method of playing notes
                    else:
                        #print('not a chord and continue')   #for testign purposes
                        pass

                # Assuming the rotation is based on the difference in x-values. 
                # #we use f+1 becasue there are 2 things before the fingers
                # Angle in radians, then convert to degrees
                rotate_angle = np.degrees(np.arctan2(self.KB[name][0].x - pygH[f+1][1].x, self.KB[name][0].y - pygH[f+1][1].y))  
                # If the absolute value of the angle is within the threshold, rotate the rect
                if abs(rotate_angle) <= 30:       #30 is the max amoutn of dgerees that the finger can rotate
                    rect_surface = pygame.Surface(pygH[f+1][1].size)
                    #print('rect_surface size: ', rect_surface.get_size())
                    #rect_surface.fill(c1)
                    rotated_surface = pygame.transform.rotate(rect_surface, rotate_angle)
                    rotated_rect = rotated_surface.get_rect(center=pygH[f+1][1].center)   
                    pygH[f+1][3] = ['type_surface', rotated_surface, rotated_rect, rotate_angle, rect_surface]
                    self.screen.blit(pygH[f+1][3][1], pygH[f+1][3][2].topleft)
                else:
                    # Just move all fingers by the movement for the finger to key
                    delta_x_move =  self.KB[name][0].x - pygH[f+1][1].x
                    for i in [2,3,4,5,6]:     #figner indexes
                        if pygH[i][3][0] == 'type_rect':
                            pygH[i][1].x += delta_x_move
                        else:   #type_surface
                            pygH[i][3][2].centerx += delta_x_move
                    pygH[0][1].x = pygH[2][1].x   #index 0 is palm, put it where index finger is. palm is part of arm
                    pygH[1][1].x = pygH[4][1].x   #index 0 is wrist, put it where middle finger is. wrist is part of arm
                    pygH[f+1][1] = pygame.draw.rect(self.screen, c1, pygH[f+1][1])  #finger down

                self.KB[name][0] = pygame.draw.rect(self.screen, c2, self.KB[name][0])  #key pressed
                pygame.display.update()
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
                if self.playsounds:
                    if not self.chord_is_on:    #so when no chord
                        playNote([name], n.duration / self.speedfactor)
                        #soundof([n], duration = n.duration / self.speedfactor, wait=True)   #another method of playing notes
                    else:
                        pass
                else:
                    pass
    
    def draw(self):
        self.screen.fill('gray')

        text_surface = self.small_font.render(f'Playing {self.songname}', True, (0, 0, 0))
        self.screen.blit(text_surface, (self.screen_width / 2 - 100, 5))
        text_surface = self.small_font.render('Esc to quit, Space to play/pause, Left/Right to go forward/backward,', True, (0, 0, 0))
        self.screen.blit(text_surface, (self.screen_width / 2 - 200, 45))
        text_surface = self.small_font.render('Up/Down to speed up/slow down, S to toggle sound, R to restart', True, (0, 0, 0))
        self.screen.blit(text_surface, (self.screen_width / 2 - 200, 80))
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

        if self.pygRH:
            for component in self.pygRH:
                if component[0] == 'rect':    #fingers
                    if component[3][0] == 'type_surface':
                        self.screen.blit(component[3][1], component[3][2].topleft)
                    else:
                        pygame.draw.rect(self.screen, component[2], component[1])
                elif component[0] == 'wrist_rect':     #wrist
                    pygame.draw.rect(self.screen, component[2], component[1])
                elif component[0] == 'ellipse':      #palm
                    pygame.draw.ellipse(self.screen, component[2], component[1])
                    key_label = self.normal_font.render('RH', True, 'black')  
                    self.screen.blit(key_label, (component[1].centerx, component[1].centery))
        if self.pygLH:
            for component in self.pygLH:
                if component[0] == 'rect':    #fingers
                    if component[3][0] == 'type_surface':
                        self.screen.blit(component[3][1], component[3][2].topleft)
                    else:
                        pygame.draw.rect(self.screen, component[2], component[1])
                elif component[0] == 'wrist_rect':     #wrist
                    pygame.draw.rect(self.screen, component[2], component[1])
                elif component[0] == 'ellipse':      #palm
                    pygame.draw.ellipse(self.screen, component[2], component[1])
                    key_label = self.normal_font.render('LH', True, 'black')  
                    self.screen.blit(key_label, (component[1].centerx, component[1].centery - 10))
        pygame.display.flip()
        


############################ test
if __name__ == "__main__":
    vk = VisualizeKeyboard('Night Dancer')




