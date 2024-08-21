def nameof(n):
    a = n.name + str(n.octave)
    if "--" in a:                 # order matters
        b = a.replace("B--", "A")
        b = b.replace("A--", "G") # chain b.replace not a.replace
        b = b.replace("G--", "F")
        b = b.replace("E--", "D")
        b = b.replace("D--", "C")
        return b
    elif "-" in a:
        b = a.replace("C-", "B")
        b = b.replace("D-", "C#")  # chain b.replace not a.replace
        b = b.replace("E-", "D#")
        b = b.replace("F-", "E")
        b = b.replace("G-", "F#")
        b = b.replace("A-", "G#")
        b = b.replace("B-", "A#")
        return b
    elif "##" in a:
        b = a.replace("C##", "D")
        b = b.replace("D##", "E") # chain b.replace not a.replace
        b = b.replace("F##", "G")
        b = b.replace("G##", "A")
        b = b.replace("A##", "B")
        return b
    elif "E#" in a:
        b = a.replace("E#", "F")
        return b
    elif "B#" in a:
        b = a.replace("B#", "C")
        return b
    else:
        return a


def fpress(f, color):
    f.rotate(-20, axis=(1, 0, 0), point=f.pos())
    f.addPos([0, 0, -1])
    f.color(color)


def frelease(f):
    f.addPos([0, 0, 1])    
    f.rotate(20, axis=(1, 0, 0), point=f.pos())
    f.color((0.7, 0.3, 0.3))


def kpress(f, color):
    f.rotate(4, axis=(1, 0, 0), point=f.pos())
    f.addPos([0, 0, -0.4])
    f.color(color)


def krelease(f):
    f.addPos([0, 0, 0.4])
    p = f.pos()
    f.rotate(-4, axis=(1, 0, 0), point=p)
    if p[2] > 0.5:
        f.color("k")
    else:
        f.color("w")


_kb_layout = {
    "C"  : 0.5,
    "D"  : 1.5,
    "E"  : 2.5,
    "F"  : 3.5,
    "G"  : 4.5,
    "A"  : 5.5,
    "B"  : 6.5,
    "B#" : 0.5,
    "C#" : 1.0,
    "D#" : 2.0,
    "E#" : 3.5,
    "F#" : 4.0,
    "G#" : 5.0,
    "A#" : 6.0,
    "C-" : 6.5,
    "D-" : 1.0,
    "E-" : 2.0,
    "F-" : 2.5,
    "G-" : 4.0,
    "A-" : 5.0,
    "B-" : 6.0,
    "C##": 1.5,
    "D##": 2.5,
    "F##": 4.5,
    "G##": 5.5,
    "A##": 6.5,
    "D--": 0.5,
    "E--": 1.5,
    "G--": 3.5,
    "A--": 4.5,
    "B--": 5.5,
}

# TODO The assumtion of equal distance between notes is not totally true. 

