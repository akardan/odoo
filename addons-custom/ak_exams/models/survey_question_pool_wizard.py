# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api
from odoo.tools.translate import _

class SurveyQuestionPoolWizard(models.TransientModel):
    _name = 'survey.question.pool.wizard'
    _description = 'Survey Question Pool Wizard'

    survey_id = fields.Many2one(
        'survey.survey',
        string=_('Survey'),
        required=True,
        readonly=True
    )
    
    job_position_id = fields.Many2one(
        'hr.job',
        string=_('Role'),
        domain="[('active', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
    
    category_id = fields.Many2one(
        'survey.question.poll.category',
        string=_('Category'),
        domain="[('active', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
    
    company_id = fields.Many2one(
        'res.company',
        string=_('Company'),
        related='survey_id.company_id',
        readonly=True
    )
    
    question_poll_ids = fields.Many2many(
        'survey.question.poll',
        string=_('Questions'),
        domain="[('active', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]"
    )
    
    @api.onchange('job_position_id')
    def _onchange_job_position_id(self):
        """Filter categories based on selected role"""
        domain = [('active', '=', True)]
        
        # Add job position filter if selected
        if self.job_position_id:
            domain.append(('job_position_ids', 'in', [self.job_position_id.id]))
        
        # Add company filter
        domain.extend(['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)])
        
        # Log for debugging
        _logger = logging.getLogger(__name__)
        _logger.info("Category domain: %s", domain)
        
        return {'domain': {'category_id': domain}}
    
    @api.model
    def default_get(self, fields_list):
        """Set default values for the wizard"""
        res = super(SurveyQuestionPoolWizard, self).default_get(fields_list)
        
        # Log for debugging
        _logger = logging.getLogger(__name__)
        _logger.info("Default get context: %s", self.env.context)
        
        return res
    
    @api.onchange('category_id')
    def _onchange_category_id(self):
        """Filter questions based on selected category"""
        domain = [('active', '=', True)]
        
        # Add category filter if selected
        if self.category_id:
            domain.append(('category_id', '=', self.category_id.id))
        
        # Add company filter
        domain.extend(['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)])
        
        return {'domain': {'question_poll_ids': domain}}
    
    def action_add_questions(self):
        """Add selected questions to the survey"""
        _logger = logging.getLogger(__name__)
        _logger.info("action_add_questions called")
        _logger.info("survey_id: %s", self.survey_id)
        _logger.info("question_poll_ids: %s", self.question_poll_ids)
        
        self.ensure_one()
        if not self.question_poll_ids:
            _logger.warning("No questions selected")
            return {'type': 'ir.actions.act_window_close'}
        
        # Get the highest sequence number in the survey
        questions = self.env['survey.question'].search([
            ('survey_id', '=', self.survey_id.id),
            ('is_page', '=', False)
        ], order='sequence desc', limit=1)
        
        sequence = 10
        if questions:
            sequence = questions.sequence + 1
        
        _logger.info("Starting sequence: %s", sequence)
        
        # Add each selected question to the survey
        added_questions = 0
        for poll in self.question_poll_ids:
            _logger.info("Adding question: %s", poll.name)
            try:
                new_question_id = poll.create_poll_from_template(poll.id, self.survey_id.id, sequence)
                _logger.info("Question added with ID: %s", new_question_id)
                sequence += 1
                added_questions += 1
            except Exception as e:
                _logger.error("Error adding question: %s", e)
        
        _logger.info("Total questions added: %s", added_questions)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%s questions added to the survey.') % added_questions,
                'sticky': False,
                'type': 'success',
            }
        }