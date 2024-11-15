import time
import html
from markdownify import markdownify as md
import re
import emoji  # You'll need to install this package: pip install emoji
from quirks_handler import QuirksHandler

class ContentFormatter:
    def __init__(self, base_url='https://oldcommunity.example.com'):
        self.base_url = base_url.rstrip('/')
        self.quirks_handler = QuirksHandler()

    def process_links(self, content):
        # First handle user profile links
        user_pattern = r'\[([^\]]+)\]\(/display/~[^\)]+\)'
        content = re.sub(user_pattern, r'\1', content)
        
        # Then process regular markdown-style links
        pattern = r'\[([^\]]+)\]\((/[^)]+)\)'
        replacement = rf'[\1]({self.base_url}\2)  <small>_(old community)_</small>'
        content = re.sub(pattern, replacement, content)
        return content

    def html_to_markdown(self, html_content):
        unescaped_html = html.unescape(html_content)
        return md(unescaped_html, heading_style="ATX").strip()

    def convert_emojis(self, content):
        # Convert Confluence emoji HTML to Discourse format
        pattern = r'<img[^>]*data-emoji-short-name="([^"]*)"[^>]*/>'
        return re.sub(pattern, r'\1', content)

    def format_question_content(self, question, question_details, processed_body):
        # replace user IDs with display names
        author = self.quirks_handler.get_display_name(question['author'])
        date_asked = time.strftime('%d %B %Y', time.localtime(question['dateAsked']/1000))
        
        # Add link to original question
        original_link = f"{self.base_url}/questions/{question['id']}"
        content = f"<small>_Originally asked by {author} on {date_asked} [(original question)]({original_link})_</small>\n\n---\n\n"
        
        # Process the body content to update relative links and convert emojis
        processed_body = self.process_links(processed_body)
        
        content += processed_body
        content += self.format_comments(question_details.get('comments', []))
        return content

    def format_answer_content(self, answer_details, processed_body):
        # Replace specific user IDs with display names
        author = self.quirks_handler.get_display_name(answer_details['author'])
        date = time.strftime('%d %B %Y', time.localtime(answer_details['dateAnswered']/1000))
        content = f"<small>*Answer by {author} on {date}*</small>\n\n\n\n"
        
        # Process the body content to update relative links and convert emojis
        processed_body = self.process_links(processed_body)
        content += processed_body
        content += self.format_comments(answer_details.get('comments', []))
        return content

    def format_comments(self, comments):
        if not comments:
            return ""
        
        formatted_comments = "\n\n#### Comments:\n"
        for comment in comments:
            # Replace specific user IDs with display names
            author = self.quirks_handler.get_display_name(comment['author'])
            date = time.strftime('%d %B %Y', time.localtime(comment['dateCommented']/1000))
            body = self.html_to_markdown(comment.get('body', {}).get('content', ''))
            # Process the comment content to update relative links and convert emojis
            body = self.process_links(body)
            body = self.convert_emojis(body)
            formatted_comments += f"\n[details=\"{author} commented on {date}\"]\n> {body}\n[/details]\n"
        return formatted_comments 