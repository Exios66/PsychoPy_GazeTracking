#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This experiment was created using PsychoPy3 Experiment Builder (v2022.2.0dev3),
    on Wed May 18 14:18:19 2022
If you publish work using this script the most relevant publication is:

    Peirce J, Gray JR, Simpson S, MacAskill M, Höchenberger R, Sogo H, Kastman E, Lindeløv JK. (2019) 
        PsychoPy2: Experiments in behavior made easy Behav Res 51: 195. 
        https://doi.org/10.3758/s13428-018-01193-y

"""

from psychopy import locale_setup
from psychopy import prefs
from psychopy import sound, gui, visual, core, data, event, logging, clock, colors, layout
from psychopy.constants import (NOT_STARTED, STARTED, PLAYING, PAUSED,
                                STOPPED, FINISHED, PRESSED, RELEASED, FOREVER)

import numpy as np  # whole numpy lib is available, prepend 'np.'
from numpy import (sin, cos, tan, log, log10, pi, average,
                   sqrt, std, deg2rad, rad2deg, linspace, asarray)
from numpy.random import random, randint, normal, shuffle, choice as randchoice
import os  # handy system and path functions
import sys  # to get file system encoding

import psychopy.iohub as io
from psychopy.hardware import keyboard



# Ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))
os.chdir(_thisDir)
# Store info about the experiment session
psychopyVersion = '2022.2.0dev3'
expName = 'gamma_correction_visual'  # from the Builder filename that created this script
expInfo = {'participant': '', 'session': '001'}
dlg = gui.DlgFromDict(dictionary=expInfo, sortKeys=False, title=expName)
if dlg.OK == False:
    core.quit()  # user pressed cancel
expInfo['date'] = data.getDateStr()  # add a simple timestamp
expInfo['expName'] = expName
expInfo['psychopyVersion'] = psychopyVersion

# Data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
filename = _thisDir + os.sep + u'data/%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])

# An ExperimentHandler isn't essential but helps with data saving
thisExp = data.ExperimentHandler(name=expName, version='',
    extraInfo=expInfo, runtimeInfo=None,
    originPath='/Users/lpzjwp/code/psychopy/git/psychopy/demos/builder/Tools/gammaCorrection/gamma_correction_visual_lastrun.py',
    savePickle=True, saveWideText=True,
    dataFileName=filename)
# save a log file for detail verbose info
logFile = logging.LogFile(filename+'.log', level=logging.EXP)
logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file

endExpNow = False  # flag for 'escape' or other condition => quit the exp
frameTolerance = 0.001  # how close to onset before 'same' frame

# Start Code - component code to be run after the window creation

# Setup the Window
win = visual.Window(
    size=[1440, 900], fullscr=True, screen=0, 
    winType='pyglet', allowGUI=False, allowStencil=False,
    monitor='testMonitor', color=[0,0,0], colorSpace='rgb',
    blendMode='avg', useFBO=True, 
    units='height')
# store frame rate of monitor if we can measure it
expInfo['frameRate'] = win.getActualFrameRate()
if expInfo['frameRate'] != None:
    frameDur = 1.0 / round(expInfo['frameRate'])
else:
    frameDur = 1.0 / 60.0  # could not measure, so guess
# Setup ioHub
ioConfig = {}

# Setup iohub keyboard
ioConfig['Keyboard'] = dict(use_keymap='psychopy')

ioSession = '1'
if 'session' in expInfo:
    ioSession = str(expInfo['session'])
ioServer = io.launchHubServer(window=win, **ioConfig)
eyetracker = None

# create a default keyboard (e.g. to check for escape)
defaultKeyboard = keyboard.Keyboard(backend='iohub')

# Initialize components for Routine "setup_trial"
setup_trialClock = core.Clock()
# Run 'Begin Experiment' code from set_gamma
gamma = 1

# Initialize components for Routine "frames"
framesClock = core.Clock()
luminance_000 = visual.GratingStim(
    win=win, name='luminance_000',units='height', 
    tex='resources/low_contrast.png', mask=None, anchor='center',
    ori=1.0, pos=(0, 0), size=(0.5,0.5), sf=5.0, phase=0.0,
    color=[1,1,1], colorSpace='rgb',
    opacity=1.0, contrast=1.0, blendmode='avg',
    texRes=256.0, interpolate=True, depth=0.0)
second_ord_025 = visual.GratingStim(
    win=win, name='second_ord_025',units='height', 
    tex='resources/second_order_tex.png', mask=None, anchor='center',
    ori=1.0, pos=(0, 0), size=(0.5,0.5), sf=5.0, phase=0.25,
    color=[1,1,1], colorSpace='rgb',
    opacity=1.0, contrast=1.0, blendmode='avg',
    texRes=256.0, interpolate=True, depth=-1.0)
luminance_050 = visual.GratingStim(
    win=win, name='luminance_050',units='height', 
    tex='resources/low_contrast.png', mask=None, anchor='center',
    ori=1.0, pos=(0, 0), size=(0.5,0.5), sf=5.0, phase=0.5,
    color=[1,1,1], colorSpace='rgb',
    opacity=1.0, contrast=1.0, blendmode='avg',
    texRes=256.0, interpolate=True, depth=-2.0)
second_ord_075 = visual.GratingStim(
    win=win, name='second_ord_075',units='height', 
    tex='resources/second_order_tex.png', mask=None, anchor='center',
    ori=1.0, pos=(0, 0), size=(0.5,0.5), sf=5.0, phase=0.75,
    color=[1,1,1], colorSpace='rgb',
    opacity=1.0, contrast=1.0, blendmode='avg',
    texRes=256.0, interpolate=True, depth=-3.0)

# Initialize components for Routine "response"
responseClock = core.Clock()
resp = keyboard.Keyboard()

# Initialize components for Routine "feedback"
feedbackClock = core.Clock()
show_feedbk = visual.TextBox2(
     win, text='', font='Open Sans',
     pos=(0, 0),     letterHeight=0.05,
     size=(None, None), borderWidth=2.0,
     color='white', colorSpace='rgb',
     opacity=None,
     bold=False, italic=False,
     lineSpacing=1.0,
     padding=0.0, alignment='center',
     anchor='center',
     fillColor=None, borderColor=None,
     flipHoriz=False, flipVert=False, languageStyle='LTR',
     editable=False,
     name='show_feedbk',
     autoLog=True,
)

# Create some handy timers
globalClock = core.Clock()  # to track the time since experiment started
routineTimer = core.CountdownTimer()  # to track time remaining of each (non-slip) routine 

# set up handler to look after randomisation of trials etc
conditions = data.importConditions('questStairs.xlsx')
trials = data.MultiStairHandler(stairType='QUEST', name='trials',
    nTrials=30.0,
    conditions=conditions,
    method='random',
    originPath=-1)
thisExp.addLoop(trials)  # add the loop to the experiment
# initialise values for first condition
level = trials._nextIntensity  # initialise some vals
condition = trials.currentStaircase.condition

for level, condition in trials:
    currentLoop = trials
    # abbreviate parameter names if possible (e.g. rgb=condition.rgb)
    for paramName in condition:
        exec(paramName + '= condition[paramName]')
    
    # ------Prepare to start Routine "setup_trial"-------
    continueRoutine = True
    # update component parameters for each repeat
    # Run 'Begin Routine' code from set_gamma
    gamma = level # from staircase
    trials.addOtherData('gamma', level)
    
    win.gamma = level
    # Run 'Begin Routine' code from rand_side
    # randomize whether "high gamma" is right or left
    # "high" is where the grating appears to drift if
    # the gamma is too high. Count as "correct" so
    # that next level will reduce.
    if random() > 0.5:
        ori = 180
        high_ans = 'right'
    else:
        ori = 0
        high_ans = 'left'
    # keep track of which components have finished
    setup_trialComponents = []
    for thisComponent in setup_trialComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    setup_trialClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
    frameN = -1
    
    # -------Run Routine "setup_trial"-------
    while continueRoutine:
        # get current time
        t = setup_trialClock.getTime()
        tThisFlip = win.getFutureFlipTime(clock=setup_trialClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # check for quit (typically the Esc key)
        if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
            core.quit()
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in setup_trialComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # -------Ending Routine "setup_trial"-------
    for thisComponent in setup_trialComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # the Routine "setup_trial" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # set up handler to look after randomisation of conditions etc
    frame_cycles = data.TrialHandler(nReps=5.0, method='sequential', 
        extraInfo=expInfo, originPath=-1,
        trialList=[None],
        seed=None, name='frame_cycles')
    thisExp.addLoop(frame_cycles)  # add the loop to the experiment
    thisFrame_cycle = frame_cycles.trialList[0]  # so we can initialise stimuli with some values
    # abbreviate parameter names if possible (e.g. rgb = thisFrame_cycle.rgb)
    if thisFrame_cycle != None:
        for paramName in thisFrame_cycle:
            exec('{} = thisFrame_cycle[paramName]'.format(paramName))
    
    for thisFrame_cycle in frame_cycles:
        currentLoop = frame_cycles
        # abbreviate parameter names if possible (e.g. rgb = thisFrame_cycle.rgb)
        if thisFrame_cycle != None:
            for paramName in thisFrame_cycle:
                exec('{} = thisFrame_cycle[paramName]'.format(paramName))
        
        # ------Prepare to start Routine "frames"-------
        continueRoutine = True
        routineTimer.add(0.200000)
        # update component parameters for each repeat
        luminance_000.setOri(ori)
        second_ord_025.setOri(ori)
        luminance_050.setOri(ori)
        second_ord_075.setOri(ori)
        # keep track of which components have finished
        framesComponents = [luminance_000, second_ord_025, luminance_050, second_ord_075]
        for thisComponent in framesComponents:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        framesClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
        frameN = -1
        
        # -------Run Routine "frames"-------
        while continueRoutine and routineTimer.getTime() > 0:
            # get current time
            t = framesClock.getTime()
            tThisFlip = win.getFutureFlipTime(clock=framesClock)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame
            
            # *luminance_000* updates
            if luminance_000.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                luminance_000.frameNStart = frameN  # exact frame index
                luminance_000.tStart = t  # local t and not account for scr refresh
                luminance_000.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(luminance_000, 'tStartRefresh')  # time at next scr refresh
                luminance_000.setAutoDraw(True)
            if luminance_000.status == STARTED:
                if frameN >= (luminance_000.frameNStart + 3):
                    # keep track of stop time/frame for later
                    luminance_000.tStop = t  # not accounting for scr refresh
                    luminance_000.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(luminance_000, 'tStopRefresh')  # time at next scr refresh
                    luminance_000.setAutoDraw(False)
            
            # *second_ord_025* updates
            if second_ord_025.status == NOT_STARTED and frameN >= 3:
                # keep track of start time/frame for later
                second_ord_025.frameNStart = frameN  # exact frame index
                second_ord_025.tStart = t  # local t and not account for scr refresh
                second_ord_025.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(second_ord_025, 'tStartRefresh')  # time at next scr refresh
                second_ord_025.setAutoDraw(True)
            if second_ord_025.status == STARTED:
                if frameN >= (second_ord_025.frameNStart + 3):
                    # keep track of stop time/frame for later
                    second_ord_025.tStop = t  # not accounting for scr refresh
                    second_ord_025.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(second_ord_025, 'tStopRefresh')  # time at next scr refresh
                    second_ord_025.setAutoDraw(False)
            
            # *luminance_050* updates
            if luminance_050.status == NOT_STARTED and frameN >= 6:
                # keep track of start time/frame for later
                luminance_050.frameNStart = frameN  # exact frame index
                luminance_050.tStart = t  # local t and not account for scr refresh
                luminance_050.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(luminance_050, 'tStartRefresh')  # time at next scr refresh
                luminance_050.setAutoDraw(True)
            if luminance_050.status == STARTED:
                if frameN >= (luminance_050.frameNStart + 3):
                    # keep track of stop time/frame for later
                    luminance_050.tStop = t  # not accounting for scr refresh
                    luminance_050.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(luminance_050, 'tStopRefresh')  # time at next scr refresh
                    luminance_050.setAutoDraw(False)
            
            # *second_ord_075* updates
            if second_ord_075.status == NOT_STARTED and frameN >= 9:
                # keep track of start time/frame for later
                second_ord_075.frameNStart = frameN  # exact frame index
                second_ord_075.tStart = t  # local t and not account for scr refresh
                second_ord_075.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(second_ord_075, 'tStartRefresh')  # time at next scr refresh
                second_ord_075.setAutoDraw(True)
            if second_ord_075.status == STARTED:
                if frameN >= (second_ord_075.frameNStart + 3):
                    # keep track of stop time/frame for later
                    second_ord_075.tStop = t  # not accounting for scr refresh
                    second_ord_075.frameNStop = frameN  # exact frame index
                    win.timeOnFlip(second_ord_075, 'tStopRefresh')  # time at next scr refresh
                    second_ord_075.setAutoDraw(False)
            
            # check for quit (typically the Esc key)
            if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
                core.quit()
            
            # check if all components have finished
            if not continueRoutine:  # a component has requested a forced-end of Routine
                break
            continueRoutine = False  # will revert to True if at least one component still running
            for thisComponent in framesComponents:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished
            
            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()
        
        # -------Ending Routine "frames"-------
        for thisComponent in framesComponents:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
    # completed 5.0 repeats of 'frame_cycles'
    
    
    # ------Prepare to start Routine "response"-------
    continueRoutine = True
    # update component parameters for each repeat
    resp.keys = []
    resp.rt = []
    _resp_allKeys = []
    # keep track of which components have finished
    responseComponents = [resp]
    for thisComponent in responseComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    responseClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
    frameN = -1
    
    # -------Run Routine "response"-------
    while continueRoutine:
        # get current time
        t = responseClock.getTime()
        tThisFlip = win.getFutureFlipTime(clock=responseClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *resp* updates
        waitOnFlip = False
        if resp.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            resp.frameNStart = frameN  # exact frame index
            resp.tStart = t  # local t and not account for scr refresh
            resp.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(resp, 'tStartRefresh')  # time at next scr refresh
            resp.status = STARTED
            # keyboard checking is just starting
            waitOnFlip = True
            win.callOnFlip(resp.clock.reset)  # t=0 on next screen flip
        if resp.status == STARTED and not waitOnFlip:
            theseKeys = resp.getKeys(keyList=['left','right'], waitRelease=False)
            _resp_allKeys.extend(theseKeys)
            if len(_resp_allKeys):
                resp.keys = _resp_allKeys[-1].name  # just the last key pressed
                resp.rt = _resp_allKeys[-1].rt
                # was this correct?
                if (resp.keys == str('right')) or (resp.keys == 'right'):
                    resp.corr = 1
                else:
                    resp.corr = 0
                # a response ends the routine
                continueRoutine = False
        
        # check for quit (typically the Esc key)
        if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
            core.quit()
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in responseComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # -------Ending Routine "response"-------
    for thisComponent in responseComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # check responses
    if resp.keys in ['', [], None]:  # No response was made
        resp.keys = None
        # was no response the correct answer?!
        if str('right').lower() == 'none':
           resp.corr = 1;  # correct non-response
        else:
           resp.corr = 0;  # failed to respond (incorrectly)
    # store data for trials (MultiStairHandler)
    trials.addResponse(resp.corr, level)
    trials.addOtherData('resp.rt', resp.rt)
    trials.addOtherData('resp.started', resp.tStartRefresh)
    trials.addOtherData('resp.stopped', resp.tStopRefresh)
    # the Routine "response" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()
    
    # ------Prepare to start Routine "feedback"-------
    continueRoutine = True
    routineTimer.add(0.500000)
    # update component parameters for each repeat
    # Run 'Begin Routine' code from make_feedbk
    msg = f"gamma = {level} \nresp:{resp.keys}"
    show_feedbk.reset()
    show_feedbk.setText(msg)
    # keep track of which components have finished
    feedbackComponents = [show_feedbk]
    for thisComponent in feedbackComponents:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    feedbackClock.reset(-_timeToFirstFrame)  # t0 is time of first possible flip
    frameN = -1
    
    # -------Run Routine "feedback"-------
    while continueRoutine and routineTimer.getTime() > 0:
        # get current time
        t = feedbackClock.getTime()
        tThisFlip = win.getFutureFlipTime(clock=feedbackClock)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame
        
        # *show_feedbk* updates
        if show_feedbk.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            show_feedbk.frameNStart = frameN  # exact frame index
            show_feedbk.tStart = t  # local t and not account for scr refresh
            show_feedbk.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(show_feedbk, 'tStartRefresh')  # time at next scr refresh
            show_feedbk.setAutoDraw(True)
        if show_feedbk.status == STARTED:
            # is it time to stop? (based on global clock, using actual start)
            if tThisFlipGlobal > show_feedbk.tStartRefresh + 0.5-frameTolerance:
                # keep track of stop time/frame for later
                show_feedbk.tStop = t  # not accounting for scr refresh
                show_feedbk.frameNStop = frameN  # exact frame index
                win.timeOnFlip(show_feedbk, 'tStopRefresh')  # time at next scr refresh
                show_feedbk.setAutoDraw(False)
        
        # check for quit (typically the Esc key)
        if endExpNow or defaultKeyboard.getKeys(keyList=["escape"]):
            core.quit()
        
        # check if all components have finished
        if not continueRoutine:  # a component has requested a forced-end of Routine
            break
        continueRoutine = False  # will revert to True if at least one component still running
        for thisComponent in feedbackComponents:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished
        
        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()
    
    # -------Ending Routine "feedback"-------
    for thisComponent in feedbackComponents:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    trials.addOtherData('show_feedbk.started', show_feedbk.tStartRefresh)
    trials.addOtherData('show_feedbk.stopped', show_feedbk.tStopRefresh)
    thisExp.nextEntry()
    
# all staircases completed


# Flip one final time so any remaining win.callOnFlip() 
# and win.timeOnFlip() tasks get executed before quitting
win.flip()

# these shouldn't be strictly necessary (should auto-save)
thisExp.saveAsWideText(filename+'.csv', delim='auto')
thisExp.saveAsPickle(filename)
logging.flush()
# make sure everything is closed down
if eyetracker:
    eyetracker.setConnectionState(False)
thisExp.abort()  # or data files will save again on exit
win.close()
core.quit()
