// Script to handle exam security features and randomization - Plain JavaScript
console.log("Survey Security Script Loaded (Plain JS Version)");

// Randomization functions
function randomizeAnswerOptions() {
    console.log("ak_exams: Randomizing answer options");
    
    // Find all question containers with randomization enabled
    const questionContainers = document.querySelectorAll('.js_question-wrapper[data-randomize-answers="true"]');
    
    questionContainers.forEach(function(container) {
        const questionId = container.getAttribute('data-question-id');
        
        console.log(`ak_exams: Randomizing answers for question ${questionId}`);
        
        // Find the answer wrapper for simple choice questions
        const answersContainer = container.querySelector('.o_survey_answer_wrapper.o_survey_form_choice[data-question-type="simple_choice_radio"]');
        if (answersContainer) {
            // Get all answer option divs (col-sm-12 divs containing labels)
            const answerElements = Array.from(answersContainer.querySelectorAll('.col-sm-12'));
            
            if (answerElements.length > 1) {
                console.log(`ak_exams: Found ${answerElements.length} answer options to randomize`);
                
                // Store original answer texts and values
                const answerData = answerElements.map((element, index) => {
                    const label = element.querySelector('label');
                    const input = element.querySelector('input[type="radio"]');
                    const span = element.querySelector('span.text-break');
                    return {
                        element: element,
                        originalIndex: index,
                        text: span ? span.textContent.trim() : '',
                        value: input ? input.value : '',
                        originalLetter: String.fromCharCode(65 + index) // A, B, C, D
                    };
                });
                
                // Shuffle array using Fisher-Yates algorithm with question ID as seed
                function seededShuffle(array, seed) {
                    let currentIndex = array.length;
                    let randomIndex;
                    
                    // Simple seeded random function
                    function seededRandom() {
                        seed = (seed * 9301 + 49297) % 233280;
                        return seed / 233280;
                    }
                    
                    while (currentIndex !== 0) {
                        randomIndex = Math.floor(seededRandom() * currentIndex);
                        currentIndex--;
                        [array[currentIndex], array[randomIndex]] = [array[randomIndex], array[currentIndex]];
                    }
                    
                    return array;
                }
                
                const shuffledData = seededShuffle([...answerData], parseInt(questionId) || 1);
                
                // Update the DOM with shuffled answers but keep A, B, C, D codes
                shuffledData.forEach((data, newIndex) => {
                    const newLetter = String.fromCharCode(65 + newIndex); // A, B, C, D for new positions
                    const element = answerElements[newIndex];
                    const label = element.querySelector('label');
                    const input = element.querySelector('input[type="radio"]');
                    const span = element.querySelector('span.text-break');
                    
                    // Update the text content
                    if (span) {
                        span.textContent = data.text;
                    }
                    
                    // Update input value to match the original answer
                    if (input) {
                        input.value = data.value;
                    }
                    
                    // Update any selection keys to show correct letter
                    const selectionKey = element.querySelector('.o_survey_key');
                    if (selectionKey) {
                        selectionKey.textContent = newLetter;
                    }
                });
                
                console.log(`ak_exams: Successfully randomized ${shuffledData.length} answer options with preserved codes`);
            }
        } else {
            console.log(`ak_exams: No answer container found for question ${questionId}`);
        }
    });
}

// Function to observe DOM changes and re-randomize when new content is loaded
function setupRandomizationObserver() {
    const observer = new MutationObserver(function(mutations) {
        let shouldRandomize = false;
        
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                // Check if new question content was added
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        if (node.classList && node.classList.contains('js_question-wrapper') ||
                            node.querySelector && node.querySelector('.js_question-wrapper')) {
                            shouldRandomize = true;
                        }
                    }
                });
            }
        });
        
        if (shouldRandomize) {
            console.log('ak_exams: New question content detected, re-randomizing answers');
            setTimeout(randomizeAnswerOptions, 100); // Small delay to ensure DOM is ready
        }
    });
    
    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    console.log('ak_exams: Randomization observer setup complete');
}

