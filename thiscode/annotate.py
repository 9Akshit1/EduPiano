import csv, json, os, sys, platform
from music21 import converter, stream
from music21.articulations import Fingering
from thiscode.common import reader, PIG_to_Stream
from thiscode.hand import Hand

def annotate_fingers_xml(sf, hand, args, is_right=True):
    part = sf.parts[args.rbeam if is_right else args.lbeam]
    i = 0
    
    for p in part.flat.getElementsByClass("GeneralNote"):
        if i >= len(hand.noteseq):
            break
        if p.isNote:
            n = hand.noteseq[i]
            if hand.lyrics:
                p.addLyric(n.fingering)
            else:
                p.articulations.append(Fingering(n.fingering))
            i += 1
        elif p.isChord:
            for j, cn in enumerate(p.pitches):
                if i >= len(hand.noteseq):
                    break
                n = hand.noteseq[i]
                if hand.lyrics:
                    nl = len(cn.chord21.pitches) - cn.chordnr
                    p.addLyric(cn.fingering, nl)
                else:
                    p.articulations.append(Fingering(n.fingering))
                i += 1

    return sf

def annotate_PIG(hand, is_right=True):
    ans = []
    for n in hand.noteseq:
        onset_time = "{:.4f}".format(n.time)
        offset_time = "{:.4f}".format(n.time + n.duration)
        spelled_pitch = n.pitch
        onset_velocity = str(None)
        offset_velocity = str(None)
        channel = '0' if is_right else '1'
        finger_number = n.fingering if is_right else -n.fingering
        cost = n.cost
        ans.append((onset_time, offset_time, spelled_pitch, onset_velocity, offset_velocity, channel,
                    finger_number, cost, n.noteID))
    return ans

