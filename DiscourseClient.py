import requests
import json
import tempfile
import os
from pydiscourse.client import DiscourseClient as BaseDiscourseClient
from pydiscourse.exceptions import DiscourseClientError


class DiscourseClient:
    def __init__(self, base_url, api_key, api_username, default_category_name="Migrated Questions"):
        self.base_url = base_url
        self.api_key = api_key
        self.api_username = api_username
        self.client = BaseDiscourseClient(
            host=base_url,
            api_username=api_username,
            api_key=api_key
        )

        # Set up the default category
        self.default_category_id = self.get_or_create_category(default_category_name)

    def get_or_create_category(self, category_name):
        # Get all categories
        categories = self.client.categories()
        
        # Search for the category by name
        for category in categories:
            if category['name'] == category_name:
                return category['id']
        
        # If the category doesn't exist, create it
        new_category = self.client.create_category(
            name=category_name,
            color="0088CC",  # You can change this default color
            text_color="FFFFFF"  # You can change this default text color
        )
        return new_category['category']['id']

    def create_topic(self, title, raw_content, date_asked=None, category_id=None):
        try:
            create_post_params = {
                'content': raw_content,
                'title': title,
                'category_id': category_id or self.default_category_id,
                #'created_at': date_asked.isoformat() if date_asked else None,
            }

            topic = self.client.create_post(**create_post_params)
            return topic
        except DiscourseClientError as e:
            print(f"Error creating topic '{title}': {str(e)}")
            # You might want to log this error or handle it in a specific way
            # For now, we'll re-raise the exception
            raise

    def create_post(self, topic_id, raw_content):
        post = self.client.create_post(
            topic_id=topic_id,
            content=raw_content
        )
        return post

    def accept_solution(self, topic_id, post_id):
        """
        Mark a post as the accepted solution for a topic.

        Args:
            topic_id (int): The ID of the topic that contains the post.
            post_id (int): The ID of the post to mark as the solution.

        Returns:
            dict: The response from the Discourse API.
        """
        data = {
            "id": post_id,
            "topic_id": topic_id,
            "post_id": post_id
        }
        return self.client._put("/solution/accept.json",json=True, **data)

    def upload_file(self, filename, file_content):
        """
        Upload a file to Discourse if it has an allowed extension.

        Args:
            filename (str): The name of the file to be uploaded.
            file_content (bytes): The content of the file to be uploaded.

        Returns:
            tuple: (upload_response, message)
                upload_response (dict): The response from the Discourse API containing the upload details,
                                        or None if the file type is not supported.
                message (str): A message to be inserted into the body content if the file couldn't be uploaded,
                               or None if the upload was successful.
        """
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'heic', 'heif', 'webp', 'avif'}
        file_extension = filename.lower().split('.')[-1]

        if file_extension not in allowed_extensions:
            return None, f"\n\n*A file named '{filename}' was present in the original content but couldn't be uploaded due to unsupported file type.*\n\n   "

        try:
            # Create a temporary file to store the content
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            # Use the upload_image method from the client
            response = self.client.upload_image(
                image=temp_file_path,
                upload_type="composer",
                synchronous=True
            )

            # Remove the temporary file
            os.unlink(temp_file_path)

            return response, None
        except Exception as e:
            return None, f"\n\n[Error uploading file '{filename}': {str(e)}]"
    # Add more methods as needed, using self.client to interact with the API
