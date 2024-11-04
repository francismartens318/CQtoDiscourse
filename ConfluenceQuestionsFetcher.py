import requests
from atlassian import Confluence
from typing import Union
import logging
import time

class ConfluenceQuestionsFetcher:
    def __init__(self, confluence_url, confluence_username, confluence_password):
        self.confluence = Confluence(
            url=confluence_url,
            username=confluence_username,
            password=confluence_password
        )
        self.base_url = confluence_url.rstrip('/') + '/rest/questions/1.0'
        self.auth = (confluence_username, confluence_password)

    def fetch_questions(self, space_key=None, limit=None, start=None):
        """Fetch questions from Confluence.
        
        Args:
            space_key (str, optional): The Confluence space key to fetch from
            limit (int, optional): Maximum number of questions to fetch (if None, fetches all)
            start (int, optional): Starting offset for pagination (if None, starts from beginning)
            
        Returns:
            list: List of question data dictionaries
            
        Raises:
            requests.exceptions.HTTPError: If the API request fails
        """
        url = f"{self.base_url}/question"
        params = {
            'spaceKey': space_key,
            'limit': 10000  # Set a very high limit to get all questions
        }
        
        # Override with specific limit if provided
        if limit is not None:
            params['limit'] = limit
        if start is not None:
            params['start'] = start
            
        response = requests.get(url, params=params, auth=self.auth)
        response.raise_for_status()
        
        questions = response.json()
        logging.info(f"Fetched {len(questions)} questions from Confluence")
        return questions

    def get_all_questions(self, space_key=None):
        """Fetch all questions using pagination and return them sorted by creation date.
        
        Args:
            space_key (str, optional): The Confluence space key to fetch from
            
        Returns:
            list: List of question objects sorted by creation date (oldest first)
        """
        logging.info("Starting to fetch all questions from Confluence...")
        if space_key:
            logging.info(f"Using space key: {space_key}")
        
        all_questions = []
        start = 0
        batch_size = 50  # Confluence's maximum batch size is 500
        
        while True:
            logging.info(f"Fetching questions batch starting at offset {start}...")
            questions_batch = self.fetch_questions(space_key, limit=batch_size, start=start)
            
            if not questions_batch:
                break
                
            batch_count = len(questions_batch)
            all_questions.extend(questions_batch)
            logging.info(f"Fetched {batch_count} questions (total so far: {len(all_questions)})")
            
            # If we have enough questions for the try_count, we can stop fetching
            if hasattr(self, 'try_count') and self.try_count and len(all_questions) >= self.try_count:
                all_questions = all_questions[:self.try_count]
                break
            
            if batch_count < batch_size:
                break
                
            start += batch_size
        
        # Sort questions by creation date (oldest first)
        sorted_questions = sorted(all_questions, key=lambda q: q['dateAsked'])
        
        logging.info(f"Found {len(sorted_questions)} total questions to process")
        if sorted_questions:
            oldest_date = time.strftime('%Y-%m-%d', time.localtime(sorted_questions[0]['dateAsked']/1000))
            newest_date = time.strftime('%Y-%m-%d', time.localtime(sorted_questions[-1]['dateAsked']/1000))
            logging.info(f"Date range: {oldest_date} to {newest_date}")
        
        return sorted_questions

    def get_question_details(self, question_id):
        """Fetch detailed information for a specific question.
        
        Args:
            question_id (str): The ID of the question to fetch
            
        Returns:
            dict: Detailed question data including body, comments, etc.
            
        Raises:
            requests.exceptions.HTTPError: If the API request fails
        """
        url = f"{self.base_url}/question/{question_id}"
        response = requests.get(url, auth=self.auth)
        response.raise_for_status()
        return response.json()

    def get_answers(self, question_id):
        """Fetch all answers for a specific question.
        
        Args:
            question_id (str): The ID of the question to fetch answers for
            
        Returns:
            Union[list, dict]: List of answers or dictionary containing answer results
            
        Raises:
            requests.exceptions.HTTPError: If the API request fails
            requests.exceptions.RequestException: For other request-related errors
        """
        url = f"{self.base_url}/question/{question_id}/answers"  # Note the plural 'answers'
        try:
            response = requests.get(url, auth=self.auth)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"Error 404: Answers for question ID {question_id} not found or the API endpoint might not exist.")
            raise
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching answers: {e}")
            raise

    def get_answer_details(self, answer_id):
        url = f"{self.base_url}/answer/{answer_id}"
        response = requests.get(url, auth=self.auth)
        response.raise_for_status()
        return response.json()

    def get_all_question_ids(self, space_key=None):
        """Fetch all question IDs and their creation dates using pagination.
        
        Args:
            space_key (str, optional): The Confluence space key to fetch from
            
        Returns:
            list: List of tuples (question_id, creation_date)
        """
        logging.info("Starting to fetch all question IDs from Confluence...")
        if space_key:
            logging.info(f"Using space key: {space_key}")
        
        all_questions = []
        start = 0
        batch_size = 50 
        
        while True:
            logging.info(f"Fetching questions batch starting at offset {start}...")
            questions_batch = self.fetch_questions(space_key, limit=batch_size, start=start)
            
            if not questions_batch:
                break
                
            batch_count = len(questions_batch)
            all_questions.extend(questions_batch)
            logging.info(f"Fetched {batch_count} questions (total so far: {len(all_questions)})")
            
            if batch_count < batch_size:
                break
                
            start += batch_size
        
        # Extract ID and creation date for each question
        question_data = [
            (question['id'], question['dateAsked'])
            for question in all_questions
        ]
        
        # Sort by creation date (oldest first)
        sorted_questions = sorted(question_data, key=lambda x: x[1])
        
        logging.info(f"Found {len(sorted_questions)} total questions to process")
        if sorted_questions:
            oldest_date = time.strftime('%Y-%m-%d', time.localtime(sorted_questions[0][1]/1000))
            newest_date = time.strftime('%Y-%m-%d', time.localtime(sorted_questions[-1][1]/1000))
            logging.info(f"Date range: {oldest_date} to {newest_date}")
        
        return sorted_questions
