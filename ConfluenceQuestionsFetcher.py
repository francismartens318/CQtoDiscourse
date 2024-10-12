from atlassian import Confluence

class ConfluenceQuestionsFetcher:
    def __init__(self, confluence_url, confluence_username, confluence_password):
        self.confluence = Confluence(
            url=confluence_url,
            username=confluence_username,
            password=confluence_password
        )

    def fetch_questions(self, space_key=None, limit=50, start=0):
        # This method needs to be implemented based on the specific Confluence Questions API
        # The following is a placeholder and needs to be replaced with actual API calls
        questions = self.confluence.get_all_questions(space_key, limit=limit, start=start)
        return questions

    def get_all_questions(self, space_key=None):
        all_questions = []
        start = 0
        limit = 50

        while True:
            questions = self.fetch_questions(space_key, limit, start)
            if not questions:
                break
            all_questions.extend(questions)
            start += limit

        return all_questions