def keypos_midi(n):  # position of notes on keyboard
    keybsize = 16.5  # cm
    k = keybsize / 7.0  # 7 notes
    step = (n.pitch % 12) * k
    return keybsize * (n.pitch // 12) + step


def keypos(n):  # position of notes on keyboard
    step = 0.0
    keybsize = 16.5  # cm
    k = keybsize / 7.0  # 7 notes
    if n.name in _kb_layout.keys():
        step = _kb_layout[n.name] * k
    else:
        print("ERROR note not found", n.name)
    return keybsize * n.octave + step


def handSizeFactor(s):
    f = 0.82
    if s == "XXS":
        f = 0.33
    elif s == "XS":
        f = 0.46
    elif s == "S":
        f = 0.64
    elif s == "M":
        f = 0.82
    elif s == "L":
        f = 1.0
    elif s == "XL":
        f = 1.1
    elif s == "XXL":
        f = 1.2
    return f




############################################################################################################################

from music21.articulations import Fingering
from operator import attrgetter


class INote:
    def __init__(self):
        self.name     = None
        self.isChord  = False
        self.isBlack  = False
        self.pitch = 0
        self.octave   = 0
        self.x        = 0.0
        self.time     = 0.0
        self.duration = 0.0
        self.fingering= 0
        self.measure  = 0
        self.chordnr  = 0
        self.NinChord = 0
        self.chordID  = 0
        self.noteID   = 0


#####################################################
def get_finger_music21(n, j=0):
    fingers = []
    for art in n.articulations:
        if type(art) == Fingering:
            fingers.append(art.fingerNumber)
    finger = 0
    if len(fingers) > j:
        finger = fingers[j]
    return finger


def reader(sf, beam=0):

    noteslist = []

    if hasattr(sf, 'parts'):
        if len(sf.parts) <= beam:
            return []
        strm = sf.parts[beam].flat
    elif hasattr(sf, 'elements'):
        if len(sf.elements)==1 and beam==1:
            strm = sf[0]
        else:
            if len(sf) <= beam:
                return []
            strm = sf[beam]
    else:
        strm = sf.flat

    print('Reading beam', beam, 'with', len(strm), 'objects in stream.')

    chordID = 0
    noteID = 0
    for n in strm.getElementsByClass("GeneralNote"):

        if n.duration.quarterLength==0: continue

        if hasattr(n, 'tie'): 
            if n.tie and (n.tie.type == 'continue' or n.tie.type=='stop'): continue

        if n.isNote:
            if len(noteslist) and n.offset == noteslist[-1].time:
                # print "doppia nota", n.name
                continue
            an        = INote()
            an.noteID = noteID
            an.note21 = n
            an.isChord= False
            an.name   = n.name
            an.octave = n.octave
            an.measure= n.measureNumber
            an.x      = keypos(n)
            an.pitch  = n.pitch.midi
            an.time   = n.offset
            an.duration = n.duration.quarterLength
            an.isBlack= False
            pc = n.pitch.pitchClass
            an.isBlack = False
            if pc in [1, 3, 6, 8, 10]:
                an.isBlack = True
            if n.lyrics:
                an.fingering = n.lyric

            an.fingering = get_finger_music21(n)
            noteslist.append(an)
            noteID += 1

        elif n.isChord:

            if n.tie and (n.tie.type=='continue' or n.tie.type=='stop'): continue
            sfasam = 0.05 # sfasa leggermente le note dell'accordo

            for j, cn in enumerate(n.pitches):
                an = INote()
                an.chordID  = chordID
                an.noteID = noteID
                an.isChord = True
                an.pitch = cn.midi
                an.note21  = cn
                an.name    = cn.name
                an.chordnr = j
                an.NinChord = len(n.pitches)
                an.octave  = cn.octave
                an.measure = n.measureNumber
                an.x       = keypos(cn)
                an.time    = n.offset-sfasam*(len(n.pitches)-j-1)
                an.duration= n.duration.quarterLength+sfasam*(an.NinChord-1)
                if hasattr(cn, 'pitch'):
                    pc = cn.pitch.pitchClass
                else:
                    pc = cn.pitchClass
                if pc in [1, 3, 6, 8, 10]:
                    an.isBlack = True
                else:
                    an.isBlack = False
                an.fingering = get_finger_music21(n, j)
                noteID += 1
                noteslist.append(an)
            chordID += 1

    if len(noteslist) < 2:
        print("Beam is empty.")
        return []
    return noteslist


def reader_pretty_midi(pm, beam=0):

    noteslist = []
    pm_notes = sorted(pm.notes, key=attrgetter('start'))
    pm_onsets = [onset.start for onset in pm_notes]

    print('Reading beam', beam, 'with', len(pm_notes), 'objects in stream.')

    chordID = 0

    ii = 0
    while ii < len(pm_notes):
        n = pm_notes[ii]
        n_duration = n.end - n.start
        chord_notes = pm_onsets.count(n.start)
        if chord_notes != 1:
            if n_duration == 0: continue
            an        = INote()
            an.noteID += 1
            an.note21 = n
            an.pitch = n.pitch
            an.isChord= False
            an.octave = n.pitch // 12
            an.x      = keypos_midi(n)
            an.time   = n.start
            an.duration = n_duration
            an.isBlack= False
            pc = n.pitch % 12
            if pc in [1, 3, 6, 8, 10]: an.isBlack = True
            noteslist.append(an)
            ii += 1

        else:
            if n_duration == 0: continue
            sfasam = 0.05 # sfasa leggermente le note dell'accordo

            for jj in range(chord_notes):
                cn = pm_notes[ii]
                cn_duration = cn.end - cn.start
                an = INote()
                an.chordID = chordID
                an.noteID += 1
                an.isChord = True
                an.chord21 = n
                an.pitch   = cn.pitch
                an.note21  = cn
                an.chordnr = jj
                an.NinChord = chord_notes
                an.octave  = cn.pitch // 2
                an.x       = keypos_midi(cn)
                an.time    = cn.start-sfasam*jj
                an.duration = cn_duration + sfasam * (jj - 1)
                pc = n.pitch % 12
                if pc in [1, 3, 6, 8, 10]: an.isBlack = True
                else: an.isBlack = False
                noteslist.append(an)
                ii += 1

            chordID += 1

    if len(noteslist)<2:
        print("Beam is empty.")
        return []
    return noteslist


def reader_PIG(fname, beam=0):
    # not done yet

    return []


def PIG_to_Stream(fname, beam=0, time_unit=.5, fixtempo=0):
    from music21 import stream, note, chord
    from music21.articulations import Fingering
    import numpy as np

    f = open(fname, "r")
    lines = f.readlines()
    f.close()

    #work out note type from distribution of durations
    # triplets are squashed to the closest figure
    durations = []
    firstonset = 0
    blines=[]
    for l in lines:
        if l.startswith('//'): continue
        _, onset, offset, name, _, _, channel, _ = l.split()
        onset, offset = float(onset), float(offset)
        if beam != int(channel): continue
        if not firstonset:
            firstonset = onset
        if offset-onset<0.0001: continue
        durations.append(offset-onset)
        blines.append(l)
    durations = np.array(durations)
    logdurs = -np.log2(durations)
    mindur = np.min(logdurs)
    expos = (logdurs-mindur).astype(int)
    if np.max(expos) > 3:
        mindur = mindur + 1
    #print(durations, '\nexpos=',expos, '\nmindur=', mindur)

    sf = stream.Part()
    sf.id = beam

    # first rest
    if not fixtempo and firstonset:
        r = note.Rest()
        logdur = -np.log2(firstonset)
        r.duration.quarterLength = 1.0/time_unit/pow(2, int(logdur-mindur))
        sf.append(r)

    n = len(blines)
    for i in range(n):
        if blines[i].startswith('//'): continue
        _, onset, offset, name, _, _, _, finger = blines[i].split()
        onset, offset = float(onset), float(offset)
        name = name.replace('b', '-')

        chordnotes = [name]
        for j in range(1, 5):
            if i+j<n:
                noteid1, onset1, offset1, name1, _, _, _, finger1 = blines[i+j].split()
                onset1 = float(onset1)
                if onset1 == onset:
                    name1 = name1.replace('b', '-')
                    chordnotes.append(name1)

        if len(chordnotes)>1:
            an = chord.Chord(chordnotes)
        else:
            an = note.Note(name)
            if '_' not in finger:
                x = Fingering(abs(int(finger)))
                x.style.absoluteY = 20
            an.articulations.append(x)

        if fixtempo:
            an.duration.quarterLength = fixtempo
        else:
            logdur = -np.log2(offset - onset)
            an.duration.quarterLength = 1.0/time_unit/pow(2, int(logdur-mindur))
        #print('note/chord:', an, an.duration.quarterLength, an.duration.type, 't=',onset)

        sf.append(an)

        # rest up to the next
        if i+1<n:
            _, onset1, _, _, _, _, _, _ = blines[i+1].split()
            onset1 = float(onset1)
            if onset1 - offset > 0:
                r = note.Rest()
                if fixtempo:
                    r.duration.quarterLength = fixtempo
                logdur = -np.log2(onset1 - offset)
                d = int(logdur-mindur)
                if d<4:
                    r.duration.quarterLength = 1.0/time_unit/pow(2, d)
                    sf.append(r)
    return sf