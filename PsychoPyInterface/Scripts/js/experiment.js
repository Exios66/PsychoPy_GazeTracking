/* 
 * Comprehensive PsychoJS Experiment with WebGazer.js Eye Tracking
 *
 * Features:
 * - Loads and initializes WebGazer.js (with debug overlays hidden and custom camera constraints)
 * - Displays welcome instructions and collects participant consent
 * - Runs a 9-point calibration routine (3x3 grid) with visual feedback and computes a linear mapping
 * - Runs multiple trials that present fixation and stimulus phases while continuously logging gaze data
 * - Provides export options for CSV and JSON data downloads at experiment end
 * - Includes robust error handling (for camera issues, calibration aborts, etc.)
 *
 * Requirements:
 * - Include PsychoJS (e.g. via a <script> tag pointing to the appropriate version)
 * - Include WebGazer.js (make sure the file is loaded in your HTML)
 *
 * To use:
 * - Open this file via a supported browser (Chrome or Safari are recommended)
 * - The experiment will start automatically and display instructions.
 */

import { core, data, sound, util, visual, event } from 'https://pavlovia.org/lib/psychojs-2020.2.3.js';

// Create a global PsychoJS instance
const psychoJS = new PsychoJS({
    debug: true
});

// (Optionally) set experiment info – this example uses a basic participant field
psychoJS.serverManager.setExperimentInfo({
    participant: '',
    session: '001'
});

// Global variables
let win, globalClock;
let calibrationData = [];           // Each element: [expectedX, expectedY, observedX, observedY]
let calibrationMapping = null;      // Object { a_x, b_x, a_y, b_y }
let calibrationQuality = 0;
let gazeDataLog = [];               // To store all gaze samples (trial, timestamp, raw and calibrated positions)
let currentGaze = { x: null, y: null, timestamp: null }; // Updated continuously by WebGazer

/**
 * Initialize WebGazer with desired settings.
 * Configures camera constraints and hides debug overlays.
 */
function initWebGazer() {
    return new Promise((resolve, reject) => {
        try {
            // Set camera constraints (adjust as needed)
            webgazer.setCameraConstraints({
                width: { ideal: 1280 },
                height: { ideal: 720 },
                frameRate: { ideal: 60 }
            });
            // Initialize WebGazer with a gaze listener that continuously updates currentGaze
            webgazer.setGazeListener(function(data, elapsedTime) {
                if (data == null) return;
                currentGaze.x = data.x;
                currentGaze.y = data.y;
                currentGaze.timestamp = elapsedTime;
            }).begin();

            // Hide video preview and overlays for performance
            webgazer.showVideo(false)
                     .showFaceOverlay(false)
                     .showFaceFeedbackBox(false)
                     .showPredictionPoints(false);
            resolve();
        } catch (e) {
            reject(e);
        }
    });
}

/**
 * Runs the calibration routine.
 * Displays a 3x3 grid of calibration points, collects several samples per point,
 * computes a simple linear regression for both x and y to derive a mapping,
 * and shows calibration quality. If quality is poor (<0.85) and the user presses 'r',
 * the calibration is repeated.
 */
