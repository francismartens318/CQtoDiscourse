class CommentProcessor:
    def __init__(self, questions_fetcher, user_registry):
        self.questions_fetcher = questions_fetcher
        self.user_registry = user_registry

    def process_question_comments(self, question_id):
        question_details = self.questions_fetcher.get_question_details(question_id)
        self._register_comment_authors(question_details.get('comments', []))
        return question_details

    def process_answer_comments(self, answer_id):
        answer_details = self.questions_fetcher.get_answer_details(answer_id)
        self._register_comment_authors(answer_details.get('comments', []))
        return answer_details

    def _register_comment_authors(self, comments):
        for comment in comments:
            self.user_registry.register_user(comment.get('author')) 