def runner(params):
    
    filename = params[0]
    outputfile = params[1]
    n_measures = params[2]
    start_measure = params[3]
    depth = params[4]
    rbeam = params[5]
    lbeam = params[6]
    quiet = params[7]
    musescore = params[8]
    below_beam = params[9]
    with_2D = params[10]
    speed_2D = params[11]
    sound_off = params[12]
    left_only = params[13]
    right_only = params[14]
    hand_size = params[15]
    
    if filename == '':
        print("Please input/upload the file you want annotated")
        return
    if outputfile == '':
        outputfile = 'output.xml'
    if n_measures == '':
        n_measures = 100
    else:
        n_measures = int(n_measures)
    if start_measure == '':
        start_measure = 1
    else:
        start_measure = int(start_measure)
    if depth == '':
        depth = 0
    else:
        depth = int(depth)
    if rbeam == '':
        rbeam = 0
    else:
        rbeam = int(rbeam)
    if lbeam == '':
        lbeam = 1
    else:
        lbeam = int(lbeam)
    if quiet == '':
        quiet = False
    else:
        quiet = bool(quiet)
    if musescore == '':
        musescore = False
    else:
        musescore = bool(musescore)
    if below_beam == '':
        below_beam = False
    else:
        below_beam = bool(below_beam)
    if with_2D == '':
        with_2D = False
    else:
        with_2D = bool(with_2D)
    if speed_2D == '':
        speed_2D = 1.0
    elif float(speed_2D) <= 0:
        print("speed_2D cannot be 0 or below")
        speed_2D = 1
    else:
        speed_2D = float(speed_2D)
    if sound_off == '':
        sound_off = False
    else:
        sound_off = bool(sound_off)
    if left_only == '':
        left_only = False
    else:
        left_only = bool(left_only)
    if right_only == '':
        right_only = False
    else:
        right_only = bool(right_only)
    if hand_size == '':
        hand_size = 'M'

    class Args(object):
        pass
    args = Args()
    args.filename = filename
    args.outputfile = outputfile
    args.n_measures = n_measures
    args.start_measure = start_measure
    args.depth = depth
    args.rbeam = rbeam
    args.lbeam = lbeam
    args.quiet = quiet
    args.musescore = musescore
    args.below_beam = below_beam
    args.with_2D = with_2D
    args.speed_2D = speed_2D
    args.sound_off = sound_off
    args.left_only = left_only
    args.right_only = right_only

    '''
    in reader for score, time_unit must be multiple of 2.
    beam = 0 is right hand
    beam = 1 is left hand.
    '''
    xmlfn = args.filename
    if '.msc' in args.filename:
        try:
            xmlfn = str(args.filename).replace('.mscz', '.xml').replace('.mscx', '.xml')
            print('..trying to convert your musescore file to', xmlfn)
            os.system(
                'musescore -f "' + args.filename + '" -o "' + xmlfn + '"')  # quotes avoid problems w/ spaces in filename
            sf = converter.parse(xmlfn)
            if not args.left_only:
                rh_noteseq = reader(sf, beam=args.rbeam)
            if not args.right_only:
                lh_noteseq = reader(sf, beam=args.lbeam)
        except:
            print('Unable to convert file, try to do it from musescore.')
            sys.exit()

    
    elif '.txt' in args.filename:
        pass    #delete after the conversion problem solved
        '''
        if not args.left_only:
            rh_noteseq = reader_PIG(args.filename, args.rbeam)
        if not args.right_only:
            lh_noteseq = reader_PIG(args.filename, args.lbeam)

    elif '.mid' in args.filename or '.midi' in args.filename:
        pm = pretty_midi.PrettyMIDI(args.filename)
        if not args.left_only:
            pm_right = pm.instruments[args.rbeam]
            rh_noteseq = reader_pretty_midi(pm_right, beam=args.rbeam)
        if not args.right_only:
            pm_left = pm.instruments[args.lbeam]
            lh_noteseq = reader_pretty_midi(pm_left, beam=args.lbeam)
        '''
    

    else:
        sc = converter.parse(xmlfn)
        if not args.left_only:
            rh_noteseq = reader(sc, beam=args.rbeam)
        if not args.right_only:
            lh_noteseq = reader(sc, beam=args.lbeam)

    if not args.left_only:
        rh = Hand("right", hand_size)
        rh.noteseq = rh_noteseq
        rh.verbose = not (args.quiet)
        if args.depth == 0:
            rh.autodepth = True
        else:
            rh.autodepth = False
            rh.depth = args.depth
        rh.lyrics = args.below_beam

        rh.generate(args.start_measure, args.n_measures)

    if not args.right_only:
        lh = Hand("left", hand_size)
        lh.noteseq = lh_noteseq
        lh.verbose = not (args.quiet)
        if args.depth == 0:
            lh.autodepth = True
        else:
            lh.autodepth = False
            lh.depth = args.depth
        lh.lyrics = args.below_beam

        lh.noteseq = lh_noteseq
        lh.generate(args.start_measure, args.n_measures)

    if args.outputfile is not None:
        ext = os.path.splitext(args.outputfile)[1]
        # an extended PIG file  (note ID) (onset time) (offset time) (spelled pitch) (onset velocity) (offset velocity) (channel) (finger number) (cost)
        if ext == ".txt":
            pig_notes = []
            if not args.left_only:
                pig_notes.extend(annotate_PIG(rh))

            if not args.right_only:
                pig_notes.extend(annotate_PIG(lh, is_right=False))

            with open(args.outputfile, 'wt') as out_file:
                tsv_writer = csv.writer(out_file, delimiter='\t')
                for idx, (onset_time, offset_time, spelled_pitch, onset_velocity, offset_velocity, channel,
                          finger_number, cost, id_n) in enumerate(sorted(pig_notes, key=lambda tup: (float(tup[0]), int(tup[5]), int(tup[2])))):
                    tsv_writer.writerow([idx, onset_time, offset_time, spelled_pitch, onset_velocity, offset_velocity,
                                         channel, finger_number, cost, id_n])
        else:
            ext = os.path.splitext(args.filename)[1]
            if ext in ['mid', 'midi']:
                sf = converter.parse(xmlfn)
            elif ext in ['txt']:
                sf = stream.Stream()
                if not args.left_only:
                    ptr = PIG_to_Stream(args.filename, 0)
                    sf.insert(0, ptr)
                if not args.right_only:
                    ptl = PIG_to_Stream(args.filename, 1)
                    sf.insert(0, ptl)  # 0=offset
            else:
                sf = converter.parse(xmlfn)

            # Annotate fingers in XML
            if not args.left_only:
                sf = annotate_fingers_xml(sf, rh, args, is_right=True)

            if not args.right_only:
                sf = annotate_fingers_xml(sf, lh, args, is_right=False)
            sf.write('musicxml', fp=args.outputfile)

            if args.musescore:  # -m option
                print('Opening musescore with output score:', args.outputfile)
                if platform.system() == 'Darwin':
                    os.system('open "' + args.outputfile + '"')
                else:
                    #doesn't work yet
                    print('''To visualize annotated score with fingering type, right click on the file 
in the file explorer and select "Open with" and select MuseScore 4.''')
            else:
                print('''To visualize annotated score with fingering type, right click on the file 
in the file explorer and select "Open with" and select MuseScore 4.''')

    if not args.left_only:
        return args.outputfile, args.with_2D, args.start_measure, xmlfn, rh, [], args.sound_off, args.speed_2D
    if not args.right_only:
        return args.outputfile, args.with_2D, args.start_measure, xmlfn, [], lh, args.sound_off, args.speed_2D
    else:     #msut be both
        return args.outputfile, args.with_2D, args.start_measure, xmlfn, rh, lh, args.sound_off, args.speed_2D


if __name__ == '__main__':
    runner(['scores/Night Dancer.xml', "output_annotated.xml", 800, '', '', '', '', '', True, '', True, 3.0, '', '', '', ''])
