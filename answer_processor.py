import logging
from content_formatter import ContentFormatter

class AnswerProcessor:
    def __init__(self, questions_fetcher, discourse_client, attachment_processor, user_registry, content_formatter, dry_run=True):
        self.questions_fetcher = questions_fetcher
        self.discourse_client = discourse_client
        self.attachment_processor = attachment_processor
        self.user_registry = user_registry
        self.dry_run = dry_run
        self.content_formatter = content_formatter

    def process_answers(self, question, topic_id):
        """Process all answers for a given question and add them to the Discourse topic.
        
        Args:
            question (dict): The question data containing answers
            topic_id (int): The Discourse topic ID to add answers to
        """
        if question['answersCount'] <= 0:
            return

        answers = self.questions_fetcher.get_answers(question['id'])
        if isinstance(answers, list):
            self._process_answer_list(answers, topic_id, question['title'])
        elif isinstance(answers, dict) and 'results' in answers:
            self._process_answer_list(answers['results'], topic_id, question['title'])
        else:
            logging.warning(f"Unexpected format for answers: {type(answers)}")

    def _process_answer_list(self, answers, topic_id, title):
        """Process a list of answers and add them to the topic.
        
        Args:
            answers (List[dict]): List of answer data
            topic_id (int): The Discourse topic ID
            title (str): The topic title for logging
        """
        for answer in answers:
            self.user_registry.register_user(answer.get('author'))
            self.add_answer_to_topic(topic_id, answer, title)

    def add_answer_to_topic(self, topic_id, answer, title):
        """Add a single answer as a post to a Discourse topic.
        
        Args:
            topic_id (int): The Discourse topic ID
            answer (dict): The answer data to add
            title (str): The topic title for logging
        """
        answer_id = answer['id']
        answer_details = self.questions_fetcher.get_answer_details(answer_id)
        answer_content = self._prepare_answer_content(answer_details)
        
        if self.dry_run:
            print(f"Would add answer to topic '{title}'")
            print(f"Answer preview: {answer_content[:100]}...")
            return

        post = self.discourse_client.create_post(topic_id, answer_content)
        print(f"Added answer to topic '{title}'")
        
        if answer_details.get('accepted', True):
            self._mark_answer_as_solution(topic_id, post['id'])

    def _prepare_answer_content(self, answer_details):
        body = answer_details.get('body', '')
        if isinstance(body, dict):
            body = body.get('content', '')
            
        # Convert emojis before processing attachments
        body = self.content_formatter.convert_emojis(body)
        processed_body = self.attachment_processor.process_attachments(body, answer_details['id'])
        return self.content_formatter.format_answer_content(answer_details, processed_body)

    def _mark_answer_as_solution(self, topic_id, post_id):
        
        if self.dry_run:
            print(f"Would mark post {post_id} as solution for topic {topic_id}")
            return

        try:
            self.discourse_client.accept_solution(topic_id, post_id)
            print(f"Marked post {post_id} as solution for topic {topic_id}")
        except Exception as e:
            logging.error(f"Failed to mark post {post_id} as solution: {str(e)}") 