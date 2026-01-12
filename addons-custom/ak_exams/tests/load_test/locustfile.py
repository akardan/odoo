from locust import HttpUser, task, between
from bs4 import BeautifulSoup
import random
import logging
import os
import warnings
import urllib3

# Suppress SSL warnings and deprecation warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

class SurveyUser(HttpUser):
    wait_time = between(2, 5)
    
    # Token will be read from environment variable
    survey_token = None
    question_number = 0

    def on_start(self):
        self.client.verify = False  # Ignore SSL warnings
        
        # Read token from environment variable
        self.survey_token = os.environ.get('SURVEY_TOKEN')
        
        if not self.survey_token:
            logging.error("SURVEY_TOKEN environment variable is not set! Please run with: SURVEY_TOKEN=your_token locust")
            self.environment.runner.quit()
        
        # Reset question counter for this user
        self.question_number = 0

    @task
    def take_survey(self):
        if not self.survey_token:
            return

        # 1. Access the survey page
        if self.survey_token.startswith("http"):
            url = self.survey_token
        else:
            url = f"/survey/start/{self.survey_token}"
            
        response = self.client.get(url)
        
        if response.status_code != 200:
            logging.error(f"Failed to load survey start page: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = self._get_csrf_token(soup)
        
        # 2. Check for "Start Certification" or "Start Survey" button
        # Odoo surveys often have a welcome page.
        # Look specifically for a button with value="start"
        start_button = soup.find('button', {'type': 'submit', 'value': 'start'})
        
        if start_button:
            logging.info("Starting survey...")
            # The form usually posts to the same URL or a specific start URL
            # We'll try to find the form action
            form = soup.find('form')
            if form:
                action = form.get('action')
                
                # If action is missing, it usually submits to the same URL (Start URL)
                if not action:
                    action = url
                
                if action:
                    # Try to find the token input in the form
                    token_input = form.find('input', {'name': 'token'})
                    token_value = token_input.get('value') if token_input else self.survey_token

                    response = self.client.post(action, data={
                        'csrf_token': csrf_token,
                        'token': token_value,
                        'button_submit': 'start' # Common in Odoo
                    })
                    soup = BeautifulSoup(response.text, 'html.parser')
                    csrf_token = self._get_csrf_token(soup)
                else:
                    logging.warning("Start form found but has no action attribute and could not construct one.")
            else:
                logging.warning("No start form found on the page.")

        # 3. Loop through questions
        while True:
            # Find the main survey form
            # Try standard Odoo class first, then fallback to generic form with survey data
            form = soup.find('form', {'class': 'js_surveyform'})
            if not form:
                form = soup.find('form', attrs={'data-survey-token': True})
            
            if not form:
                # Check for completion message
                if "Sınavınız tamamlandı" in response.text or "Thank you" in response.text or "survey_fill_form_done" in response.text:
                    logging.info("Survey completed successfully.")
                else:
                    logging.error("No survey form found! Survey may not be active or accessible. Stopping all tests.")
                    if self.environment.runner:
                        self.environment.runner.quit()
                break
            
            action = form.get('action')
            if not action:
                # Try to construct from data attributes
                survey_token = form.get('data-survey-token')
                answer_token = form.get('data-answer-token')
                if survey_token and answer_token:
                    action = f"/survey/submit/{survey_token}/{answer_token}"
            
            if not action:
                logging.error("Form has no action and could not construct one. Stopping.")
                break

            # Prepare data
            # Try to find the token input in the form
            token_input = form.find('input', {'name': 'token'})
            token_value = token_input.get('value') if token_input else self.survey_token

            data = {
                'csrf_token': csrf_token,
                'token': token_value
            }

            # Find all questions on this page
            # Odoo 14+ structure: div.js_question-wrapper
            questions = soup.find_all('div', {'class': 'js_question-wrapper'})
            
            if not questions:
                # Fallback for older versions or different layouts
                questions = soup.find_all('div', class_=lambda x: x and 'js_question' in x)

            for question in questions:
                q_id = question.get('id') # e.g. question_123
                
                # Increment question number (max 20)
                self.question_number += 1
                
                # Simulate violations for this question (random 1-15 for each type)
                if self.question_number <= 20:
                    self._simulate_violations_for_question(self.question_number)
                
                # Find inputs within this question
                inputs = question.find_all('input')
                
                # Radio buttons (Simple Choice)
                radios = [i for i in inputs if i.get('type') == 'radio']
                if radios:
                    # Pick one random option
                    chosen = random.choice(radios)
                    name = chosen.get('name')
                    value = chosen.get('value')
                    data[name] = value
                
                # Checkboxes (Multiple Choice)
                checkboxes = [i for i in inputs if i.get('type') == 'checkbox']
                if checkboxes:
                    # Pick random number of options
                    to_check = random.sample(checkboxes, k=random.randint(1, len(checkboxes)))
                    for cb in to_check:
                        name = cb.get('name')
                        value = cb.get('value')
                        data[name] = value

                # Text inputs
                texts = [i for i in inputs if i.get('type') == 'text']
                for txt in texts:
                    name = txt.get('name')
                    data[name] = "Test Answer"

            # Submit the page
            logging.info(f"Submitting page to {action}")
            # Try sending as JSON since the controller is type='json'
            response = self.client.post(action, json=data)
            
            # Update soup and token for next iteration
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_token = self._get_csrf_token(soup)
            
            # Check if we are redirected to the "done" page or similar
            if "print" in response.url or "results" in response.url:
                logging.info("Survey finished (redirected).")
                break

    def _simulate_violations_for_question(self, question_num):
        """Simulate random violations (1-15) for each violation type for a specific question"""
        if not self.survey_token:
            return
        
        # Extract survey_token
        token = self.survey_token.split('/')[-1] if '/' in self.survey_token else self.survey_token
        
        # Generate random counts for each violation type (1-3)
        fullscreen_count = random.randint(1, 3)
        tab_switch_count = random.randint(1, 3)
        devtools_count = random.randint(1, 3)
        print_screen_count = random.randint(1, 3)
        
        logging.info(f"Question {question_num}: Simulating violations - "
                    f"Fullscreen: {fullscreen_count}, Tab Switch: {tab_switch_count}, "
                    f"DevTools: {devtools_count}, Print Screen: {print_screen_count}")
        
        # Simulate fullscreen violations
        for i in range(fullscreen_count):
            self.client.post(
                f"/survey/log_violation/{token}",
                json={
                    'violation_type': 'fullscreen_exit',
                    'question_number': question_num,
                    'timestamp': i
                },
                name="/survey/log_violation [fullscreen]"
            )
        
        # Simulate tab switch violations
        for i in range(tab_switch_count):
            self.client.post(
                f"/survey/log_violation/{token}",
                json={
                    'violation_type': 'tab_switch',
                    'question_number': question_num,
                    'timestamp': i
                },
                name="/survey/log_violation [tab_switch]"
            )
        
        # Simulate devtools attempt violations
        for i in range(devtools_count):
            self.client.post(
                f"/survey/log_violation/{token}",
                json={
                    'violation_type': 'devtools_open',
                    'question_number': question_num,
                    'timestamp': i
                },
                name="/survey/log_violation [devtools]"
            )
        
        # Simulate print screen violations
        for i in range(print_screen_count):
            self.client.post(
                f"/survey/log_violation/{token}",
                json={
                    'violation_type': 'print_screen',
                    'question_number': question_num,
                    'timestamp': i
                },
                name="/survey/log_violation [print_screen]"
            )

    def _get_csrf_token(self, soup):
        token_input = soup.find('input', {'name': 'csrf_token'})
        if token_input:
            return token_input.get('value')
        
        # Sometimes it's in a script variable `odoo.csrf_token`
        # But for standard forms, the input should be there.
        return ""
