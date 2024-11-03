import argparse
from ConfluenceQuestionsFetcher import ConfluenceQuestionsFetcher
from DiscourseClient import DiscourseClient
import html
import time
import os
from dotenv import load_dotenv
from pydiscourse.exceptions import DiscourseClientError, DiscourseServerError
import logging
import json
import html2text
from markdownify import markdownify as md
import requests
import re
from logger_config import setup_logger
from UserRegistry import UserRegistry
from attachment_processor import AttachmentProcessor
from content_formatter import ContentFormatter
from answer_processor import AnswerProcessor
from comment_processor import CommentProcessor

# Load environment variables from .env file
load_dotenv()

# Setup logging
logger = setup_logger()

class QuestionMigrator:
    def __init__(self, dry_run=True, try_count=None, ignore_duplicate=False):
        # Load configuration from environment variables
        confluence_url = os.getenv('CONFLUENCE_URL')
        confluence_username = os.getenv('CONFLUENCE_USERNAME')
        confluence_password = os.getenv('CONFLUENCE_PASSWORD')
        discourse_url = os.getenv('DISCOURSE_URL')
        discourse_api_key = os.getenv('DISCOURSE_API_KEY')
        discourse_api_username = os.getenv('DISCOURSE_API_USERNAME')

        # Validate that all required environment variables are set
        required_vars = [
            'CONFLUENCE_URL', 'CONFLUENCE_USERNAME', 'CONFLUENCE_PASSWORD',
            'DISCOURSE_URL', 'DISCOURSE_API_KEY', 'DISCOURSE_API_USERNAME'
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        self.questions_fetcher = ConfluenceQuestionsFetcher(confluence_url, confluence_username, confluence_password)
        self.discourse_client = DiscourseClient(discourse_url, discourse_api_key, discourse_api_username)
        self.dry_run = dry_run
        self.try_count = try_count
        self.ignore_duplicate = ignore_duplicate
        self.migrated_questions_file = 'migrated_questions.json'
        self.migrated_questions = self.load_migrated_questions()
        self.topics_created = 0
        self.confluence_url = confluence_url
        self.confluence_username = confluence_username
        self.confluence_password = confluence_password
        self.user_registry = UserRegistry()

        self.attachment_processor = AttachmentProcessor(
            confluence_url,
            (confluence_username, confluence_password),
            self.discourse_client,
            dry_run
        )
        self.content_formatter = ContentFormatter()
        self.answer_processor = AnswerProcessor(
            self.questions_fetcher,
            self.discourse_client,
            self.attachment_processor,
            self.user_registry,
            dry_run
        )
        self.comment_processor = CommentProcessor(
            self.questions_fetcher,
            self.user_registry
        )

    def load_migrated_questions(self):
        if os.path.exists(self.migrated_questions_file):
            with open(self.migrated_questions_file, 'r') as f:
                return json.load(f)
        return []

    def save_migrated_questions(self):
        with open(self.migrated_questions_file, 'w') as f:
            json.dump(self.migrated_questions, f)

    def migrate_question(self, question):
        question_id = question['id']
        if question_id in self.migrated_questions and not self.ignore_duplicate:
            print(f"Skipping already migrated question: {question['title']} (ID: {question_id})")
            return

        title = question['title']
        content = self.prepare_question_content(question)
        
        # Extract tags from the question's topics
        tags = self._extract_tags(question)

        # Register question author
        self.user_registry.register_user(question.get('author'))
        
        # Process question comments
        self.comment_processor.process_question_comments(question['id'])

        if self.dry_run:
            self.simulate_topic_creation(title, content, tags)
            return

        try:
            topic = self.discourse_client.create_topic(title, content, question['dateAsked'], tags=tags)
            print(f"Created Discourse topic: '{title}' (ID: {topic['topic_id']})")
            self.answer_processor.process_answers(question, topic['topic_id'])
            self.update_migration_status(question_id)
        except (DiscourseClientError, DiscourseServerError) as e:
            logging.error(f"Failed to create topic '{title}': {str(e)}")

        print(f"{'Would migrate' if self.dry_run else 'Migrated'} question: {title}")

    def prepare_question_content(self, question):
        question_details = self.questions_fetcher.get_question_details(question['id'])
        body = question_details.get('body', '')
        if isinstance(body, dict):
            body = body.get('content', '')
            
        processed_body = self.attachment_processor.process_attachments(body, question['id'])
        return self.content_formatter.format_question_content(question, question_details, processed_body)

    def _extract_tags(self, question):
        return [topic['name'] for topic in question.get('topics', [])] if 'topics' in question else []

    def simulate_topic_creation(self, title, content, tags=None):
        print(f"Would create Discourse topic: '{title}'")
        if tags:
            print(f"With tags: {', '.join(tags)}")
        print(f"Content preview: {content[:100]}...")

    def update_migration_status(self, question_id):
        self.migrated_questions.append(question_id)
        self.save_migrated_questions()
        self.topics_created += 1

    def run_migration(self, space_key=None):
        start = 0
        limit = 50

        print(f"{'Dry run: ' if self.dry_run else ''}Starting migration...")

        while True:
            questions = self.questions_fetcher.fetch_questions(space_key, limit, start)
            if not questions:
                break

            for question in questions:
                self.migrate_question(question)
                
                if self.try_count and self.topics_created >= self.try_count:
                    print(f"Reached the specified try count of {self.try_count}")
                    return

            if len(questions) < limit:
                break
            start += limit

        print(f"{'Dry run: ' if self.dry_run else ''}Migration completed. Total topics created/simulated: {self.topics_created}")

    def migrate_single_question(self, question_id):
        question = self.questions_fetcher.get_question_details(question_id)
        if not question:
            print(f"Question with ID {question_id} not found.")
            return
        self.migrate_question(question)
        print(f"Migration of question {question_id} completed.")

    def delete_all_topics(self):
        if self.dry_run:
            print("Dry run: Would delete migrated topics")
            return

        print("Starting to delete migrated topics...")
        
        deleted_count = 0
        failed_count = 0
        
        # Get all topics from the default migration category
        topics = self.discourse_client.list_topics_by_category()
        
        for topic in topics:
            try:
                self.discourse_client.delete_topic(topic['id'])
                deleted_count += 1
                print(f"Deleted topic ID: {topic['id']}")
                # Sleep for 1 second after every 10 deletions
                if deleted_count % 10 == 0 and deleted_count > 0:
                    time.sleep(5)
                    logging.info(f"Pausing after {deleted_count} deletions...")
            except Exception as e:
                failed_count += 1
                logging.error(f"Failed to delete topic {topic['id']}: {str(e)}")
        
        print(f"Topic deletion completed. Deleted {deleted_count} topics. Failed to delete {failed_count} topics.")

def main():
    parser = argparse.ArgumentParser(description='Migrate questions from Confluence to Discourse.')
    parser.add_argument('--dry-run', action='store_true', help='Perform a dry run without actually creating topics')
    parser.add_argument('--do-run', action='store_true', help='Actually perform the migration (sets dry-run to false, ignores try-count, and does not ignore duplicates)')
    parser.add_argument('--try-count', type=int, default=2, help='Number of topics to attempt to create (default: 2, ignored if --do-run is set)')
    parser.add_argument('--question-id', type=str, help='ID of a single question to migrate')
    parser.add_argument("--ignore-duplicate", action="store_true", help="Ignore duplicate question check")
    parser.add_argument('--delete-all-topics', action='store_true', help='Delete all topics in Discourse')

    args = parser.parse_args()

    # If question-id is provided, ignore dry-run and try-count
    if args.question_id:
        migrator = QuestionMigrator(dry_run=False, try_count=None, ignore_duplicate=True)
        migrator.migrate_single_question(args.question_id)
    elif args.delete_all_topics:
        migrator = QuestionMigrator(dry_run=args.dry_run)
        migrator.delete_all_topics()
    else:
        # Logic for bulk migration
        if args.do_run:
            args.dry_run = False
            args.try_count = None
            args.ignore_duplicate = False
            print("Do run specified. Dry run disabled, try count ignored, and duplicates will not be ignored.")
        elif args.try_count is not None:
            args.dry_run = False
            print(f"Try count set to {args.try_count}. Dry run disabled.")
        
        space_key = os.getenv('CONFLUENCE_SPACE_KEY')
        
        migrator = QuestionMigrator(dry_run=args.dry_run, try_count=args.try_count, ignore_duplicate=args.ignore_duplicate)
        migrator.run_migration(space_key)

if __name__ == "__main__":
    main()
