import time
import html
from markdownify import markdownify as md
import re
import emoji  # You'll need to install this package: pip install emoji

class ContentFormatter:
    def __init__(self, base_url='https://oldcommunity.exalate.com'):
        self.base_url = base_url.rstrip('/')

    def process_links(self, content):
        # Process markdown-style links
        pattern = r'\[([^\]]+)\]\((/[^)]+)\)'
        replacement = rf'[\1 (_old community_)]({self.base_url}\2)'
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
        author = question['author']['fullName']
        date_asked = time.strftime('%d %B %Y', time.localtime(question['dateAsked']/1000))
        
        # Add link to original question
        original_link = f"{self.base_url}/questions/{question['id']}"
        content = f"*Originally asked by {author} on {date_asked}*\n*<sub>View [question on old community]({original_link})</sub>*\n\n---\n\n"
        
        # Process the body content to update relative links and convert emojis
        processed_body = self.process_links(processed_body)
        
        content += processed_body
        content += self.format_comments(question_details.get('comments', []))
        return content

    def format_answer_content(self, answer_details, processed_body):
        author = answer_details['author']['fullName']
        date = time.strftime('%d %B %Y', time.localtime(answer_details['dateAnswered']/1000))
        content = f"*Answer by {author} on {date}*\n\n"
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
            author = comment['author']['fullName']
            date = time.strftime('%d %B %Y', time.localtime(comment['dateCommented']/1000))
            body = self.html_to_markdown(comment.get('body', {}).get('content', ''))
            # Process the comment content to update relative links and convert emojis
            body = self.process_links(body)
            body = self.convert_emojis(body)
            formatted_comments += f"\n[details=\"{author} commented on {date}\"]\n> {body}\n[/details]\n"
        return formatted_comments 