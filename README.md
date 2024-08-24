# EduPiano
Please make sure to have/download the latest version of pygame, numpy, wave, tkinter, shutil, music21, simpleaudio, and vedo library in python.
Remember that all music shores have to be in .XML, because I'm still working on .pig and .midi files.
Before running main.py, move the score of your choice outside all of the folders of this application. 
When running and inputting the parameters, change n_measures to 800 or above if it is a long musical piece with many notes.

Also, to view the annotated output files, please have Musescore 4 downloaded or another musical software that can view the .xml files. If not, I've shown the output in my video/demo (https://youtu.be/wk9ouowyQqA). Also, read the info on my devpost submission page (https://devpost.com/software/altercomp)!

Hello! When you run my code, the 2D keyboard proba bly only opens fro a secodn or two adn the ncloses. After soem testing, I think it may be due to some address issue and pygame-specific as well. When I run the code on my original folder, it works completely fine (as shown in my demo video), but when I clone this github version (has the exactly same code), it doesn't work. When I renamed my original folder to something other than "Piano Fingering Generator" (this was the original name), it didn't work. So, I hypothesize that there is some address related issue going on, and it seems to be out of my control. I will continue to find ways to bypass this, so please do not give up on this project.
