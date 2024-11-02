import csv
import os

class UserRegistry:
    def __init__(self, registry_file='user_registry.csv'):
        self.registry_file = registry_file
        self.registry = self.load_registry()

    def load_registry(self):
        """Load existing user registry or create new one"""
        registry = {}
        if os.path.exists(self.registry_file):
            with open(self.registry_file, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    registry[row['username']] = row['email']
        return registry

    def save_registry(self):
        """Save user registry to CSV file"""
        with open(self.registry_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['FullName', 'username', 'email'])
            writer.writeheader()
            for fullname, username in self.registry.items():
                writer.writerow({'FullName': fullname, 'username': username})

    def register_user(self, user_data):
        """Register a user in the registry"""
        if not user_data:
            return
        
        username = user_data.get('name')  # This could be email or username
        full_name = user_data.get('fullName')
        email = None

        # Check if username contains @ or if email is provided
        if '@' in (username or ''):
            email = username
        else:
            email = user_data.get('email')  # Try to get email from data
        
        if not username or username in self.registry:
            return
        # Validate and clean email

            
        # Store all three attributes
        self.registry[full_name] = {
            'username': username,
            'email': email,
            'full_name': full_name
        }



        self.registry[full_name] = username  # Store full name as key, email as value
        self.save_registry()

    def get_user(self, username):
        """Get user details from registry"""
        return self.registry.get(username)

    def get_all_users(self):
        """Get all registered users"""
        return self.registry 