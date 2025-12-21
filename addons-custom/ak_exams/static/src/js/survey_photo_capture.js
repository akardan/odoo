// Survey Photo Capture Module - Plain JavaScript
console.log("Survey Photo Capture Module Loaded");

class SurveyPhotoCapture {
    constructor(accessToken, config) {
        this.accessToken = accessToken;
        this.config = {
            mode: config.mode || 'disabled', // 'disabled', 'optional', 'mandatory'
            minInterval: config.minInterval || 120000, // 2 minutes in ms
            maxInterval: config.maxInterval || 600000, // 10 minutes in ms
            captureInitial: config.captureInitial || true
        };
        this.stream = null;
        this.videoElement = null;
        this.captureTimer = null;
        this.permissionGranted = false;
    }
    
    /**
     * Request camera permission
     */
    async requestCameraPermission() {
        try {
            console.log('ak_exams: Requesting camera permission...');
            
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                },
                audio: false
            });
            
            this.permissionGranted = true;
            console.log('ak_exams: Camera permission granted');
            
            // Update permission status on server
            await this.updatePermissionStatus(true);
            
            return true;
            
        } catch (error) {
            console.error('ak_exams: Camera permission denied:', error);
            this.permissionGranted = false;
            
            // Update permission status on server
            await this.updatePermissionStatus(false);
            
            if (this.config.mode === 'mandatory') {
                this.showPermissionDeniedModal();
            }
            
            return false;
        }
    }
    
    /**
     * Update camera permission status on server
     */
    async updatePermissionStatus(granted) {
        try {
            const response = await fetch('/survey/photo/permission', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        access_token: this.accessToken,
                        permission_granted: granted
                    }
                })
            });
            
            const data = await response.json();
            console.log('ak_exams: Permission status updated:', data);
            
        } catch (error) {
            console.error('ak_exams: Error updating permission status:', error);
        }
    }
    
    /**
     * Capture photo from camera
     */
    async capturePhoto(captureType = 'random') {
        if (!this.permissionGranted || !this.stream) {
            console.warn('ak_exams: Cannot capture photo: permission not granted or stream not available');
            return null;
        }
        
        try {
            // Create hidden video element if not exists
            if (!this.videoElement) {
                this.videoElement = document.createElement('video');
                this.videoElement.style.display = 'none';
                this.videoElement.autoplay = true;
                this.videoElement.srcObject = this.stream;
                document.body.appendChild(this.videoElement);
                
                // Wait for video to be ready
                await new Promise(resolve => {
                    this.videoElement.onloadedmetadata = resolve;
                });
            }
            
            // Create canvas to capture frame
            const canvas = document.createElement('canvas');
            canvas.width = this.videoElement.videoWidth;
            canvas.height = this.videoElement.videoHeight;
            
            const context = canvas.getContext('2d');
            context.drawImage(this.videoElement, 0, 0, canvas.width, canvas.height);
            
            // Convert to base64
            const photoData = canvas.toDataURL('image/jpeg', 0.8);
            
            console.log(`ak_exams: Photo captured (${captureType}), size: ${photoData.length} bytes`);
            
            // Send to server
            await this.sendPhotoToServer(photoData, captureType);
            
            return photoData;
            
        } catch (error) {
            console.error('ak_exams: Error capturing photo:', error);
            return null;
        }
    }
    
    /**
     * Send captured photo to server
     */
    async sendPhotoToServer(photoData, captureType) {
        try {
            const response = await fetch('/survey/photo/capture', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        access_token: this.accessToken,
                        photo_data: photoData,
                        capture_type: captureType
                    }
                })
            });
            
            const data = await response.json();
            
            if (data.result && data.result.success) {
                console.log('ak_exams: Photo sent successfully:', data.result.photo_id);
            } else {
                console.error('ak_exams: Failed to send photo:', data.result?.error || 'Unknown error');
            }
            
        } catch (error) {
            console.error('ak_exams: Error sending photo to server:', error);
        }
    }
    
    /**
     * Start random photo capture
     */
    startRandomCapture() {
        if (!this.permissionGranted) {
            console.warn('ak_exams: Cannot start random capture: permission not granted');
            return;
        }
        
        const scheduleNextCapture = () => {
            // Calculate random interval
            const interval = Math.floor(
                Math.random() * (this.config.maxInterval - this.config.minInterval) + 
                this.config.minInterval
            );
            
            console.log(`ak_exams: Next photo capture scheduled in ${interval / 1000} seconds`);
            
            this.captureTimer = setTimeout(async () => {
                await this.capturePhoto('random');
                scheduleNextCapture(); // Schedule next capture
            }, interval);
        };
        
        scheduleNextCapture();
    }
    
    /**
     * Stop random photo capture
     */
    stopRandomCapture() {
        if (this.captureTimer) {
            clearTimeout(this.captureTimer);
            this.captureTimer = null;
            console.log('ak_exams: Random photo capture stopped');
        }
    }
    
    /**
     * Release camera resources
     */
    releaseCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        if (this.videoElement) {
            this.videoElement.remove();
            this.videoElement = null;
        }
        
        this.stopRandomCapture();
        console.log('ak_exams: Camera resources released');
    }
    
    /**
     * Show permission denied modal (for mandatory mode)
     */
    showPermissionDeniedModal() {
        const overlay = document.createElement('div');
        overlay.id = 'camera-permission-denied-overlay';
        Object.assign(overlay.style, {
            position: 'fixed',
            top: '0',
            left: '0',
            width: '100vw',
            height: '100vh',
            backgroundColor: 'rgba(0,0,0,0.95)',
            zIndex: '200000',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            color: 'white',
            textAlign: 'center'
        });
        
        overlay.innerHTML = `
            <div style="background: #fff; color: #333; padding: 40px; border-radius: 8px; 
                        box-shadow: 0 5px 20px rgba(0,0,0,0.3); max-width: 500px;">
                <i class="fa fa-camera" style="font-size: 48px; color: #dc3545; margin-bottom: 20px;"></i>
                <h2>Camera Permission Required</h2>
                <p style="font-size: 1.1em; margin-top: 15px;">
                    This exam requires camera access for identity verification. 
                    You cannot start the exam without granting camera permission.
                </p>
                <p style="font-size: 0.9em; margin-top: 20px; color: #777;">
                    Please refresh the page and allow camera access when prompted.
                </p>
                <button onclick="location.reload()" 
                        style="margin-top: 20px; padding: 10px 20px; font-size: 1em; 
                               background-color: #007bff; color: white; border: none; 
                               border-radius: 5px; cursor: pointer;">
                    Refresh Page
                </button>
            </div>
        `;
        
        document.body.appendChild(overlay);
    }
    
    /**
     * Show permission warning message (for optional mode)
     */
    showPermissionWarningMessage() {
        const warningDiv = document.createElement('div');
        warningDiv.id = 'camera-permission-warning';
        Object.assign(warningDiv.style, {
            position: 'fixed',
            top: '20px',
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: '#fff3cd',
            color: '#856404',
            padding: '15px 20px',
            borderRadius: '5px',
            border: '1px solid #ffeaa7',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
            zIndex: '100000',
            maxWidth: '500px',
            textAlign: 'center'
        });
        
        warningDiv.innerHTML = `
            <i class="fa fa-exclamation-triangle" style="margin-right: 10px;"></i>
            <strong>Warning:</strong> Camera permission was denied. 
            Photo verification will not be available for this exam.
        `;
        
        document.body.appendChild(warningDiv);
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            warningDiv.style.transition = 'opacity 0.5s';
            warningDiv.style.opacity = '0';
            setTimeout(() => warningDiv.remove(), 500);
        }, 10000);
    }
}

