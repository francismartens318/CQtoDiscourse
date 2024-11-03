import requests
import json
import tempfile
import os
import logging

from pydiscourse.client import DiscourseClient as BaseDiscourseClient
from pydiscourse.exceptions import DiscourseClientError
from typing import List, Optional
from time import sleep
from DiscourseCategoryManager import DiscourseCategoryManager
from DiscourseTagManager import DiscourseTagManager


class DiscourseClient:
    def __init__(self, host, api_key, api_username):
        """Initialize the Discourse client.
        
        Args:
            host (str): The Discourse host URL
            api_username (str): The Discourse API username
            api_key (str): The Discourse API key
            default_category_id (int, optional): Default category ID for operations
        """
        # Setup logging for pydiscourse
        
        
        self.client = BaseDiscourseClient(
            host=host,
            api_username=api_username,
            api_key=api_key
        )

        # Initialize managers
        self.category_manager = DiscourseCategoryManager(self.client)
        self.tag_manager = DiscourseTagManager(self.client)

    def create_topic(self, title, raw_content, date_asked=None, category_id=None, tags=None):
        """Create a new topic in Discourse.
        
        Args:
            title (str): The title of the topic
            raw_content (str): The content/body of the topic
            date_asked (datetime, optional): Original creation date
            category_id (int, optional): Category ID to place the topic in
            tags (List[str], optional): List of tags to apply to the topic
            
        Returns:
            dict: The created topic response from Discourse
            
        Raises:
            DiscourseClientError: If topic creation fails
        """
        try:
            # Ensure tags is a list
            tags = tags or []
            
            # Add migrated_question tag
            if 'migrated_question' not in tags:
                tags.append('migrated_question')
                
            # Determine category if not explicitly provided
            if category_id is None:
                category_id = self.category_manager.determine_category(tags)
                
            create_post_params = {
                'content': raw_content,
                'title': title,
                'category_id': category_id,
            }

            cleaned_tags = [self.tag_manager.clean_tag_name(tag) for tag in tags]
            topic = self.client.create_post(**create_post_params, tags=cleaned_tags)

            return topic
        except DiscourseClientError as e:
            print(f"Error creating topic '{title}': {str(e)}")
            raise

    def create_post(self, topic_id, raw_content):
        """Create a new post within an existing topic.
        
        Args:
            topic_id (int): The ID of the topic to add the post to
            raw_content (str): The content of the post
            
        Returns:
            dict: The created post response from Discourse
        """
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
        }
        return self.client._post("/solution/accept",json=True, **data)

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

    def delete_topic(self, topic_id: int) -> dict:
        """Delete a topic by its ID.
        
        Args:
            topic_id (int): The ID of the topic to delete
            
        Returns:
            dict: Response from the server
        """
        return self.client.delete_topic(topic_id)

    def get_topics(self):
        """Fetch all topics from Discourse"""
        response = self.client.get('/latest.json')
        return response.get('topic_list', {}).get('topics', [])

    def list_topics_by_category(self, category_id: int = None, category_slug: str = None) -> List[dict]:
        """Fetch all topics from a specific category with pagination.
        
        Args:
            category_id (int, optional): The ID of the category to fetch topics from
            category_slug (str, optional): The slug of the category
            
        Returns:
            List[dict]: List of topics in the category
            
        Raises:
            DiscourseClientError: If the API request fails
        """
        if category_id is None and category_slug is None:
            # Use general category as default
            category_id = self.category_manager.get_category_id('general')
            category_slug = self.category_manager.get_category_slug('general')
        
        all_topics = []
        page = 0
        
        while True:
            try:
                response = self.client._get(
                    f"/c/{category_id}/l/latest.json?page={page}"
                )
            except DiscourseClientError as e:
                if e.response.status_code == 400:
                    page += 1
                    continue
                raise
            
            if not response or 'topic_list' not in response:
                break
                
            topics = response['topic_list'].get('topics', [])
            if not topics:
                break
                
            all_topics.extend(topics)
            page += 1
            logging.info(f"Fetched page {page}, having {len(all_topics)} topics, last topic: {topics[-1]['title']}")
            sleep(5)  # Sleep for 5 seconds between page fetches

        return all_topics

    # Add more methods as needed, using self.client to interact with the API
