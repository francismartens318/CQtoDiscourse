import re
import requests
from markdownify import markdownify as md

class AttachmentProcessor:
    def __init__(self, confluence_url, confluence_auth, discourse_client, dry_run=True):
        self.confluence_url = confluence_url
        self.confluence_auth = confluence_auth
        self.discourse_client = discourse_client
        self.dry_run = dry_run

    def process_attachments(self, body, content_id):
        img_tags = re.findall(r'<img.*?>', body)
        message = ""
        missing_file_sep = ""
        
        for img_tag in img_tags:
            src_match = re.search(r'src="(.*?)"', img_tag)
            if not src_match:
                print(f"Warning: Couldn't find src attribute in img tag: {img_tag}")
                continue
            
            body, message, missing_file_sep = self._process_single_attachment(
                body, content_id, img_tag, src_match, message, missing_file_sep
            )
        
        return self._format_final_content(body, message)

    def _process_single_attachment(self, body, content_id, img_tag, src_match, message, missing_file_sep):
        img_src = src_match.group(1)
        filename = f"attachment_{content_id}_{img_src.split('/')[-1].split('?')[0]}"
        full_url = self._get_full_url(img_src)
        
        if self.dry_run:
            print(f"Would download and upload attachment: {filename} from {full_url}")
            return body, message, missing_file_sep

        return self._handle_attachment_upload(body, img_tag, img_src, filename, full_url, message, missing_file_sep)

    def _get_full_url(self, img_src):
        return img_src if img_src.startswith(('http://', 'https://')) else f"{self.confluence_url}{img_src}"

    def _handle_attachment_upload(self, body, img_tag, img_src, filename, full_url, message, missing_file_sep):
        try:
            response = requests.get(full_url, auth=self.confluence_auth)
            response.raise_for_status()
            
            upload, missing_file = self.discourse_client.upload_file(filename, response.content)

            if upload and 'url' in upload:
                body = body.replace(img_src, upload['url'])
                print(f"Uploaded attachment: {filename}")
            else:
                body = body.replace(img_tag, '')
                message += missing_file_sep + missing_file
                missing_file_sep = "\n\n"
                print(f"Couldn't upload attachment: {filename}")
        except requests.exceptions.RequestException as e:
            body = body.replace(img_tag, '')
            message += f"\n\n[Failed to download attachment: {filename}. Error: {str(e)}]"
            print(f"Failed to download attachment: {filename}. Error: {str(e)}")
            
        return body, message, missing_file_sep

    def _format_final_content(self, body, message):
        return md(body) + "\n\n---\n\n" + message + "\n\n" 