#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
WebGazer.js bridge for PsychoPy.

This module provides functions for integrating PsychoPy with WebGazer.js
via a websocket connection.
"""

import json
import asyncio
import websockets
import threading
import time
from pathlib import Path
from datetime import datetime

from ..config import DATA_DIR


class WebGazerBridge:
    """Bridge between PsychoPy and WebGazer.js."""

    def __init__(self, session_id=None, host="localhost", port=8765, save_locally=True):
        """
        Initialize the WebGazer bridge.

        Parameters
        ----------
        session_id : str, optional
            The session ID for data storage. If None, a timestamp will be used.
        host : str, optional
            The websocket host. Default is "localhost".
        port : int, optional
            The websocket port. Default is 8765.
        save_locally : bool, optional
            Whether to save data locally. Default is True.
        """
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.host = host
        self.port = port
        self.save_locally = save_locally
        self.server = None
        self.server_thread = None
        self.is_running = False
        self.connected_clients = set()
        self.gaze_data = []
        self.on_gaze_callback = None

    async def _handle_client(self, websocket, path):
        """
        Handle a client connection.

        Parameters
        ----------
        websocket : websockets.WebSocketServerProtocol
            The websocket connection.
        path : str
            The connection path.
        """
        self.connected_clients.add(websocket)
        try:
            # Send session ID to client
            await websocket.send(json.dumps({
                "type": "session_info",
                "session_id": self.session_id
            }))
            
            # Handle messages from client
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get("type") == "gaze_data":
                        # Process gaze data
                        gaze_point = {
                            "timestamp": time.time(),
                            "x": data.get("x"),
                            "y": data.get("y"),
                            "session_id": self.session_id,
                            "screen_width": data.get("screen_width"),
                            "screen_height": data.get("screen_height")
                        }
                        
                        self.gaze_data.append(gaze_point)
                        
                        # Call callback if registered
                        if self.on_gaze_callback:
                            self.on_gaze_callback(gaze_point)
                    
                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {message}")
        
        finally:
            self.connected_clients.remove(websocket)

    def start(self):
        """Start the WebGazer bridge server."""
        if self.is_running:
            return
        
        # Define server coroutine
        async def run_server():
            self.server = await websockets.serve(
                self._handle_client, self.host, self.port
            )
            print(f"WebGazer bridge server started at ws://{self.host}:{self.port}")
            await self.server.wait_closed()
        
        # Run server in a separate thread
        def run_asyncio_loop():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_server())
        
        self.server_thread = threading.Thread(target=run_asyncio_loop, daemon=True)
        self.server_thread.start()
        self.is_running = True
        self.gaze_data = []

    def stop(self):
        """Stop the WebGazer bridge server."""
        if not self.is_running:
            return
        
        # Close all client connections
        if self.connected_clients:
            asyncio.run(self._close_connections())
        
        # Close server
        if self.server:
            self.server.close()
            asyncio.run(self.server.wait_closed())
        
        self.is_running = False
        
        # Save data
        if self.save_locally and self.gaze_data:
            self._save_data_locally()

    async def _close_connections(self):
        """Close all client connections."""
        if not self.connected_clients:
            return
        
        close_tasks = [client.close() for client in self.connected_clients]
        await asyncio.gather(*close_tasks, return_exceptions=True)

    def _save_data_locally(self):
        """Save recorded data to a local file."""
        if not self.gaze_data:
            return
            
        # Create session directory
        session_dir = DATA_DIR / self.session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Save data to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = session_dir / f"webgazer_data_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.gaze_data, f, indent=2)
            
        print(f"Saved {len(self.gaze_data)} WebGazer data points to {filename}")

    def send_message(self, message_type, data=None):
        """
        Send a message to all connected clients.

        Parameters
        ----------
        message_type : str
            The type of message to send.
        data : dict, optional
            Additional data to include in the message.
        """
        if not self.is_running or not self.connected_clients:
            return
        
        message = {
            "type": message_type
        }
        
        if data:
            message.update(data)
        
        # Send message to all clients
        asyncio.run(self._broadcast_message(json.dumps(message)))

    async def _broadcast_message(self, message):
        """
        Broadcast a message to all connected clients.

        Parameters
        ----------
        message : str
            The message to broadcast.
        """
        if not self.connected_clients:
            return
        
        send_tasks = [client.send(message) for client in self.connected_clients]
        await asyncio.gather(*send_tasks, return_exceptions=True)

    def register_gaze_callback(self, callback):
        """
        Register a callback function for gaze data.

        Parameters
        ----------
        callback : callable
            The callback function to call when gaze data is received.
            The function should accept a single argument, which is the gaze data point.
        """
        self.on_gaze_callback = callback

    def get_client_html(self):
        """
        Get HTML code for the client to connect to the WebGazer bridge.

        Returns
        -------
        str
            HTML code for the client.
        """
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>WebGazer Bridge</title>
            <script src="https://webgazer.cs.brown.edu/webgazer.js"></script>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                    text-align: center;
                }}
                #status {{
                    margin: 20px 0;
                    padding: 10px;
                    border-radius: 5px;
                }}
                .connected {{
                    background-color: #d4edda;
                    color: #155724;
                }}
                .disconnected {{
                    background-color: #f8d7da;
                    color: #721c24;
                }}
                .calibrating {{
                    background-color: #fff3cd;
                    color: #856404;
                }}
                #video-container {{
                    position: relative;
                    margin: 0 auto;
                    width: 320px;
                    height: 240px;
                }}
                #webgazerVideoFeed {{
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                }}
                .calibration-point {{
                    position: absolute;
                    width: 20px;
                    height: 20px;
                    border-radius: 50%;
                    background-color: red;
                    cursor: pointer;
                }}
                button {{
                    margin: 10px;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    background-color: #007bff;
                    color: white;
                    cursor: pointer;
                }}
                button:disabled {{
                    background-color: #cccccc;
                }}
            </style>
        </head>
        <body>
            <h1>WebGazer Bridge</h1>
            
            <div id="status" class="disconnected">Disconnected</div>
            
            <div id="video-container">
                <video id="webgazerVideoFeed" autoplay></video>
            </div>
            
            <div id="calibration-container" style="display: none;">
                <h2>Calibration</h2>
                <p>Click on each point to calibrate</p>
                <div id="calibration-points"></div>
            </div>
            
            <div id="controls">
                <button id="start-btn">Start WebGazer</button>
                <button id="calibrate-btn" disabled>Calibrate</button>
                <button id="connect-btn" disabled>Connect to PsychoPy</button>
                <button id="stop-btn" disabled>Stop</button>
            </div>
            
            <script>
                // WebSocket connection
                let socket = null;
                let isTracking = false;
                let sessionId = null;
                
                // DOM elements
                const statusEl = document.getElementById('status');
                const startBtn = document.getElementById('start-btn');
                const calibrateBtn = document.getElementById('calibrate-btn');
                const connectBtn = document.getElementById('connect-btn');
                const stopBtn = document.getElementById('stop-btn');
                const calibrationContainer = document.getElementById('calibration-container');
                const calibrationPoints = document.getElementById('calibration-points');
                
                // Initialize WebGazer
                startBtn.addEventListener('click', async () => {{
                    try {{
                        await webgazer.setGazeListener(() => {{}}).begin();
                        webgazer.showVideoPreview(true).showPredictionPoints(true);
                        
                        startBtn.disabled = true;
                        calibrateBtn.disabled = false;
                        
                        statusEl.textContent = 'WebGazer initialized';
                        statusEl.className = 'calibrating';
                    }} catch (error) {{
                        console.error('Error starting WebGazer:', error);
                        statusEl.textContent = 'Error: ' + error.message;
                        statusEl.className = 'disconnected';
                    }}
                }});
                
                // Calibration
                calibrateBtn.addEventListener('click', () => {{
                    calibrationContainer.style.display = 'block';
                    createCalibrationPoints();
                }});
                
                function createCalibrationPoints() {{
                    // Clear existing points
                    calibrationPoints.innerHTML = '';
                    
                    // Create 9 calibration points
                    const positions = [
                        {{x: '10%', y: '10%'}}, {{x: '50%', y: '10%'}}, {{x: '90%', y: '10%'}},
                        {{x: '10%', y: '50%'}}, {{x: '50%', y: '50%'}}, {{x: '90%', y: '50%'}},
                        {{x: '10%', y: '90%'}}, {{x: '50%', y: '90%'}}, {{x: '90%', y: '90%'}}
                    ];
                    
                    let pointsClicked = 0;
                    
                    positions.forEach((pos, index) => {{
                        const point = document.createElement('div');
                        point.className = 'calibration-point';
                        point.style.left = pos.x;
                        point.style.top = pos.y;
                        
                        point.addEventListener('click', () => {{
                            point.style.backgroundColor = 'green';
                            pointsClicked++;
                            
                            if (pointsClicked === positions.length) {{
                                // Calibration complete
                                setTimeout(() => {{
                                    calibrationContainer.style.display = 'none';
                                    connectBtn.disabled = false;
                                    statusEl.textContent = 'Calibration complete';
                                }}, 1000);
                            }}
                        }});
                        
                        calibrationPoints.appendChild(point);
                    }});
                }}
                
                // Connect to PsychoPy
                connectBtn.addEventListener('click', () => {{
                    connectToServer();
                }});
                
                function connectToServer() {{
                    socket = new WebSocket('ws://{self.host}:{self.port}');
                    
                    socket.onopen = () => {{
                        statusEl.textContent = 'Connected to PsychoPy';
                        statusEl.className = 'connected';
                        connectBtn.disabled = true;
                        stopBtn.disabled = false;
                        
                        // Start sending gaze data
                        startGazeTracking();
                    }};
                    
                    socket.onmessage = (event) => {{
                        try {{
                            const message = JSON.parse(event.data);
                            
                            if (message.type === 'session_info') {{
                                sessionId = message.session_id;
                                console.log('Session ID:', sessionId);
                            }}
                        }} catch (error) {{
                            console.error('Error parsing message:', error);
                        }}
                    }};
                    
                    socket.onclose = () => {{
                        statusEl.textContent = 'Disconnected from PsychoPy';
                        statusEl.className = 'disconnected';
                        connectBtn.disabled = false;
                        stopBtn.disabled = true;
                        
                        // Stop tracking
                        stopGazeTracking();
                    }};
                    
                    socket.onerror = (error) => {{
                        console.error('WebSocket error:', error);
                        statusEl.textContent = 'Connection error';
                        statusEl.className = 'disconnected';
                    }};
                }}
                
                function startGazeTracking() {{
                    if (isTracking) return;
                    
                    isTracking = true;
                    
                    webgazer.setGazeListener((data, timestamp) => {{
                        if (data == null || !socket || socket.readyState !== WebSocket.OPEN) return;
                        
                        // Send gaze data to server
                        socket.send(JSON.stringify({{
                            type: 'gaze_data',
                            x: data.x,
                            y: data.y,
                            timestamp: timestamp,
                            screen_width: window.innerWidth,
                            screen_height: window.innerHeight
                        }}));
                    }});
                }}
                
                function stopGazeTracking() {{
                    if (!isTracking) return;
                    
                    isTracking = false;
                    webgazer.setGazeListener(() => {{}});
                }}
                
                // Stop tracking and disconnect
                stopBtn.addEventListener('click', () => {{
                    if (socket) {{
                        socket.close();
                    }}
                    
                    stopGazeTracking();
                    
                    statusEl.textContent = 'Stopped';
                    statusEl.className = 'disconnected';
                    connectBtn.disabled = false;
                    stopBtn.disabled = true;
                }});
                
                // Handle page unload
                window.addEventListener('beforeunload', () => {{
                    if (socket) {{
                        socket.close();
                    }}
                    
                    if (webgazer.isReady()) {{
                        webgazer.end();
                    }}
                }});
            </script>
        </body>
        </html>
        """
        return html

    def save_client_html(self, filename=None):
        """
        Save the client HTML to a file.

        Parameters
        ----------
        filename : str or Path, optional
            The filename to save to. If None, a default name will be used.

        Returns
        -------
        Path
            The path to the saved file.
        """
        if filename is None:
            # Create resources directory
            resources_dir = Path(__file__).parent.parent / "resources"
            resources_dir.mkdir(parents=True, exist_ok=True)
            
            filename = resources_dir / "webgazer_client.html"
        
        with open(filename, 'w') as f:
            f.write(self.get_client_html())
        
        print(f"Saved WebGazer client HTML to {filename}")
        return filename 