function initializeAkExamsSecurity() {
    console.log("ak_exams: DOM Content Loaded or function called directly. Initializing security features...");
    var surveyBackgrounds = document.querySelectorAll('.o_survey_background');
    console.log("ak_exams: Survey containers (.o_survey_background) found:", surveyBackgrounds.length);
    
    surveyBackgrounds.forEach(function(surveyBgElement, containerIndex) {
        setTimeout(function() {
            console.log(`ak_exams: Processing survey container (o_survey_background) ${containerIndex} (after 100ms delay)`);

            var formElement = surveyBgElement.querySelector('form.o_survey_form, form'); 
            if (!formElement) {
                if (surveyBgElement.tagName === 'FORM') {
                    formElement = surveyBgElement;
                    console.log(`ak_exams: .o_survey_background element IS the form for container ${containerIndex}`);
                } else {
                    console.warn(`ak_exams: No <form> element found inside .o_survey_background[${containerIndex}]. Using container itself for attributes.`);
                    formElement = surveyBgElement; 
                }
            } else {
                console.log(`ak_exams: Found <form> element inside .o_survey_background[${containerIndex}]:`, formElement);
            }

            var rawDisableCopyPasteAttr = formElement.getAttribute('data-disable-copy-paste');
            var rawFullScreenAttr = formElement.getAttribute('data-full-screen-mode');
            var rawDetectTabSwitchingAttr = formElement.getAttribute('data-detect-tab-switching');
            var rawDisableDevToolsAttr = formElement.getAttribute('data-disable-dev-tools');
            var rawIsStartScreenAttr = formElement.getAttribute('data-is-start-screen');
            var rawDisablePrintScreenAttr = formElement.getAttribute('data-disable-print-screen');
            var accessToken = formElement.getAttribute('data-access-token'); // Added for violation logging

            console.log(`ak_exams: FormElement - Raw getAttribute('data-disable-copy-paste'): "${rawDisableCopyPasteAttr}"`);
            console.log(`ak_exams: FormElement - Raw getAttribute('data-full-screen-mode'): "${rawFullScreenAttr}"`);
            console.log(`ak_exams: FormElement - Raw getAttribute('data-detect-tab-switching'): "${rawDetectTabSwitchingAttr}"`);
            console.log(`ak_exams: FormElement - Raw getAttribute('data-disable-dev-tools'): "${rawDisableDevToolsAttr}"`);
            console.log(`ak_exams: FormElement - Raw getAttribute('data-is-start-screen'): "${rawIsStartScreenAttr}"`);
            console.log(`ak_exams: FormElement - Raw getAttribute('data-disable-print-screen'): "${rawDisablePrintScreenAttr}"`);
            
            function getBooleanAttribute(rawValue) {
                // Check if rawValue is a string before calling toLowerCase
                return typeof rawValue === 'string' && rawValue.toLowerCase() === 'true';
            }

            var disableCopyPaste = getBooleanAttribute(rawDisableCopyPasteAttr);
            var fullScreenMode = getBooleanAttribute(rawFullScreenAttr);
            var detectTabSwitching = getBooleanAttribute(rawDetectTabSwitchingAttr);
            var disableDevTools = getBooleanAttribute(rawDisableDevToolsAttr);
            var isStartScreen = getBooleanAttribute(rawIsStartScreenAttr);
            var disablePrintScreen = getBooleanAttribute(rawDisablePrintScreenAttr);
            
            console.log(`ak_exams: FormElement (container ${containerIndex}) - DisableCopyPaste: ${disableCopyPaste}, FullScreenMode: ${fullScreenMode}, DetectTabSwitching: ${detectTabSwitching}, DisableDevTools: ${disableDevTools}, IsStartScreen: ${isStartScreen}, DisablePrintScreen: ${disablePrintScreen}, AccessToken: ${accessToken ? 'present' : 'MISSING'}`);

            // --- Violation Logging Infrastructure ---
            var surveyTerminated = false; // Flag to prevent further actions if terminated

            function showTerminationModal(message) {
                surveyTerminated = true;
                console.log("ak_exams: Showing termination modal. Message:", message);
                let overlayId = 'ak-termination-overlay';
                if (document.getElementById(overlayId)) return;

                const overlay = document.createElement('div');
                overlay.id = overlayId;
                Object.assign(overlay.style, {position: 'fixed', top: '0', left: '0', width: '100vw', height: '100vh', backgroundColor: 'rgba(0,0,0,0.95)', zIndex: '200000', display: 'flex', justifyContent: 'center', alignItems: 'center', color: 'white', textAlign: 'center'});
                overlay.innerHTML = `<div style="background: #fff; color: #333; padding: 40px; border-radius: 8px; box-shadow: 0 5px 20px rgba(0,0,0,0.3); max-width: 500px;"><h2>Survey Terminated</h2><p style="font-size: 1.1em; margin-top: 15px;">${message || 'This survey has been terminated due to security policy violations.'}</p><p style="font-size: 0.9em; margin-top: 20px; color: #777;">You may close this window.</p></div>`;
                document.body.appendChild(overlay);
                // Optionally, disable all inputs/buttons on the page
                document.querySelectorAll('button, input, textarea, select').forEach(el => el.disabled = true);
            }

            async function logSecurityViolation(eventType, eventData = {}) {
                if (surveyTerminated) {
                    console.log(`ak_exams: Survey already terminated. Ignoring violation: ${eventType}`);
                    return;
                }
                if (!accessToken) {
                    console.error("ak_exams: Cannot log security violation, access_token is missing from form data-attributes.");
                    return;
                }
                console.log(`ak_exams: Logging security violation - Type: ${eventType}, Token: ${accessToken.substring(0,5)}...`);

                try {
                    // Log parameters just before sending
                    console.log(`ak_exams: Preparing to send violation. AccessToken: '${accessToken}', EventType: '${eventType}', EventData:`, JSON.stringify(eventData));

                    const response = await fetch('/survey/security/log', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            access_token: accessToken,
                            event_type: eventType,
                            event_data: eventData
                        }),
                    });

                    if (!response.ok) {
                        const errorText = await response.text();
                        console.error(`ak_exams: HTTP error during security log! Status: ${response.status}. Response: ${errorText}`);
                        return;
                    }

                    const responseData = await response.json();
                    console.log('ak_exams: Violation log response (raw JSON-RPC):', responseData);

                    if (responseData.error) {
                        console.error('ak_exams: JSON-RPC error from server:', responseData.error.message || responseData.error.data || responseData.error);
                        return;
                    }

                    const actualResult = responseData.result; // This is the payload from the controller method

                    if (actualResult && actualResult.success === true) {
                        console.log('ak_exams: Security log successful on server.', actualResult);
                        if (actualResult.action === 'terminate') {
                            showTerminationModal(actualResult.message);
                        }
                    } else if (actualResult && actualResult.success === false) {
                        console.error('ak_exams: Failed to log security violation (server indicated failure). Details:', actualResult.error || 'No error details provided.', 'Full actualResult:', actualResult);
                    } else {
                        // Unexpected structure for actualResult (e.g., null, undefined, or no 'success' property)
                        console.error('ak_exams: Invalid or unexpected response payload from security log endpoint. actualResult:', actualResult, 'Full responseData:', responseData);
                    }
                } catch (error) {
                    console.error('ak_exams: Error sending security violation log:', error);
                }
            }
            // --- End Violation Logging Infrastructure ---
        
            if (disableCopyPaste) {
                console.log(`ak_exams: Container ${containerIndex} - Applying copy/paste protection`);
                document.addEventListener('contextmenu', function(e) {
                    if (!e.target.matches('input, textarea')) {
                        console.log("ak_exams: Context menu event blocked outside inputs/textareas");
                        e.preventDefault();
                        logSecurityViolation('copy_paste_attempt', { detail: 'contextmenu_blocked' });
                        return false;
                    }
                }, true);
                
                ['copy', 'cut', 'paste'].forEach(function(jsEventType) {
                    document.addEventListener(jsEventType, function(e) {
                        if (e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
                            console.log(`ak_exams: ${jsEventType} event blocked`);
                            e.preventDefault();
                            logSecurityViolation('copy_paste_attempt', { detail: `${jsEventType}_blocked` });
                        }
                    }, true);
                });
            }
            
            if (fullScreenMode) {
                console.log(`ak_exams: Container ${containerIndex} - Setting up fullscreen mode`);
                var startButton = formElement.querySelector('button[type="submit"][value="start"]');
                if (!startButton) {
                    startButton = formElement.querySelector('.o_survey_start_survey button[type="submit"], button.o_survey_start_survey[type="submit"]');
                }
                if (!startButton) {
                    var allSubmitButtons = formElement.querySelectorAll('button[type="submit"]');
                    allSubmitButtons.forEach(function(btn) {
                        const btnText = (btn.textContent || btn.innerText || "").trim().toLowerCase();
                        if (btnText === "start survey" || btnText === "start" || btnText === "start exam") {
                            startButton = btn;
                        }
                    });
                }
                if (startButton) {
                     console.log(`ak_exams: Container ${containerIndex} - Found start button:`, startButton);
                } else {
                    var submitButtonsOnForm = formElement.querySelectorAll('button[type="submit"]');
                    if (submitButtonsOnForm.length === 1) {
                        startButton = submitButtonsOnForm[0];
                        console.log(`ak_exams: Container ${containerIndex} - Found start button as the only submit button on the form:`, startButton);
                    } else {
                        console.warn(`ak_exams: Container ${containerIndex} - Survey start button NOT found for fullscreen mode trigger.`);
                    }
                }
                
                function requestFullScreen(isUserInitiated = true) {
                    console.log("ak_exams: requestFullScreen called. User initiated:", isUserInitiated);
                    var element = document.documentElement;
                    if (!isFullScreen()) { 
                        if (element.requestFullscreen) {
                            element.requestFullscreen().catch(err => {
                                console.error(`ak_exams: Error attempting to enable full-screen mode: ${err.message} (${err.name})`);
                                if (isUserInitiated) { 
                                   alert("Could not enter fullscreen mode. Please ensure your browser allows it for this site, or try a non-Incognito window.");
                                }
                                showReEnterFullscreenMessage(formElement, fullScreenMode); 
                            });
                        } else if (element.mozRequestFullScreen) { element.mozRequestFullScreen();
                        } else if (element.webkitRequestFullscreen) { element.webkitRequestFullscreen();
                        } else if (element.msRequestFullscreen) { element.msRequestFullscreen();
                        } else {
                            console.error("ak_exams: Fullscreen API not supported by this browser.");
                            if (isUserInitiated) alert("Fullscreen API is not supported by your browser.");
                        }
                    } else {
                        console.log("ak_exams: Already in fullscreen mode or request not needed.");
                    }
                }

                if (startButton) {
                    startButton.addEventListener('click', function() { requestFullScreen(true); });
                }
                
                function isFullScreen() {
                    return !!(document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement || document.msFullscreenElement);
                }

                function showReEnterFullscreenMessage(currentFormElement, fsModeEnabled) {
                    let overlayId = 'ak-fullscreen-overlay';
                    let existingOverlay = document.getElementById(overlayId);
                    if (!fsModeEnabled || isFullScreen()) {
                        if (existingOverlay) existingOverlay.remove();
                        return;
                    }
                    if (existingOverlay) return;

                    const overlay = document.createElement('div');
                    overlay.id = overlayId;
                    Object.assign(overlay.style, {position: 'fixed', top: '0', left: '0', width: '100vw', height: '100vh', backgroundColor: 'rgba(0,0,0,0.9)', zIndex: '100000', display: 'flex', justifyContent: 'center', alignItems: 'center', webkitBackdropFilter: 'blur(4px)', backdropFilter: 'blur(4px)'});
                    const messageBox = document.createElement('div');
                    Object.assign(messageBox.style, {backgroundColor: 'white', padding: '30px 40px', borderRadius: '8px', textAlign: 'center', boxShadow: '0 4px 15px rgba(0,0,0,0.2)', color: '#333'});
                    const messageText = document.createElement('p');
                    messageText.textContent = "Fullscreen mode is required to continue the exam.";
                    Object.assign(messageText.style, {fontSize: '1.2em', marginBottom: '20px'});
                    const reEnterButton = document.createElement('button');
                    reEnterButton.textContent = "Re-enter Fullscreen";
                    Object.assign(reEnterButton.style, {padding: '10px 20px', fontSize: '1em', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer', marginLeft: '10px'});
                    reEnterButton.onmouseover = function() { this.style.backgroundColor = '#0056b3'; };
                    reEnterButton.onmouseout = function() { this.style.backgroundColor = '#007bff'; };
                    reEnterButton.onclick = function() { requestFullScreen(true); };
                    messageBox.appendChild(messageText);
                    messageBox.appendChild(reEnterButton);
                    overlay.appendChild(messageBox);
                    document.body.appendChild(overlay);
                }
                
                function onFullScreenChange() {
                    console.log("ak_exams: onFullScreenChange event triggered. Is fullscreen:", isFullScreen());
                    if (!isFullScreen() && fullScreenMode && !isStartScreen) {
                        logSecurityViolation('fullscreen_exit');
                        showReEnterFullscreenMessage(formElement, fullScreenMode); // Keep existing modal for re-entry prompt
                    } else {
                         showReEnterFullscreenMessage(formElement, fullScreenMode); // Handles removing overlay if back in fullscreen
                    }
                }
                
                document.addEventListener('fullscreenchange', onFullScreenChange);
                document.addEventListener('webkitfullscreenchange', onFullScreenChange);
                document.addEventListener('mozfullscreenchange', onFullScreenChange);
                document.addEventListener('MSFullscreenChange', onFullScreenChange);

                if (fullScreenMode && !isFullScreen() && !isStartScreen) { 
                     console.log(`ak_exams: Container ${containerIndex} - Page loaded (not start screen), not in fullscreen. Showing re-enter message.`);
                     showReEnterFullscreenMessage(formElement, fullScreenMode);
                }
            }

            // Tab Switching and Focus Loss Detection
            if (detectTabSwitching) {
                console.log(`ak_exams: Container ${containerIndex} - Setting up tab switch/focus loss detection`);
                let visibilityWarningModal = null;

                function showVisibilityWarningModal(reason = "Tab switched or focus lost") {
                    let isVisible = document.visibilityState === 'visible';
                    let isFocused = document.hasFocus();
                    console.log(`ak_exams: showVisibilityWarningModal called. Reason: ${reason}. Visible: ${isVisible}, Focused: ${isFocused}`);

                    if (isVisible && isFocused) {
                        if (visibilityWarningModal) {
                            console.log("ak_exams: Tab/window is active, removing visibility warning.");
                            visibilityWarningModal.remove();
                            visibilityWarningModal = null;
                        }
                        return;
                    }
                    
                    if (visibilityWarningModal) {
                        console.log("ak_exams: Visibility warning overlay already shown.");
                        return; 
                    }

                    console.log(`ak_exams: Creating visibility warning modal overlay (${reason}).`);
                    visibilityWarningModal = document.createElement('div');
                    visibilityWarningModal.id = 'ak-visibility-warning-overlay';
                    Object.assign(visibilityWarningModal.style, {position: 'fixed', top: '0', left: '0', width: '100vw', height: '100vh', backgroundColor: 'rgba(0,0,0,0.9)', zIndex: '100000', display: 'flex', justifyContent: 'center', alignItems: 'center', webkitBackdropFilter: 'blur(4px)', backdropFilter: 'blur(4px)'});
                    
                    const messageBox = document.createElement('div');
                    Object.assign(messageBox.style, {backgroundColor: 'white', padding: '30px 40px', borderRadius: '8px', textAlign: 'center', boxShadow: '0 4px 15px rgba(0,0,0,0.2)', color: '#333'});
                    
                    const messageText = document.createElement('p');
                    messageText.textContent = "You have navigated away from the exam. Please return to the exam window to continue.";
                    if (reason === "PrintScreen attempt") { // Check for specific reason
                        messageText.textContent = "Attempting to take a screenshot is not allowed. Please focus on the exam.";
                    }
                    Object.assign(messageText.style, {fontSize: '1.2em', marginBottom: '0px'});
                                        
                    messageBox.appendChild(messageText);
                    visibilityWarningModal.appendChild(messageBox);
                    document.body.appendChild(visibilityWarningModal);
                }

                function handleVisibilityChange() {
                    console.log(`ak_exams: Event - visibilitychange. New state: ${document.visibilityState}`);
                    if (document.visibilityState === 'hidden') {
                        logSecurityViolation('tab_switch', { detail: 'visibility_hidden' });
                    }
                    showVisibilityWarningModal("Visibility changed"); // Keep existing modal
                }
                function handleWindowBlur() {
                    console.log("ak_exams: Event - window blur (lost focus)");
                    if (document.visibilityState === 'visible') {
                        logSecurityViolation('tab_switch', { detail: 'window_blur' });
                        showVisibilityWarningModal("Window lost focus"); // Keep existing modal
                    }
                }
                function handleWindowFocus() {
                    console.log("ak_exams: Event - window focus (gained focus)");
                    showVisibilityWarningModal("Window gained focus"); // Keep existing modal
                }
 
                document.addEventListener('visibilitychange', handleVisibilityChange);
                window.addEventListener('blur', handleWindowBlur);
                window.addEventListener('focus', handleWindowFocus);
                
                if (document.visibilityState === 'hidden' || !document.hasFocus()) {
                    console.log(`ak_exams: Initial check on load: page is hidden or unfocused. Visibility: ${document.visibilityState}, HasFocus: ${document.hasFocus()}`);
                    showVisibilityWarningModal("Initial page load: hidden or unfocused");
                }
            } else {
                console.log(`ak_exams: Container ${containerIndex} - Tab switch/focus loss detection IS DISABLED.`);
            }

            // Disable developer tools shortcuts
            if (disableDevTools) {
                console.log(`ak_exams: Container ${containerIndex} - Setting up DevTools disabler`);
                document.addEventListener('keydown', function(e) {
                    const isDevToolsShortcut = (
                        e.key === 'F12' ||
                        (e.ctrlKey && e.shiftKey && (e.key === 'I' || e.key === 'i' || e.key === 'J' || e.key === 'j' || e.key === 'C' || e.key === 'c')) ||
                        (e.ctrlKey && (e.key === 'U' || e.key === 'u')) || 
                        (e.metaKey && e.altKey && (e.key === 'I' || e.key === 'i' || e.key === 'J' || e.key === 'j' || e.key === 'C' || e.key === 'c')) 
                    );

                    if (isDevToolsShortcut) {
                        console.log(`ak_exams: DevTools shortcut blocked (key: ${e.key}, ctrl: ${e.ctrlKey}, shift: ${e.shiftKey}, meta: ${e.metaKey}, alt: ${e.altKey})`);
                        e.preventDefault();
                        logSecurityViolation('devtools_attempt', { key: e.key, ctrl: e.ctrlKey, shift: e.shiftKey });
                        return false;
                    }
                });
            }

            // Disable Print Screen (deterrent)
            if (disablePrintScreen) {
                console.log(`ak_exams: Container ${containerIndex} - Setting up Print Screen deterrent`);
                document.addEventListener('keyup', function(e) {
                    if (e.key === 'PrintScreen' || e.keyCode === 44) {
                        console.log("ak_exams: PrintScreen key detected");
                        logSecurityViolation('print_screen_attempt');
                        showVisibilityWarningModal("PrintScreen attempt"); // Keep existing modal
                    }
                });
            }

        }, 100); // Delay for setTimeout
    }); // End of surveyBackgrounds.forEach
    
    // Initialize randomization after security setup
    setTimeout(randomizeAnswerOptions, 200);
    
    // Setup observer for AJAX navigation
    setupRandomizationObserver();
    
    // Initialize photo capture after security setup
    setTimeout(initializePhotoCapture, 300);
} // End of initializeAkExamsSecurity

