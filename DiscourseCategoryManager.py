from typing import Dict, Optional
from pydiscourse.exceptions import DiscourseClientError

class DiscourseCategoryManager:
    def __init__(self, client):
        """Initialize the category manager.
        
        Args:
            client: The base Discourse client instance
        """
        self.client = client
        
        # Define category names
        self.categories = {
            'use_case': 'Use Case',
            'general': 'General Questions'
        }
        
        self.category_ids = {}
        self.category_slugs = {}
        
        # Set up the categories
        self.setup_categories()

    def setup_categories(self) -> None:
        """Set up all required categories."""
        # Get all categories
        categories = self.client.categories()
        
        for category_key, category_name in self.categories.items():
            # Search for existing category
            category_found = False
            for category in categories:
                if category['name'] == category_name:
                    self.category_ids[category_key] = category['id']
                    self.category_slugs[category_key] = category['slug']
                    category_found = True
                    break
            
            # Create category if it doesn't exist
            if not category_found:
                self._create_category(category_key, category_name)

    def _create_category(self, key: str, name: str) -> None:
        """Create a new category in Discourse.
        
        Args:
            key (str): Internal key for the category
            name (str): Display name for the category
        """
        new_category = self.client.create_category(
            name=name,
            color="0088CC",
            text_color="FFFFFF"
        )
        self.category_ids[key] = new_category['category']['id']
        self.category_slugs[key] = new_category['category']['slug']

    def determine_category(self, tags: Optional[list] = None) -> int:
        """Determine which category to use based on tags.
        
        Args:
            tags (list, optional): List of tags to check
            
        Returns:
            int: The ID of the determined category
        """
        tags = tags or []
        return self.category_ids['use_case'] if 'usecase' in tags else self.category_ids['general']

    def get_category_id(self, key: str) -> Optional[int]:
        """Get category ID by key.
        
        Args:
            key (str): The category key
            
        Returns:
            int: The category ID, or None if not found
        """
        return self.category_ids.get(key)

    def get_category_slug(self, key: str) -> Optional[str]:
        """Get category slug by key.
        
        Args:
            key (str): The category key
            
        Returns:
            str: The category slug, or None if not found
        """
        return self.category_slugs.get(key) 