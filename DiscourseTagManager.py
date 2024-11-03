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
        """Clean tag name to fit Discourse requirements"""
        # Remove 'connector-' prefix and limit to 20 chars
        tag = tag.replace('connector-', '')
        return tag[:20]
    
    def create_tag(self, tag_name: str) -> Optional[dict]:
        """Create a new tag if it doesn't exist"""
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
        """Create tags if they don't exist and return cleaned tag names"""
        cleaned_tags = [self.clean_tag_name(tag) for tag in tags]
        for tag in cleaned_tags:
            self.create_tag(tag)
        return cleaned_tags
        
    def add_tags_to_topic(self, topic_id: int, tags: List[str]) -> dict:
        """Add tags to a topic"""
        cleaned_tags = self.ensure_tags_exist(tags)
        return self.client._put(
            f"/t/{topic_id}.json",
            tags=cleaned_tags
        )