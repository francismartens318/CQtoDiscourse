class QuirksHandler:
    """Handles special cases and quirks related to source data."""
    
    def __init__(self):
        # Dictionary of known user replacements
        self.user_replacements = {
            # Confluence user ID -> Display name
            'user-abcd': 'John Doe',
            'legacy_user': 'Jane Smith'
        }
    
    def get_display_name(self, author_data):
        """
        Get the display name for a user, handling any special cases.
        
        Args:
            author_data (dict): Dictionary containing user data with at least 'fullName'
            
        Returns:
            str: The display name to use for the user
        """
        full_name = author_data.get('fullName', '')
        return self.user_replacements.get(full_name, full_name) 