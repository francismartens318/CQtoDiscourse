class CommentProcessor:
    def __init__(self, questions_fetcher, user_registry):
        self.questions_fetcher = questions_fetcher
        self.user_registry = user_registry

    def process_question_comments(self, question_id):
        """Process and register authors for all comments on a question.
        
        Args:
            question_id (str): ID of the question to process comments for
            
        Returns:
            dict: Question details including processed comments
        """
        question_details = self.questions_fetcher.get_question_details(question_id)
        self._register_comment_authors(question_details.get('comments', []))
        return question_details

    def process_answer_comments(self, answer_id):
        """Process and register authors for all comments on an answer.
        
        Args:
            answer_id (str): ID of the answer to process comments for
            
        Returns:
            dict: Answer details including processed comments
        """
        answer_details = self.questions_fetcher.get_answer_details(answer_id)
        self._register_comment_authors(answer_details.get('comments', []))
        return answer_details

    def _register_comment_authors(self, comments):
        """Register all comment authors with the user registry.
        
        Args:
            comments (List[dict]): List of comment data containing author information
        """
        for comment in comments:
            self.user_registry.register_user(comment.get('author')) 