// ========== PHOTO CAPTURE FUNCTIONALITY ==========
let wakeLockSentinel = null;

async function requestWakeLock() {
    try {
        if ('wakeLock' in navigator) {
            wakeLockSentinel = await navigator.wakeLock.request('screen');
            console.log('ak_exams: Screen wake lock activated - screen will not dim');
            
            // Re-request wake lock when visibility changes
            document.addEventListener('visibilitychange', async () => {
                if (wakeLockSentinel !== null && document.visibilityState === 'visible') {
                    wakeLockSentinel = await navigator.wakeLock.request('screen');
                }
            });
        }
    } catch (err) {
        console.log('ak_exams: Wake lock not supported or denied:', err);
    }
}

async function releaseWakeLock() {
    if (wakeLockSentinel !== null) {
        await wakeLockSentinel.release();
        wakeLockSentinel = null;
        console.log('ak_exams: Screen wake lock released');
    }
}

async function initializePhotoCapture() {
    console.log('ak_exams: Initializing photo capture...');
    const formElement = document.querySelector('form.o_survey_form, form[data-photo-capture-mode]');
    
    if (!formElement) {
        console.log('ak_exams: Form element not found for photo capture');
        return;
    }
    
    const photoCaptureMode = formElement.getAttribute('data-photo-capture-mode') || 'disabled';
    const isStartScreen = formElement.getAttribute('data-is-start-screen') === 'true';
    
    console.log('ak_exams: Photo capture mode: ' + photoCaptureMode + ', isStartScreen: ' + isStartScreen);
    
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
    
    // Request camera permission
    try {
        console.log('ak_exams: Requesting camera permission...');
        
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' },
            audio: false
        });
        
        console.log('ak_exams: Camera permission granted');
        
        // Update permission status on server
        fetch('/survey/photo/permission', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: { access_token: accessToken, permission_granted: true }
            })
        });
        
        // Store stream globally for cleanup
        window.examCameraStream = stream;
        
        // Find start button and add photo capture logic
        const startButton = formElement.querySelector('button[type="submit"][value="start"]');
        if (startButton) {
            startButton.addEventListener('click', function() {
                console.log('ak_exams: Start button clicked, will capture photos during exam');
                
                // Request wake lock to prevent screen from dimming
                requestWakeLock();
                
                // Capture initial photo after exam starts
                setTimeout(function() {
                    captureAndSendPhoto(stream, accessToken, 'initial');
                    
                    // Schedule random captures
                    scheduleRandomCaptures(stream, accessToken, photoCaptureConfig);
                }, 1000);
            });
        }
        
    } catch (error) {
        console.error('ak_exams: Camera permission denied:', error);
        
        // Update permission status on server
        fetch('/survey/photo/permission', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: { access_token: accessToken, permission_granted: false }
            })
        });
        
        if (photoCaptureConfig.mode === 'mandatory') {
            // Mandatory mode: BLOCK exam start
            
            // Find and disable ALL submit buttons to be sure
            const allButtons = formElement.querySelectorAll('button[type="submit"]');
            allButtons.forEach(function(btn) {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
                btn.style.backgroundColor = '#ccc';
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    alert('Bu sınav için kamera izni zorunludur. Lütfen sayfayı yenileyin ve kamera iznini verin.');
                    return false;
                }, true);
            });
            
            // Also prevent form submission
            formElement.addEventListener('submit', function(e) {
                e.preventDefault();
                e.stopPropagation();
                alert('Sınav başlatılamaz! Kamera izni gereklidir.');
                return false;
            }, true);
            
            alert('Kamera İzni Gerekli: Bu sınav için kamera erişimi zorunludur. Lütfen sayfayı yenileyin ve kamera iznini verin.');
        } else {
            // Optional mode: show warning but allow exam
            console.warn('ak_exams: Camera permission denied (optional mode) - continuing without photos');
            alert('Uyarı: Kamera izni reddedildi. Sınava devam edebilirsiniz ancak fotoğraf çekilmeyecektir.');
        }
    }
}

