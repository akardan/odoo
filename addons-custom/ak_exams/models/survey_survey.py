from odoo import api, fields, models, _
# import re # No longer needed for this simplified approach

class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    company_id = fields.Many2one(
        'res.company',
        string=_('Company'),
        default=lambda self: self.env.company
    )

    session_timeout_minutes = fields.Integer(
        string=_('Session Timeout (minutes)'),
        help=_("Automatically end the survey session after this many minutes of inactivity. Set to 0 for no timeout."),
        default=0
    )

    full_screen_mode = fields.Boolean(
        string=_('Full Screen Mode'),
        help=_("If enabled, the survey will attempt to run in full screen mode, preventing users from switching to other applications during the exam."),
        default=False
    )

    disable_copy_paste = fields.Boolean(
        string=_('Disable Copy/Paste'),
        help=_("If enabled, right-click and copy/cut/paste operations will be disabled during the exam."),
        default=False
    )

    disable_dev_tools = fields.Boolean(
        string=_('Disable Developer Tools'),
        help=_("If enabled, F12 and other developer tools access will be restricted during the exam."),
        default=False
    )

    disable_print_screen = fields.Boolean(
        string=_('Disable Print Screen'),
        help=_("If enabled, attempts to take screenshots using the Print Screen key will be restricted during the exam."),
        default=False
    )

    detect_tab_switching = fields.Boolean(
        string=_('Detect Tab Switching'),
        help=_("If enabled, the system will detect when the user switches to another browser tab or application during the exam."),
        default=False
    )

    # Penalty and Limit Settings
    penalty_fullscreen_exit = fields.Integer(string=_("Penalty for Fullscreen Exit"), default=0, help=_("Points deducted each time user exits fullscreen."))
    penalty_tab_switch = fields.Integer(string=_("Penalty for Tab Switch"), default=0, help=_("Points deducted each time user switches tab/focus."))
    penalty_devtools_attempt = fields.Integer(string=_("Penalty for Dev Tools Attempt"), default=0, help=_("Points deducted for attempting to use developer tools."))
    penalty_print_screen_attempt = fields.Integer(string=_("Penalty for Print Screen Attempt"), default=0, help=_("Points deducted for attempting to use print screen."))
    # Note: Copy/Paste is preventative, so direct penalty per attempt is harder. Could be a fixed penalty if any circumvention is detected server-side later.

    max_total_violations_allowed = fields.Integer(
        string=_("Max Allowed Violations"),
        default=0,
        help=_("Maximum number of cumulative security violations allowed before the survey is automatically submitted. 0 means no limit.")
    )
    max_total_penalty_points = fields.Integer(
        string=_("Max Total Penalty Points"),
        default=0,
        help=_("Maximum total penalty points that can be accumulated. If 0, no limit to penalty points, but survey might end due to violation count.")
    )

    @api.onchange('full_screen_mode', 'disable_copy_paste', 'disable_dev_tools', 'detect_tab_switching', 'disable_print_screen')
    def _onchange_update_security_description(self):
        """
        Updates the survey description with security rules based on enabled security features.
        Uses plain text formatting in Turkish language.
        """
        # Build list of security messages based on enabled features
        messages = []
        
        if self.full_screen_mode:
            if self.penalty_fullscreen_exit > 0:
                messages.append(f"Tam Ekran Modu: Bu sınav tam ekran modunda alınmalıdır. Tam ekrandan çıkış ihlali, her seferinde {self.penalty_fullscreen_exit} ceza puanına neden olur.")
            else:
                messages.append("Tam Ekran Modu: Bu sınav tam ekran modunda alınmalıdır. Tam ekrandan çıkış ceza puanlarına neden olabilir.")
                
        if self.detect_tab_switching:
            if self.penalty_tab_switch > 0:
                messages.append(f"Sekme Değiştirme Tespiti: Sınav penceresinden uzaklaşmak veya sekme değiştirmek tespit edilmektedir ve ihlali, her seferinde {self.penalty_tab_switch} ceza puanına neden olacaktır.")
            else:
                messages.append("Sekme Değiştirme Tespiti: Sınav penceresinden uzaklaşmak veya sekme değiştirmek tespit edilmektedir ve ceza puanlarına neden olabilir.")
                
        if self.disable_copy_paste:
            messages.append("Kopyala/Yapıştır Devre Dışı: İçeriği kopyalama, kesme veya yapıştırma işlemleri yasaktır.")
            
        if self.disable_print_screen:
            if self.penalty_print_screen_attempt > 0:
                messages.append(f"Ekran Görüntüsü Devre Dışı: Print Screen tuşunu kullanarak ekran görüntüsü alma girişimleri yasaktır. İhlali, her seferinde {self.penalty_print_screen_attempt} ceza puanına neden olacaktır.")
            else:
                messages.append("Ekran Görüntüsü Devre Dışı: Print Screen tuşunu kullanarak ekran görüntüsü alma girişimleri yasaktır.")
                
        if self.disable_dev_tools:
            if self.penalty_devtools_attempt > 0:
                messages.append(f"Geliştirici Araçları Devre Dışı: Tarayıcı geliştirici araçlarına erişim yasaktır. İhlali {self.penalty_devtools_attempt} ceza puanına neden olacaktır.")
            else:
                messages.append("Geliştirici Araçları Devre Dışı: Tarayıcı geliştirici araçlarına erişim yasaktır.")

        # Create a plain text security section if there are messages
        if messages:
            # Create a plain text security section in Turkish
            security_text = "ÖNEMLİ GÜVENLİK UYARILARI:\n\n"
            
            for msg in messages:
                security_text += "• " + msg + "\n"
            
            # Set the description directly
            self.description = security_text
        else:
            # No security features enabled, clear the description
            self.description = ""


    def _can_go_back(self, answer, page_or_question):
        self.ensure_one()
        if self.questions_layout == "one_page" or not self.users_can_go_back:
            return False
        if answer.state != 'in_progress' or answer.is_session_answer:
            return False

        # Determine the list of questions/pages relevant for navigation
        if self.questions_layout == 'page_per_section':
            # For 'page_per_section', navigation is based on survey.page_ids
            if self.page_ids and page_or_question == self.page_ids[0]:
                return False
            return True # Can go back if not first page
        else: # 'page_per_question'
            # For 'page_per_question', navigation is based on question_ids
            # Use predefined_question_ids if random, otherwise survey.question_ids
            if not answer.is_session_answer and self.questions_selection == 'random':
                relevant_questions = answer.predefined_question_ids
            else:
                relevant_questions = self.question_ids

            if relevant_questions and page_or_question == relevant_questions[0]:
                return False
            return True # Can go back if not first question in the relevant list

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    company_id = fields.Many2one(
        'res.company',
        string=_('Company'),
        related='survey_id.company_id',
        store=True,
        readonly=True
    )
    
    is_terminated = fields.Boolean(
        string=_('Terminated Due to Security Violation'),
        help=_("Indicates if this survey session was terminated due to a security violation."),
        default=False
    )
    
    # Violation Counters per type
    fullscreen_violation_count = fields.Integer(string=_("Fullscreen Exit Count"), default=0, readonly=True)
    tab_switch_violation_count = fields.Integer(string=_("Tab Switch/Focus Loss Count"), default=0, readonly=True)
    devtools_attempt_count = fields.Integer(string=_("Dev Tools Attempt Count"), default=0, readonly=True)
    print_screen_attempt_count = fields.Integer(string=_("Print Screen Attempt Count"), default=0, readonly=True)
    # copy_paste_attempt_count - Harder to track distinct "attempts" if successfully blocked.

    total_security_violations = fields.Integer(
        string=_('Total Security Violations'),
        compute='_compute_total_security_violations',
        store=True,
        help=_("Total number of all types of security violations detected during this survey session.")
    )
    
    accumulated_penalty_points = fields.Integer(string=_("Accumulated Penalty Points"), default=0, readonly=True)

    @api.depends('fullscreen_violation_count', 'tab_switch_violation_count', 'devtools_attempt_count', 'print_screen_attempt_count')
    def _compute_total_security_violations(self):
        for record in self:
            record.total_security_violations = (
                record.fullscreen_violation_count +
                record.tab_switch_violation_count +
                record.devtools_attempt_count +
                record.print_screen_attempt_count
            )

    def _get_penalty_for_violation(self, violation_type):
        self.ensure_one()
        survey_sudo = self.survey_id.sudo()
        if violation_type == 'fullscreen_exit':
            return survey_sudo.penalty_fullscreen_exit
        elif violation_type == 'tab_switch':
            return survey_sudo.penalty_tab_switch
        elif violation_type == 'devtools_attempt':
            return survey_sudo.penalty_devtools_attempt
        elif violation_type == 'print_screen_attempt':
            return survey_sudo.penalty_print_screen_attempt
        return 0

    def log_security_violation(self, violation_type):
        """
        Log a security violation, increment its counter, apply penalty, and check limits.
        Returns True if the survey was terminated as a result, False otherwise.
        """
        self.ensure_one()
        if self.state != 'in_progress':
            return False # Cannot log violations for already completed/terminated surveys

        vals_to_write = {}
        current_penalty = self._get_penalty_for_violation(violation_type)
        new_accumulated_penalty = self.accumulated_penalty_points + current_penalty

        if violation_type == 'fullscreen_exit':
            vals_to_write['fullscreen_violation_count'] = self.fullscreen_violation_count + 1
        elif violation_type == 'tab_switch':
            vals_to_write['tab_switch_violation_count'] = self.tab_switch_violation_count + 1
        elif violation_type == 'devtools_attempt':
            vals_to_write['devtools_attempt_count'] = self.devtools_attempt_count + 1
        elif violation_type == 'print_screen_attempt':
            vals_to_write['print_screen_attempt_count'] = self.print_screen_attempt_count + 1
        else:
            # For unknown types, or generic violations if you keep the old field
            # self.security_violations += 1 # This field is now computed
            pass
        
        if current_penalty > 0:
            max_penalty = self.survey_id.sudo().max_total_penalty_points
            if max_penalty > 0 and new_accumulated_penalty > max_penalty:
                new_accumulated_penalty = max_penalty
            vals_to_write['accumulated_penalty_points'] = new_accumulated_penalty
        
        # Note: The 'note' field was removed as it doesn't exist on the base survey.user_input model.
        # If detailed textual logging per violation on the user_input record is needed,
        # a 'note' or similar Text field should be added to the SurveyUserInput model extension.
        # For now, we rely on the specific violation counters and accumulated penalty points.
        
        self.write(vals_to_write) # Write accumulated changes

        # Recompute total violations after individual counts are updated
        # The @api.depends should handle this if store=True, but explicit recompute can be safer if called within same transaction.
        # self._compute_total_security_violations() # Not strictly needed if store=True and ORM handles it.

        # Check if the overall violation limit is reached
        # Need to access the recomputed total_security_violations or sum them manually here for the check
        current_total_violations = (
            self.fullscreen_violation_count +
            self.tab_switch_violation_count +
            self.devtools_attempt_count +
            self.print_screen_attempt_count
        ) # This uses values before potential write if not re-read.
        # It's better to sum the new values based on vals_to_write
        
        updated_total_violations = sum([
            vals_to_write.get('fullscreen_violation_count', self.fullscreen_violation_count),
            vals_to_write.get('tab_switch_violation_count', self.tab_switch_violation_count),
            vals_to_write.get('devtools_attempt_count', self.devtools_attempt_count),
            vals_to_write.get('print_screen_attempt_count', self.print_screen_attempt_count),
        ])

        max_allowed = self.survey_id.sudo().max_total_violations_allowed
        if max_allowed > 0 and updated_total_violations >= max_allowed:
            if self.state == 'in_progress': # Double check state before terminating
                self.write({
                    'state': 'done',
                    'is_terminated': True
                    # Note: Removed note update here as well.
                    # A custom message could be logged to server logs if needed:
                    # _logger.info(f"Survey (User Input ID: {self.id}) auto-submitted. Exceeded max violations ({updated_total_violations}/{max_allowed}).")
                })
                return True # Survey terminated
        
        return False # Survey not terminated by this violation