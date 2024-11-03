import requests
from atlassian import Confluence
from typing import Union

class ConfluenceQuestionsFetcher:
    def __init__(self, confluence_url, confluence_username, confluence_password):
        self.confluence = Confluence(
            url=confluence_url,
            username=confluence_username,
            password=confluence_password
        )
        self.base_url = confluence_url.rstrip('/') + '/rest/questions/1.0'
        self.auth = (confluence_username, confluence_password)

    def fetch_questions(self, space_key=None, limit=50, start=0):
        """Fetch a batch of questions from Confluence.
        
        Args:
            space_key (str, optional): The Confluence space key to fetch from
            limit (int, optional): Maximum number of questions to fetch (default: 50)
            start (int, optional): Starting offset for pagination (default: 0)
            
        Returns:
            list: List of question data dictionaries
            
        Raises:
            requests.exceptions.HTTPError: If the API request fails
        """
        url = f"{self.base_url}/question"
        params = {
            'limit': limit,
            'start': start,
            'spaceKey': space_key
        }
        response = requests.get(url, params=params, auth=self.auth)
        response.raise_for_status()
        return response.json()

    def get_all_questions(self, space_key=None):
        """Fetch all questions from Confluence using pagination.
        
        Args:
            space_key (str, optional): The Confluence space key to fetch from
            
        Returns:
            list: Complete list of all question data dictionaries
        """
        all_questions = []
        start = 0
        limit = 50

        while True:
            questions = self.fetch_questions(space_key, limit, start)
            if not questions:
                break
            all_questions.extend(questions)
            if len(questions) < limit:
                break
            start += limit

        return all_questions

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