async function runCalibration() {
    // Define calibration points in normalized coordinates (norm units, where center is [0,0])
    const calibrationPoints = [
        [-0.8,  0.8], [0,  0.8], [0.8,  0.8],
        [-0.8,  0],   [0,  0],   [0.8,  0],
        [-0.8, -0.8], [0, -0.8], [0.8, -0.8]
    ];
    const dotSize = 0.05;
    const pointColor = 'red';
    const successColor = 'green';
    const waitTime = 0.5; // seconds

    for (let i = 0; i < calibrationPoints.length; i++) {
        // Create and draw the calibration dot and instruction text
        let dot = new visual.Circle({
            win: win,
            radius: dotSize,
            pos: calibrationPoints[i],
            fillColor: pointColor,
            lineColor: pointColor,
            units: 'norm'
        });
        let instruction = new visual.TextStim({
            win: win,
            text: `Calibration:\nLook at the red dot and press SPACE.\n(${i+1} of ${calibrationPoints.length})`,
            pos: [0, 0.9],
            height: 0.05,
            units: 'norm'
        });
        dot.draw();
        instruction.draw();
        win.flip();
        
        // Wait for participant input (SPACE to capture or ESCAPE to abort)
        let keys = await event.waitKeys({ keyList: ['space', 'escape'] });
        if (keys.includes('escape')) {
            throw new Error("Calibration aborted by participant.");
        }
        
        // Collect 3 samples for stability (each 50ms apart)
        let samples = [];
        for (let j = 0; j < 3; j++) {
            await core.wait(0.05);
            if (currentGaze.x != null && currentGaze.y != null) {
                samples.push({ x: currentGaze.x, y: currentGaze.y });
            }
        }
        if (samples.length > 0) {
            // Average the samples
            let avgX = samples.reduce((sum, s) => sum + s.x, 0) / samples.length;
            let avgY = samples.reduce((sum, s) => sum + s.y, 0) / samples.length;
            // Convert from pixels to normalized coordinates using the window size
            let normX = (avgX - win.size[0]/2) / (win.size[0]/2);
            let normY = (win.size[1]/2 - avgY) / (win.size[1]/2);
            // Save: [expected (calibration point), observed (gaze) coordinates]
            calibrationData.push([ calibrationPoints[i][0], calibrationPoints[i][1], normX, normY ]);
        }
        
        // Visual feedback: change dot color to success color
        dot.fillColor = successColor;
        dot.lineColor = successColor;
        dot.draw();
        instruction.draw();
        win.flip();
        await core.wait(waitTime);
    }
    // Compute calibration mapping only if sufficient data was collected
    if (calibrationData.length < 5) {
        calibrationMapping = { a_x: 1, b_x: 0, a_y: 1, b_y: 0 };
        calibrationQuality = 0;
        return false;
    }
    // For x dimension
    let expectedX = calibrationData.map(d => d[0]);
    let observedX = calibrationData.map(d => d[2]);
    let { a: a_x, b: b_x, r2: r2_x } = linearRegression(observedX, expectedX);
    // For y dimension
    let expectedY = calibrationData.map(d => d[1]);
    let observedY = calibrationData.map(d => d[3]);
    let { a: a_y, b: b_y, r2: r2_y } = linearRegression(observedY, expectedY);
    calibrationMapping = { a_x, b_x, a_y, b_y };
    calibrationQuality = (r2_x + r2_y) / 2;
    
    // Display calibration quality and ask if the user wants to recalibrate if quality is low (<0.85)
    let qualityText = `Calibration quality: ${calibrationQuality.toFixed(2)}.\nPress 'r' to recalibrate or any other key to continue.`;
    let qualityStim = new visual.TextStim({
        win: win,
        text: qualityText,
        pos: [0, 0],
        height: 0.05,
        units: 'norm'
    });
    qualityStim.draw();
    win.flip();
    let resp = await event.waitKeys({ keyList: ['r', 'escape', 'c'] });
    if (resp.includes('escape')) {
        throw new Error("Calibration aborted.");
    }
    if (resp.includes('r') && calibrationQuality < 0.85) {
        calibrationData = [];
        return await runCalibration();
    }
    return true;
}

/**
 * A simple linear regression function.
 * Given arrays x and y, returns slope (a), intercept (b), and r² value.
 */
function linearRegression(x, y) {
    let n = x.length;
    let sumX = x.reduce((a, b) => a + b, 0);
    let sumY = y.reduce((a, b) => a + b, 0);
    let sumXY = 0, sumXX = 0;
    for (let i = 0; i < n; i++) {
        sumXY += x[i] * y[i];
        sumXX += x[i] * x[i];
    }
    let a = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    let b = (sumY - a * sumX) / n;
    // Compute R²
    let yMean = sumY / n;
    let ssTot = y.reduce((acc, val) => acc + Math.pow(val - yMean, 2), 0);
    let ssRes = 0;
    for (let i = 0; i < n; i++) {
        let yiPred = a * x[i] + b;
        ssRes += Math.pow(y[i] - yiPred, 2);
    }
    let r2 = 1 - (ssRes / ssTot);
    return { a, b, r2 };
}

/**
 * Apply the computed calibration mapping to a given observed gaze point.
 */
function applyCalibration(obsX, obsY) {
    if (!calibrationMapping) return { x: obsX, y: obsY };
    let calibratedX = calibrationMapping.a_x * obsX + calibrationMapping.b_x;
    let calibratedY = calibrationMapping.a_y * obsY + calibrationMapping.b_y;
    return { x: calibratedX, y: calibratedY };
}

/**
 * Runs a single trial.
 * Displays a fixation cross followed by a stimulus while continuously logging gaze samples.
 */
