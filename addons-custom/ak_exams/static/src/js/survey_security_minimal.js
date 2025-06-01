// Script to handle exam security features - Plain JavaScript
console.log("Survey Security Script Loaded (Plain JS Version)");

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
} // End of initializeAkExamsSecurity

if (document.readyState === 'loading') {
    console.log("ak_exams: Document is loading, adding DOMContentLoaded listener.");
    document.addEventListener('DOMContentLoaded', initializeAkExamsSecurity);
} else {
    console.log("ak_exams: DOMContentLoaded already fired, running security init immediately.");
    initializeAkExamsSecurity();
}