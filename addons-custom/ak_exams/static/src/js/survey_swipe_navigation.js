/**
 * Survey Swipe Navigation
 * Adds swipe left/right gesture support for navigating between survey questions on tablets/iPads
 */

(function() {
    'use strict';

    console.log('Survey Swipe Navigation Script Loaded');

    function initSwipeNavigation() {
        const surveyForm = document.querySelector('.o_survey_form');
        
        if (!surveyForm) {
            console.log('Survey form not found, skipping swipe navigation');
            return; // Not on a survey page
        }

        console.log('Survey form found, initializing swipe navigation');

        let touchStartX = 0;
        let touchEndX = 0;
        let touchStartY = 0;
        let touchEndY = 0;
        
        const minSwipeDistance = 50; // Minimum distance for a swipe to be registered (in pixels)
        const maxVerticalDistance = 100; // Maximum vertical movement allowed for horizontal swipe

        function handleSwipe() {
            const horizontalDistance = touchEndX - touchStartX;
            const verticalDistance = Math.abs(touchEndY - touchStartY);
            
            // Check if it's a horizontal swipe (not vertical scroll)
            if (Math.abs(horizontalDistance) < minSwipeDistance) {
                return; // Swipe too short
            }
            
            if (verticalDistance > maxVerticalDistance) {
                return; // Too much vertical movement, probably scrolling
            }

            // Swipe left - go to next question
            if (horizontalDistance < 0) {
                const nextButton = document.querySelector('button.o_survey_navigation_submit:not([name="button_submit"])');
                if (nextButton && !nextButton.disabled) {
                    console.log('Swipe left detected - going to next question');
                    nextButton.click();
                }
            }
            
            // Swipe right - go to previous question
            if (horizontalDistance > 0) {
                const prevButton = document.querySelector('button.o_survey_navigation_submit[name="button_submit"]');
                if (prevButton && !prevButton.disabled) {
                    console.log('Swipe right detected - going to previous question');
                    prevButton.click();
                }
            }
        }

        // Add touch event listeners to the survey form
        surveyForm.addEventListener('touchstart', function(e) {
            // Don't interfere with input fields, textareas, or select elements
            if (e.target.tagName === 'INPUT' || 
                e.target.tagName === 'TEXTAREA' || 
                e.target.tagName === 'SELECT') {
                return;
            }
            
            touchStartX = e.changedTouches[0].screenX;
            touchStartY = e.changedTouches[0].screenY;
        }, { passive: true });

        surveyForm.addEventListener('touchend', function(e) {
            // Don't interfere with input fields, textareas, or select elements
            if (e.target.tagName === 'INPUT' || 
                e.target.tagName === 'TEXTAREA' || 
                e.target.tagName === 'SELECT') {
                return;
            }
            
            touchEndX = e.changedTouches[0].screenX;
            touchEndY = e.changedTouches[0].screenY;
            handleSwipe();
        }, { passive: true });

        console.log('Survey swipe navigation initialized successfully');
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initSwipeNavigation);
    } else {
        // DOM already loaded
        initSwipeNavigation();
    }

})();