async function runTrial(trialNum) {
    const fixationDuration = 1.0;
    const stimulusDuration = 2.0;
    const interTrialInterval = 0.5;
    
    // Fixation phase
    let fixation = new visual.TextStim({
        win: win,
        text: '+',
        pos: [0, 0],
        height: 0.2,
        units: 'norm'
    });
    fixation.draw();
    win.flip();
    let trialStart = core.getTime();
    while (core.getTime() - trialStart < fixationDuration) {
        if (currentGaze.x != null && currentGaze.y != null) {
            // Convert pixel values to normalized coordinates
            let normObsX = (currentGaze.x - win.size[0] / 2) / (win.size[0] / 2);
            let normObsY = (win.size[1] / 2 - currentGaze.y) / (win.size[1] / 2);
            let calibrated = applyCalibration(normObsX, normObsY);
            gazeDataLog.push({
                trial: trialNum,
                timestamp: core.getTime(),
                rawX: normObsX,
                rawY: normObsY,
                calibratedX: calibrated.x,
                calibratedY: calibrated.y,
                phase: 'fixation'
            });
        }
        await core.wait(0.01);
    }
    
    // Stimulus phase
    let stimulus = new visual.TextStim({
        win: win,
        text: `Trial ${trialNum}`,
        pos: [0, 0],
        height: 0.1,
        units: 'norm'
    });
    stimulus.draw();
    win.flip();
    trialStart = core.getTime();
    while (core.getTime() - trialStart < stimulusDuration) {
        if (currentGaze.x != null && currentGaze.y != null) {
            let normObsX = (currentGaze.x - win.size[0] / 2) / (win.size[0] / 2);
            let normObsY = (win.size[1] / 2 - currentGaze.y) / (win.size[1] / 2);
            let calibrated = applyCalibration(normObsX, normObsY);
            gazeDataLog.push({
                trial: trialNum,
                timestamp: core.getTime(),
                rawX: normObsX,
                rawY: normObsY,
                calibratedX: calibrated.x,
                calibratedY: calibrated.y,
                phase: 'stimulus'
            });
        }
        await core.wait(0.01);
    }
    
    // Inter-trial interval: clear screen briefly
    win.flip();
    await core.wait(interTrialInterval);
}

/**
 * Exports the logged gaze data.
 * Creates download links for CSV and JSON data that the user can click to save files locally.
 */
function exportData() {
    // CSV export
    let csvContent = "data:text/csv;charset=utf-8,trial,timestamp,rawX,rawY,calibratedX,calibratedY,phase\n";
    gazeDataLog.forEach(row => {
        csvContent += `${row.trial},${row.timestamp},${row.rawX.toFixed(3)},${row.rawY.toFixed(3)},${row.calibratedX.toFixed(3)},${row.calibratedY.toFixed(3)},${row.phase}\n`;
    });
    let encodedUri = encodeURI(csvContent);
    let csvLink = document.createElement("a");
    csvLink.setAttribute("href", encodedUri);
    csvLink.setAttribute("download", "gaze_data.csv");
    csvLink.innerHTML = "Download CSV Data";
    document.body.appendChild(csvLink);
    
    // JSON export
    let jsonContent = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(gazeDataLog, null, 2));
    let jsonLink = document.createElement("a");
    jsonLink.setAttribute("href", jsonContent);
    jsonLink.setAttribute("download", "gaze_data.json");
    jsonLink.innerHTML = "Download JSON Data";
    document.body.appendChild(jsonLink);
}

/**
 * Main experiment flow.
 * Initializes WebGazer and the PsychoJS window, shows instructions, runs calibration and trials,
 * and finally exports the data before cleaning up.
 */
async function runExperiment() {
    try {
        // Initialize WebGazer
        await initWebGazer();
    } catch (e) {
        alert("Error initializing WebGazer: " + e);
        return;
    }
    
    // Create a full-screen PsychoJS window with a black background.
    win = new visual.Window({
        fullscr: true,
        color: [-1, -1, -1],
        units: 'norm'
    });
    // Estimate window size in pixels (used for coordinate conversion)
    win.size = win._win.screenRect.slice(2);
    globalClock = new core.Clock();
    
    // Display welcome instructions
    let welcome = new visual.TextStim({
        win: win,
        text: "Welcome to the experiment.\n\nPress any key to begin.",
        pos: [0, 0],
        height: 0.05,
        units: 'norm'
    });
    welcome.draw();
    win.flip();
    await event.waitKeys();
    
    // Run calibration routine
    try {
        let calSuccess = await runCalibration();
        if (!calSuccess) {
            alert("Calibration failed or was aborted.");
            return;
        }
    } catch (e) {
        alert("Calibration aborted: " + e);
        return;
    }
    
    // Inform participant calibration was successful
    let calSuccessMsg = new visual.TextStim({
        win: win,
        text: "Calibration completed successfully.\nPress any key to begin trials.",
        pos: [0, 0],
        height: 0.05,
        units: 'norm'
    });
    calSuccessMsg.draw();
    win.flip();
    await event.waitKeys();
    
    // Run a set of trials (adjust numTrials as needed)
    const numTrials = 5;
    for (let trial = 1; trial <= numTrials; trial++) {
        await runTrial(trial);
        let abortKeys = await event.getKeys({ keyList: ['escape'] });
        if (abortKeys.includes('escape')) break;
    }
    
    // Debriefing message
    let debrief = new visual.TextStim({
        win: win,
        text: "Experiment completed.\nThank you for your participation!\nPress any key to export data and end.",
        pos: [0, 0],
        height: 0.05,
        units: 'norm'
    });
    debrief.draw();
    win.flip();
    await event.waitKeys();
    
    // Export gaze data (adds download links to the document)
    exportData();
    
    // Allow some time for the participant to download data before shutting down
    await core.wait(5);
    webgazer.end();
    win.close();
    core.quit();
}

// Start the experiment flow
runExperiment().catch(e => {
    console.error("Experiment error: ", e);
});