/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

// Wait for SurveyFormWidget to be registered before extending it
document.addEventListener('DOMContentLoaded', function() {
    if (publicWidget.registry.SurveyFormWidget) {
        publicWidget.registry.SurveyFormWidget.include({
            /**
             * Override to handle custom error messages from ak_exams module
             * Specifically handles 'time_expired' and 'exam_closed' errors
             */
            _onNextScreenDone: function(options) {
                const result = this.nextScreenResult;
                
                // CRITICAL FIX: Handle custom exam errors (time_expired, exam_closed)
                // Check if result is an object with error property
                if (result && typeof result === 'object' && result.error) {
                    if (result.error === 'time_expired' || result.error === 'exam_closed') {
                        console.log('ak_exams: Handling exam termination error:', result.error);
                        
                        // Display custom error message
                        this.$('.o_survey_form_content').fadeIn(0);
                        
                        // Create error alert
                        const errorMessage = result.error_message || 'Sınav sona erdi.';
                        const $errorAlert = $(`
                            <div class="alert alert-danger" role="alert">
                                <h4 class="alert-heading">
                                    <i class="fa fa-exclamation-triangle"></i> Sınav Sonlandırıldı
                                </h4>
                                <p class="mb-0">${errorMessage}</p>
                            </div>
                        `);
                        
                        // Clear content and show error
                        this.$('.o_survey_form_content').empty().append($errorAlert);
                        
                        // Hide navigation buttons
                        if (this.$surveyNavigation && this.$surveyNavigation.length) {
                            this.$surveyNavigation.hide();
                        }
                        
                        // Destroy timer if exists
                        if (this.surveyTimerWidget) {
                            this.surveyTimerWidget.destroy();
                        }
                        
                        // Scroll to top
                        $("html, body").animate({ scrollTop: 0 }, 400);
                        
                        // Prevent further processing
                        return;
                    }
                }
                
                // Call parent method for all other cases
                return this._super.apply(this, arguments);
            }
        });
        console.log('ak_exams: SurveyFormWidget extension loaded successfully');
    } else {
        console.error('ak_exams: SurveyFormWidget not found in registry');
    }
});
