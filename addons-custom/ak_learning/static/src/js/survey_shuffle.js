odoo.define('ak_learning.survey_shuffle', function (require) {
    'use strict';
    
    var core = require('web.core');
    var publicWidget = require('web.public.widget');
    var surveyForm = require('survey.form');
    
    // This widget extends the SurveyFormWidget to implement question shuffling
    publicWidget.registry.SurveyFormWidget.include({
        init: function () {
            this._super.apply(this, arguments);
            this.shuffleEnabled = false;
        },
    
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                // Check if we need to shuffle questions
                self._checkShuffleNeeded();
            });
        },
    
        _checkShuffleNeeded: function() {
            var self = this;
            // Check if shuffle is enabled for this survey
            this._rpc({
                route: '/survey/get_shuffle_config',
                params: {
                    'survey_token': self.options.surveyToken,
                    'answer_token': self.options.answerToken,
                },
            }).then(function (result) {
                if (result && result.shuffle_questions) {
                    self.shuffleEnabled = true;
                    self._shuffleQuestions();
                }
            });
        },
    
        _shuffleQuestions: function() {
            var self = this;
            // Only handle page_per_question layout, as it's the one most commonly used for assessments/exams
            if (self.options.questionsLayout !== 'page_per_question') {
                return;
            }
    
            // For page_per_question, we shuffle the order in the survey progression
            var $progressionLi = $('.o_survey_progress_wrapper li');
            
            if ($progressionLi.length > 1) {
                // Store original order for logging purposes
                var originalOrder = Array.from($progressionLi).map(function(li) {
                    return $(li).data('questionId');
                });
    
                console.log("Original question order:", originalOrder);
                
                // Shuffle the list items
                var $progressionUl = $('.o_survey_progress_wrapper ul');
                var $items = $progressionUl.children().detach();
                
                // Fisher-Yates shuffle algorithm
                var shuffledItems = Array.from($items);
                for (var i = shuffledItems.length - 1; i > 0; i--) {
                    var j = Math.floor(Math.random() * (i + 1));
                    var temp = shuffledItems[i];
                    shuffledItems[i] = shuffledItems[j];
                    shuffledItems[j] = temp;
                }
                
                // Re-append in new order
                $progressionUl.append($(shuffledItems));
                
                // Log shuffled order
                var shuffledOrder = Array.from($progressionUl.find('li')).map(function(li) {
                    return $(li).data('questionId');
                });
                
                console.log("Shuffled question order:", shuffledOrder);
                
                // Update active status
                $progressionUl.find('li').removeClass('active');
                $progressionUl.find('li:first-child').addClass('active');
            }
        },
    
        _onSubmit: function (event) {
            // If shuffle is enabled, we need to ensure the submission
            // uses the correct question IDs and doesn't break the survey flow
            if (this.shuffleEnabled) {
                // Get the current question ID from the form
                var currentQuestionId = this.$('input[name="question_id"]').val();
                console.log("Submitting answer for question ID:", currentQuestionId);
            }
            
            // Call original implementation
            return this._super.apply(this, arguments);
        }
    });
    
});