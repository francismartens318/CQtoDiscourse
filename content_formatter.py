import time
import html
from markdownify import markdownify as md

class ContentFormatter:
    @staticmethod
    def html_to_markdown(html_content):
        unescaped_html = html.unescape(html_content)
        return md(unescaped_html, heading_style="ATX").strip()

    @staticmethod
    def format_question_content(question, question_details, processed_body):
        author = question['author']['fullName']
        date_asked = time.strftime('%d %B %Y', time.localtime(question['dateAsked']/1000))
        content = f"*Originally asked by {author} on {date_asked}*\n\n---\n\n"
        content += processed_body
        content += ContentFormatter.format_comments(question_details.get('comments', []))
        return content

    @staticmethod
    def format_answer_content(answer_details, processed_body):
        author = answer_details['author']['fullName']
        date = time.strftime('%d %B %Y', time.localtime(answer_details['dateAnswered']/1000))
        content = f"*Answer by {author} on {date}*\n\n"
        content += processed_body
        content += ContentFormatter.format_comments(answer_details.get('comments', []))
        return content

    @staticmethod
    def format_comments(comments):
        if not comments:
            return ""
        
        formatted_comments = "\n\n#### Comments:\n"
        for comment in comments:
            author = comment['author']['fullName']
            date = time.strftime('%d %B %Y', time.localtime(comment['dateCommented']/1000))
            body = ContentFormatter.html_to_markdown(comment.get('body', {}).get('content', ''))
            formatted_comments += f"\n[details=\"{author} commented on {date}\"]\n> {body}\n[/details]\n"
        return formatted_comments 