function captureAndSendPhoto(stream, accessToken, captureType) {
    try {
        console.log('ak_exams: Capturing photo (' + captureType + ')...');
        
        // Create hidden video element
        const video = document.createElement('video');
        video.style.display = 'none';
        video.autoplay = true;
        video.srcObject = stream;
        document.body.appendChild(video);
        
        // Wait for video to be ready
        video.onloadedmetadata = function() {
            // Create canvas to capture frame
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const context = canvas.getContext('2d');
            context.drawImage(video, 0, 0);
            
            // Convert to base64
            const photoData = canvas.toDataURL('image/jpeg', 0.8);
            console.log('ak_exams: Photo captured, size: ' + photoData.length + ' bytes');
            
            // Send to server
            fetch('/survey/photo/capture', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jsonrpc: '2.0',
                    method: 'call',
                    params: {
                        access_token: accessToken,
                        photo_data: photoData,
                        capture_type: captureType
                    }
                })
            }).then(function(response) {
                return response.json();
            }).then(function(data) {
                if (data.result && data.result.success) {
                    console.log('ak_exams: Photo sent successfully');
                } else {
                    console.error('ak_exams: Failed to send photo');
                }
            });
            
            // Cleanup
            video.remove();
        };
    } catch (error) {
        console.error('ak_exams: Error capturing photo:', error);
    }
}

