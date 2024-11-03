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

    def load_migrated_questions(self):
        if os.path.exists(self.migrated_questions_file):
            with open(self.migrated_questions_file, 'r') as f:
                return json.load(f)
        return []

    def save_migrated_questions(self):
        with open(self.migrated_questions_file, 'w') as f:
            json.dump(self.migrated_questions, f)

    def html_to_markdown(self, html_content):
        # Unescape HTML entities first
        unescaped_html = html.unescape(html_content)
        # Convert HTML to Markdown
        return md(unescaped_html, heading_style="ATX").strip()

    def migrate_question(self, question):
        question_id = question['id']
        if question_id in self.migrated_questions and not self.ignore_duplicate:
            print(f"Skipping already migrated question: {question['title']} (ID: {question_id})")
            return

        title = question['title']
        content = self.prepare_question_content(question)
        
        # Extract tags from the question's topics
        tags = []
        if 'topics' in question and question['topics']:
            tags = [topic['name'] for topic in question['topics']]

        # Register question author
        self.user_registry.register_user(question.get('author'))
        
        # Get question details to register commenters
        question_details = self.questions_fetcher.get_question_details(question['id'])
        for comment in question_details.get('comments', []):
            self.user_registry.register_user(comment.get('author'))

        if self.dry_run:
            self.simulate_topic_creation(title, content, tags)
        else:
            try:
                topic = self.discourse_client.create_topic(title, content, question['dateAsked'], tags=tags)
                print(f"Created Discourse topic: '{title}' (ID: {topic['topic_id']})")
                self.process_answers(question, topic['topic_id'])
                self.update_migration_status(question_id)
            except (DiscourseClientError, DiscourseServerError) as e:
                logging.error(f"Failed to create topic '{title}': {str(e)}")
                return

        print(f"{'Would migrate' if self.dry_run else 'Migrated'} question: {title}")

    def prepare_question_content(self, question):
        author = question['author']['fullName']
        date_asked = time.strftime('%d %B %Y', time.localtime(question['dateAsked']/1000))
        content = f"*Originally asked by {author} on {date_asked}*\n\n---\n\n"
        
        question_details = self.questions_fetcher.get_question_details(question['id'])
        body = question_details.get('body', '')
        if isinstance(body, dict):
            body = body.get('content', '')
        content += self.process_attachments(body, question['id'])
        
        content += self.format_comments(question_details.get('comments', []))
        return content

    def format_comments(self, comments):
        if not comments:
            return ""
        
        formatted_comments = "\n\n#### Comments:\n"
        for comment in comments:
            author = comment['author']['fullName']
            date = time.strftime('%d %B %Y', time.localtime(comment['dateCommented']/1000))
            body = self.html_to_markdown(comment.get('body', {}).get('content', ''))
            formatted_comments += f"\n[details=\"{author} commented on {date}\"]\n> {body}\n[/details]\n"
        return formatted_comments

    def process_answers(self, question, topic_id):
        if question['answersCount'] > 0:
            answers = self.questions_fetcher.get_answers(question['id'])
            if isinstance(answers, list):
                for answer in answers:
                    # Register answer author
                    self.user_registry.register_user(answer.get('author'))
                    self.add_answer_to_topic(topic_id, answer, question['title'])
            elif isinstance(answers, dict) and 'results' in answers:
                for answer in answers['results']:
                    # Register answer author
                    self.user_registry.register_user(answer.get('author'))
                    self.add_answer_to_topic(topic_id, answer, question['title'])
            else:
                print(f"Unexpected format for answers: {type(answers)}")

    def add_answer_to_topic(self, topic_id, answer, title):
        answer_id = answer['id']
        answer_details = self.questions_fetcher.get_answer_details(answer_id)
        answer_content = self.prepare_answer_content(answer_details)
        
        if self.dry_run:
            print(f"Would add answer to topic '{title}'")
            print(f"Answer preview: {answer_content[:100]}...")
        else:
            post = self.discourse_client.create_post(topic_id, answer_content)
            print(f"Added answer to topic '{title}'")
            
            # Check if the answer is accepted
            if answer_details.get('accepted', False):
                self.mark_answer_as_solution(topic_id, post['id'])

    def prepare_answer_content(self, answer_details):
        author = answer_details['author']['fullName']
        date = time.strftime('%d %B %Y', time.localtime(answer_details['dateAnswered']/1000))
        content = f"*Answer by {author} on {date}*\n\n"
        
        body = answer_details.get('body', '')
        if isinstance(body, dict):
            body = body.get('content', '')
        content += self.process_attachments(body, answer_details['id'])
        
        content += self.format_comments(answer_details.get('comments', []))
        return content

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

    def mark_answer_as_solution(self, topic_id, post_id):
        # not possible to mark answer as solution in Discourse yet
        
        return
        if self.dry_run:
            print(f"Would mark post {post_id} as solution for topic {topic_id}")
        else:
            try:
                self.discourse_client.accept_solution(topic_id, post_id)
                print(f"Marked post {post_id} as solution for topic {topic_id}")
            except Exception as e:
                print(f"Failed to mark post {post_id} as solution: {str(e)}")

    def process_attachments(self, body, content_id):
        # Find all image tags in the body
        img_tags = re.findall(r'<img.*?>', body)
        message = ""
        missing_file_sep = ""
        
        for img_tag in img_tags:
            src_match = re.search(r'src="(.*?)"', img_tag)
            if not src_match:
                print(f"Warning: Couldn't find src attribute in img tag: {img_tag}")
                continue
            
            img_src = src_match.group(1)
            # Generate a unique filename
            filename = f"attachment_{content_id}_{img_src.split('/')[-1].split('?')[0]}"
            
            # Determine if the URL is absolute or relative
            if img_src.startswith(('http://', 'https://')):
                full_url = img_src
            else:
                full_url = f"{self.confluence_url}{img_src}"
            
            if self.dry_run:
                print(f"Would download and upload attachment: {filename} from {full_url}")
            else:
                try:
                    # Download the image
                    response = requests.get(full_url, auth=(self.confluence_username, self.confluence_password))
                    response.raise_for_status()
                    
                    # Upload the image to Discourse
                    upload, missing_file = self.discourse_client.upload_file(filename, response.content)

                    if upload and 'url' in upload:
                        # Replace the original URL with the Discourse URL in the body
                        body = body.replace(img_src, upload['url'])
                        print(f"Uploaded attachment: {filename}")
                    else:
                        # Remove the img tag and append the message if the file couldn't be uploaded
                        body = body.replace(img_tag, '')
                        message += missing_file_sep + missing_file
                        missing_file_sep = "\n\n"
                    print(f"Couldn't upload attachment: {filename}")
                except requests.exceptions.RequestException as e:
                    # Remove the img tag and add an error message
                    body = body.replace(img_tag, '')
                    body += f"\n\n[Failed to download attachment: {filename}. Error: {str(e)}]"
                    print(f"Failed to download attachment: {filename}. Error: {str(e)}")
        
        return self.html_to_markdown(body) + "\n\n---\n\n"+ message + "\n\n"

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
