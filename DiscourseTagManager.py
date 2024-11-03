import requests
import json
import tempfile
import os
from pydiscourse.client import DiscourseClient as BaseDiscourseClient
from pydiscourse.exceptions import DiscourseClientError
from typing import List, Optional
import logging
from time import sleep


class DiscourseTagManager:
    def __init__(self, client):
        self.client = client
        
    def clean_tag_name(self, tag: str) -> str:
        """Clean tag name to fit Discourse requirements.
        
        Args:
            tag (str): Original tag name
            
        Returns:
            str: Cleaned tag name that fits Discourse requirements
        """
        # Remove 'connector-' prefix and limit to 20 chars
        tag = tag.replace('connector-', '')
        return tag[:20]
    
    def create_tag(self, tag_name: str) -> Optional[dict]:
        """Create a new tag in Discourse if it doesn't exist.
        
        Args:
            tag_name (str): Name of the tag to create
            
        Returns:
            Optional[dict]: Response from tag creation or None if tag exists
            
        Raises:
            DiscourseClientError: If tag creation fails for reasons other than existence
        """
        try:
            cleaned_tag = self.clean_tag_name(tag_name)
            return self.client._post(
                "/tags.json",
                tag={"name": cleaned_tag}
            )
        except DiscourseClientError as e:
            if "already exists" not in str(e):
                print(f"Error creating tag '{tag_name}': {str(e)}")
            return None
            
    def ensure_tags_exist(self, tags: List[str]) -> List[str]:
        """Ensure all tags exist in Discourse, creating them if necessary.
        
        Args:
            tags (List[str]): List of tag names to ensure exist
            
        Returns:
            List[str]: List of cleaned tag names
        """
        cleaned_tags = [self.clean_tag_name(tag) for tag in tags]
        for tag in cleaned_tags:
            self.create_tag(tag)
        return cleaned_tags
        
    def add_tags_to_topic(self, topic_id: int, tags: List[str]) -> dict:
        """Add tags to an existing Discourse topic.
        
        Args:
            topic_id (int): ID of the topic to tag
            tags (List[str]): List of tags to add
            
        Returns:
            dict: Response from the Discourse API
        """
        cleaned_tags = self.ensure_tags_exist(tags)
        return self.client._put(
            f"/t/{topic_id}.json",
            tags=cleaned_tags
        )