function scheduleRandomCaptures(stream, accessToken, config) {
    function scheduleNext() {
        const interval = Math.floor(Math.random() * (config.maxInterval - config.minInterval) + config.minInterval);
        console.log('ak_exams: Next photo in ' + (interval / 1000) + ' seconds');
        
        const timerId = setTimeout(function() {
            captureAndSendPhoto(stream, accessToken, 'random');
            scheduleNext();
        }, interval);
        
        // Store timer ID globally for cleanup
        if (!window.examPhotoTimers) window.examPhotoTimers = [];
        window.examPhotoTimers.push(timerId);
    }
    
    scheduleNext();
}

// Cleanup function for camera and wake lock
function cleanupExamResources() {
    console.log('ak_exams: Cleaning up exam resources...');
    
    // Stop camera stream
    if (window.examCameraStream) {
        window.examCameraStream.getTracks().forEach(track => track.stop());
        window.examCameraStream = null;
        console.log('ak_exams: Camera stream stopped');
    }
    
    // Clear photo timers
    if (window.examPhotoTimers) {
        window.examPhotoTimers.forEach(timerId => clearTimeout(timerId));
        window.examPhotoTimers = [];
        console.log('ak_exams: Photo timers cleared');
    }
    
    // Release wake lock
    releaseWakeLock();
}