// Initialize photo capture on exam start screen
async function initializePhotoCapture() {
    console.log('ak_exams: Initializing photo capture...');
    const formElement = document.querySelector('form.o_survey_form, form[data-photo-capture-mode]');
    
    if (!formElement) {
        console.log('ak_exams: Form element not found for photo capture');
        return;
    }
    
    const photoCaptureMode = formElement.getAttribute('data-photo-capture-mode') || 'disabled';
    const isStartScreen = formElement.getAttribute('data-is-start-screen') === 'true';
    
    // Only proceed if on start screen and photo capture is enabled
    if (!isStartScreen || photoCaptureMode === 'disabled') {
        console.log('ak_exams: Not on start screen or photo capture disabled');
        return;
    }
    
    const photoCaptureConfig = {
        mode: photoCaptureMode,
        minInterval: parseInt(formElement.getAttribute('data-photo-capture-min-interval') || '120') * 1000,
        maxInterval: parseInt(formElement.getAttribute('data-photo-capture-max-interval') || '600') * 1000,
        captureInitial: formElement.getAttribute('data-photo-capture-initial') === 'true'
    };
    
    const accessToken = formElement.getAttribute('data-access-token');
    
    if (!accessToken) {
        console.error('ak_exams: Access token not found');
        return;
    }
    
    console.log('ak_exams: Photo capture enabled on start screen, config:', photoCaptureConfig);
    
    const photoCapture = new SurveyPhotoCapture(accessToken, photoCaptureConfig);
    
    // Store instance globally for cleanup
    window.surveyPhotoCapture = photoCapture;
    
    // Find start button
    const startButton = formElement.querySelector('button[type="submit"][value="start"]');
    
    if (!startButton) {
        console.warn('ak_exams: Start button not found');
        return;
    }
    
    // Disable start button initially while requesting permission
    startButton.disabled = true;
    const originalButtonText = startButton.textContent;
    startButton.textContent = 'Requesting camera permission...';
    
    // Request camera permission immediately on page load
    console.log('ak_exams: Requesting camera permission on start screen...');
    const permissionGranted = await photoCapture.requestCameraPermission();
    
    if (permissionGranted) {
        // Permission granted - enable start button
        startButton.disabled = false;
        startButton.textContent = originalButtonText;
        console.log('ak_exams: Camera permission granted, start button enabled');
        
        // Add click handler for start button
        startButton.addEventListener('click', async function(e) {
            console.log('ak_exams: Start button clicked, beginning exam...');
            
            // Capture initial photo if enabled
            if (photoCaptureConfig.captureInitial) {
                // Wait for form submission to complete, then capture
                setTimeout(async () => {
                    await photoCapture.capturePhoto('initial');
                    
                    // Start random captures
                    photoCapture.startRandomCapture();
                }, 1000);
            } else {
                // Just start random captures
                setTimeout(() => {
                    photoCapture.startRandomCapture();
                }, 1000);
            }
        });
        
    } else {
        // Permission denied
        if (photoCaptureConfig.mode === 'mandatory') {
            // Mandatory mode - keep button disabled and show error
            startButton.disabled = true;
            startButton.textContent = 'Camera Permission Required';
            console.log('ak_exams: Camera permission denied (mandatory) - start button disabled');
            
            // Show error modal
            photoCapture.showPermissionDeniedModal();
            
        } else {
            // Optional mode - enable button with warning
            startButton.disabled = false;
            startButton.textContent = originalButtonText + ' (No Camera)';
            console.log('ak_exams: Camera permission denied (optional) - start button enabled with warning');
            
            // Show warning message
            photoCapture.showPermissionWarningMessage();
        }
    }
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', function() {
        if (window.surveyPhotoCapture) {
            window.surveyPhotoCapture.releaseCamera();
        }
    });
}

// Run immediately if DOM is already loaded, otherwise wait for DOMContentLoaded
if (document.readyState === 'loading') {
    console.log('ak_exams: DOM still loading, waiting for DOMContentLoaded');
    document.addEventListener('DOMContentLoaded', initializePhotoCapture);
} else {
    console.log('ak_exams: DOM already loaded, running photo capture init immediately');
    initializePhotoCapture();
}

// Handle photo capture during exam (non-start screen)
function initializePhotoCaptureForExam() {
    const formElement = document.querySelector('form.o_survey_form');
    
    if (!formElement) return;
    
    const isStartScreen = formElement.getAttribute('data-is-start-screen') === 'true';
    
    // Only proceed if NOT on start screen (i.e., during exam)
    if (isStartScreen) return;
    
    // Check if photo capture instance exists from start screen
    if (window.surveyPhotoCapture && window.surveyPhotoCapture.permissionGranted) {
        console.log('ak_exams: Photo capture active during exam');
        // Random captures are already scheduled from start screen
    }
}

// Run exam photo capture handler
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePhotoCaptureForExam);
} else {
    initializePhotoCaptureForExam();
}
