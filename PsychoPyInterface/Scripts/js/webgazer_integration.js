// Scripts/webgazer_integration.js

// Wait until the window has loaded
window.onload = function() {
    // Set this flag if you want each session to be independent.
    window.saveDataAcrossSessions = false;

    // Begin data collection as early as possible
    webgazer.begin();

    // Optionally, set the tracker or regression modules (uncomment and change as needed)
    // webgazer.setTracker("TFFacemesh");
    // webgazer.setRegression("ridge");

    // Set up the gaze listener callback – this is called every few milliseconds.
    webgazer.setGazeListener(function(data, elapsedTime) {
        if (data == null) {
            return;
        }
        // The x and y coordinates are relative to the viewport.
        var xprediction = data.x;
        var yprediction = data.y;
        console.log("Elapsed Time: " + elapsedTime + " ms, X: " + xprediction + ", Y: " + yprediction);
    });

    // Optionally display the video preview and prediction points on screen.
    webgazer.showVideoPreview(true);
    webgazer.showPredictionPoints(true);

    // If you want to bind the video element to a container on your page:
    var videoContainer = document.getElementById("webgazerVideoContainer");
    if (videoContainer) {
        // Note: WebGazer automatically creates its video element,
        // so you may need to adjust CSS or reposition it as desired.
        webgazer.params.videoElement = videoContainer;
    }

    // Add key event listeners for pausing (p) and resuming (r) data collection.
    document.addEventListener("keydown", function(event) {
        if (event.key === "p") {
            console.log("Pausing WebGazer...");
            webgazer.pause();
        }
        if (event.key === "r") {
            console.log("Resuming WebGazer...");
            webgazer.resume();
        }
    });

    // Expose a function to get the current prediction on demand.
    window.getCurrentGazePrediction = function() {
        var prediction = webgazer.getCurrentPrediction();
        if (prediction) {
            console.log("Current Prediction - X: " + prediction.x + ", Y: " + prediction.y);
        } else {
            console.log("No prediction available at this time.");
        }
    };
};