// Add cleanup button when exam is completed
function addCleanupButton() {
    // Check if we're on a completed exam page
    const completedMessage = document.querySelector('.o_survey_finished, .o_survey_completed');
    if (!completedMessage) return;
    
    // Check if cleanup button already exists
    if (document.getElementById('exam-cleanup-button')) return;
    
    const cleanupButton = document.createElement('button');
    cleanupButton.id = 'exam-cleanup-button';
    cleanupButton.textContent = 'Kamerayı Kapat ve Çık';
    cleanupButton.className = 'btn btn-primary mt-3';
    Object.assign(cleanupButton.style, {
        padding: '10px 20px',
        fontSize: '16px',
        marginTop: '20px'
    });
    
    cleanupButton.addEventListener('click', function() {
        cleanupExamResources();
        alert('Kamera kapatıldı. Sayfayı kapatabilirsiniz.');
    });
    
    completedMessage.appendChild(cleanupButton);
    console.log('ak_exams: Cleanup button added');
}

// Call cleanup on page unload
window.addEventListener('beforeunload', cleanupExamResources);

// Check for completed exam state periodically
setInterval(addCleanupButton, 2000);

if (document.readyState === 'loading') {
    console.log("ak_exams: Document is loading, adding DOMContentLoaded listener.");
    document.addEventListener('DOMContentLoaded', initializeAkExamsSecurity);
} else {
    console.log("ak_exams: DOMContentLoaded already fired, running security init immediately.");
    initializeAkExamsSecurity();
}