// Screen Recording Detection and Prevention Attempts
// Note: Complete prevention is not possible, but we can add deterrents and detection

console.log("Screen Recording Detection Script Loaded");

(function() {
    'use strict';
    
    let detectionInterval = null;
    let accessToken = null;
    
    // Function to detect if screen recording might be active (iOS/iPadOS)
    function detectScreenRecording() {
        // Check for iOS/iPadOS screen recording indicators
        // Note: This is limited and may not work on all devices/browsers
        
        // Method 1: Check for media capture state (limited support)
        if (navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia) {
            // Display media API exists - could indicate screen sharing capability
            console.log("ak_exams: Display media API available");
        }
        
        // Method 2: Monitor for suspicious activity patterns
        // Screen recording often causes performance changes
        const now = performance.now();
        if (window.lastPerformanceCheck) {
            const timeDiff = now - window.lastPerformanceCheck;
            // Unusual timing patterns might indicate recording
            if (timeDiff > 5000) { // More than 5 seconds since last check
                console.warn("ak_exams: Unusual timing pattern detected");
            }
        }
        window.lastPerformanceCheck = now;
        
        // Method 3: Check for visibility state changes (recording might trigger these)
        if (document.hidden) {
            console.log("ak_exams: Document is hidden - possible recording or tab switch");
        }
    }
    
    // Function to add visual watermark overlay
    function addWatermarkOverlay() {
        // Remove existing watermark if present
        const existingWatermark = document.getElementById('ak-exam-watermark');
        if (existingWatermark) {
            existingWatermark.remove();
        }
        
        // Create watermark overlay
        const watermark = document.createElement('div');
        watermark.id = 'ak-exam-watermark';
        watermark.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 9999;
            opacity: 0.15;
            background-image: repeating-linear-gradient(
                45deg,
                transparent,
                transparent 100px,
                rgba(255, 0, 0, 0.1) 100px,
                rgba(255, 0, 0, 0.1) 200px
            );
        `;
        
        // Add timestamp and user info to watermark
        const watermarkText = document.createElement('div');
        watermarkText.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) rotate(-45deg);
            font-size: 48px;
            color: rgba(255, 0, 0, 0.2);
            font-weight: bold;
            white-space: nowrap;
            user-select: none;
        `;
        
        // Get user info from form
        const formElement = document.querySelector('form.o_survey_form, form');
        let userInfo = 'EXAM IN PROGRESS';
        
        if (formElement) {
            const emailField = formElement.querySelector('input[name="email"]');
            if (emailField && emailField.value) {
                userInfo = emailField.value;
            }
        }
        
        const timestamp = new Date().toLocaleString('tr-TR');
        watermarkText.textContent = `${userInfo} - ${timestamp}`;
        
        watermark.appendChild(watermarkText);
        document.body.appendChild(watermark);
        
        console.log("ak_exams: Watermark overlay added");
    }
    
    // Function to periodically update watermark with current time
    function updateWatermark() {
        const watermarkText = document.querySelector('#ak-exam-watermark div');
        if (watermarkText) {
            const formElement = document.querySelector('form.o_survey_form, form');
            let userInfo = 'EXAM IN PROGRESS';
            
            if (formElement) {
                const emailField = formElement.querySelector('input[name="email"]');
                if (emailField && emailField.value) {
                    userInfo = emailField.value;
                }
            }
            
            const timestamp = new Date().toLocaleString('tr-TR');
            watermarkText.textContent = `${userInfo} - ${timestamp}`;
        }
    }
    
    // Function to detect iOS/iPadOS
    function isIOSDevice() {
        return /iPad|iPhone|iPod/.test(navigator.userAgent) ||
               (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    }
    
    // Function to detect Android devices
    function isAndroidDevice() {
        return /Android/.test(navigator.userAgent);
    }
    
    // Function to detect mobile devices (iOS or Android)
    function isMobileDevice() {
        return isIOSDevice() || isAndroidDevice();
    }
    
    // Function to show warning about screen recording
    function showScreenRecordingWarning() {
        const warning = document.createElement('div');
        warning.id = 'ak-screen-recording-warning';
        warning.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            background-color: rgba(220, 53, 69, 0.95);
            color: white;
            padding: 15px 30px;
            border-radius: 8px;
            z-index: 10000;
            font-size: 16px;
            font-weight: bold;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 90%;
        `;
        
        if (isIOSDevice()) {
            warning.innerHTML = `
                <div>⚠️ UYARI: EKRAN KAYDI YASAKTIR</div>
                <div style="font-size: 14px; margin-top: 5px;">
                    iPad/iPhone ekran kaydı tespit edilirse sınav geçersiz sayılacaktır.
                </div>
            `;
        } else if (isAndroidDevice()) {
            warning.innerHTML = `
                <div>⚠️ UYARI: EKRAN KAYDI YASAKTIR</div>
                <div style="font-size: 14px; margin-top: 5px;">
                    Android ekran kaydı tespit edilirse sınav geçersiz sayılacaktır.
                </div>
            `;
        } else {
            warning.innerHTML = `
                <div>⚠️ UYARI: EKRAN GÖRÜNTÜSÜ VE KAYDI YASAKTIR</div>
                <div style="font-size: 14px; margin-top: 5px;">
                    Ekran görüntüsü veya kaydı tespit edilirse sınav geçersiz sayılacaktır.
                </div>
            `;
        }
        
        document.body.appendChild(warning);
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            warning.style.transition = 'opacity 1s';
            warning.style.opacity = '0';
            setTimeout(() => warning.remove(), 1000);
        }, 10000);
    }
    
    // Function to capture screenshot of the page
    async function captureScreenshot() {
        try {
            console.log('ak_exams: Attempting to capture screenshot...');
            
            // Use html2canvas library if available, otherwise use native canvas
            if (typeof html2canvas !== 'undefined') {
                const canvas = await html2canvas(document.body, {
                    allowTaint: true,
                    useCORS: true,
                    logging: false,
                    scale: 0.5 // Reduce quality to save bandwidth
                });
                return canvas.toDataURL('image/jpeg', 0.7);
            } else {
                // Fallback: Create a simple canvas with page info
                const canvas = document.createElement('canvas');
                canvas.width = 800;
                canvas.height = 600;
                const ctx = canvas.getContext('2d');
                
                // Fill background
                ctx.fillStyle = '#ffffff';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                
                // Add text info
                ctx.fillStyle = '#000000';
                ctx.font = '20px Arial';
                ctx.fillText('Security Violation Detected', 50, 50);
                ctx.fillText('Time: ' + new Date().toLocaleString('tr-TR'), 50, 100);
                ctx.fillText('URL: ' + window.location.href, 50, 150);
                
                return canvas.toDataURL('image/jpeg', 0.7);
            }
        } catch (error) {
            console.error('ak_exams: Error capturing screenshot:', error);
            return null;
        }
    }
    
    // Function to send screenshot to server
    async function sendScreenshot(violationType) {
        if (!accessToken) {
            console.error("ak_exams: Cannot send screenshot, access_token is missing");
            return;
        }
        
        try {
            const screenshotData = await captureScreenshot();
            
            if (!screenshotData) {
                console.warn('ak_exams: Screenshot capture failed, skipping upload');
                return;
            }
            
            console.log('ak_exams: Sending screenshot to server...');
            
            const response = await fetch('/survey/security/screenshot', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    access_token: accessToken,
                    screenshot_data: screenshotData,
                    violation_type: violationType
                }),
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.result && result.result.success) {
                    console.log('ak_exams: Screenshot uploaded successfully');
                } else {
                    console.error('ak_exams: Screenshot upload failed:', result);
                }
            }
        } catch (error) {
            console.error('ak_exams: Error sending screenshot:', error);
        }
    }
    
    // Function to log screen recording attempt
    async function logScreenRecordingAttempt() {
        if (!accessToken) {
            console.error("ak_exams: Cannot log screen recording attempt, access_token is missing");
            return;
        }
        
        // Determine device type
        let deviceType = 'Desktop';
        if (isIOSDevice()) {
            deviceType = 'iOS/iPadOS';
        } else if (isAndroidDevice()) {
            deviceType = 'Android';
        }
        
        try {
            // First, log the violation
            const response = await fetch('/survey/security/log', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    access_token: accessToken,
                    event_type: 'print_screen_attempt',
                    event_data: {
                        detail: 'screen_recording_suspected',
                        device: deviceType,
                        userAgent: navigator.userAgent
                    }
                }),
            });
            
            if (response.ok) {
                console.log('ak_exams: Screen recording attempt logged');
                
                // Then, capture and send screenshot
                await sendScreenshot('screen_recording_suspected');
            }
        } catch (error) {
            console.error('ak_exams: Error logging screen recording attempt:', error);
        }
    }
    
    // Function to make content harder to record by adding dynamic elements
    function addAntiRecordingMeasures() {
        // Add random position watermarks
        setInterval(() => {
            const randomWatermark = document.createElement('div');
            randomWatermark.style.cssText = `
                position: fixed;
                top: ${Math.random() * 80 + 10}%;
                left: ${Math.random() * 80 + 10}%;
                color: rgba(255, 0, 0, 0.3);
                font-size: 12px;
                pointer-events: none;
                z-index: 9998;
                user-select: none;
                transform: rotate(${Math.random() * 360}deg);
            `;
            randomWatermark.textContent = new Date().toLocaleTimeString('tr-TR');
            document.body.appendChild(randomWatermark);
            
            // Remove after 2 seconds
            setTimeout(() => randomWatermark.remove(), 2000);
        }, 3000);
    }
    
    // Initialize screen recording detection
    function initializeScreenRecordingDetection() {
        console.log("ak_exams: Initializing screen recording detection...");
        
        const formElement = document.querySelector('form.o_survey_form, form');
        if (!formElement) {
            console.log("ak_exams: Form element not found for screen recording detection");
            return;
        }
        
        const disablePrintScreen = formElement.getAttribute('data-disable-print-screen') === 'true';
        const isStartScreen = formElement.getAttribute('data-is-start-screen') === 'true';
        accessToken = formElement.getAttribute('data-access-token');
        
        if (!disablePrintScreen || isStartScreen) {
            console.log("ak_exams: Screen recording detection not enabled or on start screen");
            return;
        }
        
        console.log("ak_exams: Screen recording detection enabled");
        
        // Show initial warning
        showScreenRecordingWarning();
        
        // Add watermark overlay
        addWatermarkOverlay();
        
        // Update watermark every 30 seconds
        setInterval(updateWatermark, 30000);
        
        // Add anti-recording measures
        addAntiRecordingMeasures();
        
        // Start detection interval
        detectionInterval = setInterval(detectScreenRecording, 5000);
        
        // Mobile device-specific detection (iOS and Android)
        if (isMobileDevice()) {
            const deviceName = isIOSDevice() ? 'iOS/iPadOS' : 'Android';
            console.log(`ak_exams: ${deviceName} device detected - enhanced monitoring enabled`);
            
            // Monitor for screen recording status bar changes (limited effectiveness)
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    console.warn(`ak_exams: Visibility changed on ${deviceName} - possible screen recording or app switch`);
                    logScreenRecordingAttempt();
                }
            });
            
            // Monitor for orientation changes (recording might trigger these)
            window.addEventListener('orientationchange', () => {
                console.log(`ak_exams: Orientation changed on ${deviceName} - monitoring for recording`);
            });
            
            // iOS-specific: Detect Control Center access (where screen recording is started)
            if (isIOSDevice()) {
                let lastTouchY = 0;
                document.addEventListener('touchstart', (e) => {
                    if (e.touches.length > 0) {
                        lastTouchY = e.touches[0].clientY;
                    }
                });
                
                document.addEventListener('touchmove', (e) => {
                    if (e.touches.length > 0) {
                        const currentY = e.touches[0].clientY;
                        const deltaY = currentY - lastTouchY;
                        
                        // Swipe down from top-right (Control Center on iPad)
                        if (deltaY > 50 && e.touches[0].clientX > window.innerWidth * 0.8) {
                            console.warn("ak_exams: Possible Control Center access detected (iOS)");
                            showScreenRecordingWarning();
                        }
                    }
                });
            }
            
            // Android-specific: Detect notification panel swipe (where screen recording is started)
            if (isAndroidDevice()) {
                let lastTouchY = 0;
                document.addEventListener('touchstart', (e) => {
                    if (e.touches.length > 0) {
                        lastTouchY = e.touches[0].clientY;
                    }
                });
                
                document.addEventListener('touchmove', (e) => {
                    if (e.touches.length > 0) {
                        const currentY = e.touches[0].clientY;
                        const deltaY = currentY - lastTouchY;
                        
                        // Swipe down from top (notification panel on Android)
                        if (deltaY > 50 && lastTouchY < 100) {
                            console.warn("ak_exams: Possible notification panel access detected (Android)");
                            showScreenRecordingWarning();
                        }
                    }
                });
            }
        }
        
        // Prevent screenshots via keyboard (desktop browsers)
        document.addEventListener('keyup', (e) => {
            if (e.key === 'PrintScreen' || e.keyCode === 44) {
                console.log("ak_exams: PrintScreen key detected");
                logScreenRecordingAttempt();
                alert('UYARI: Ekran görüntüsü almaya çalıştınız! Bu işlem sınav güvenliği nedeniyle yasaktır.');
            }
        });
        
        // Detect screenshot shortcuts on Mac
        document.addEventListener('keydown', (e) => {
            // Cmd+Shift+3, Cmd+Shift+4, Cmd+Shift+5 (Mac screenshot shortcuts)
            if (e.metaKey && e.shiftKey && (e.key === '3' || e.key === '4' || e.key === '5')) {
                console.log("ak_exams: Mac screenshot shortcut detected");
                e.preventDefault();
                logScreenRecordingAttempt();
                alert('UYARI: Ekran görüntüsü almaya çalıştınız! Bu işlem sınav güvenliği nedeniyle yasaktır.');
            }
        });
    }
    
    // Cleanup function
    function cleanupScreenRecordingDetection() {
        if (detectionInterval) {
            clearInterval(detectionInterval);
            detectionInterval = null;
        }
        
        const watermark = document.getElementById('ak-exam-watermark');
        if (watermark) {
            watermark.remove();
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeScreenRecordingDetection);
    } else {
        initializeScreenRecordingDetection();
    }
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', cleanupScreenRecordingDetection);
    
    // Export functions for external use
    window.akExamsScreenRecording = {
        initialize: initializeScreenRecordingDetection,
        cleanup: cleanupScreenRecordingDetection,
        showWarning: showScreenRecordingWarning
    };
})();
