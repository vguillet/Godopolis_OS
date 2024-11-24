import csv
import os
import shutil
from datetime import datetime

# Define the headers globally
RECEIPT_FIELDS = ['receipt_id', 'client_id', 'date', 'items']
GUEST_FIELDS = ['user_id', 'guest_name']

class DatabaseManager:
    def __init__(self, receipt_db='receipts.csv', guest_db='guests.csv'):
        self.receipt_db = receipt_db
        self.guest_db = guest_db

        # Ensure backups directory exists
        os.makedirs('backups', exist_ok=True)

    def init_databases(self):
        """Initialize the CSV files if they don't exist"""
        self._create_db_if_not_exists(self.receipt_db, RECEIPT_FIELDS)
        self._create_db_if_not_exists(self.guest_db, GUEST_FIELDS)

    def _create_db_if_not_exists(self, db_name, headers):
        """Create the CSV file if it doesn't exist"""
        if not os.path.exists(db_name):
            with open(db_name, 'w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=headers)
                writer.writeheader()

    def backup_db(self, db_name):
        """Create a backup before modifying the database"""
        backup_filename = f"backups/{db_name.split('.')[0]}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        shutil.copy2(db_name, backup_filename)

    def add_entry(self, db_name, fields):
        """Populate fields dynamically via console input and append to the database"""
        self.backup_db(db_name)

        entry = {}
        for field in fields:
            entry[field] = input(f"Enter {field.replace('_', ' ').title()}: ")

        with open(db_name, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writerow(entry)

    def find_by_field(self, db_name, field_name, value):
        """Find and return rows by field name dynamically"""
        with open(db_name, 'r') as file:
            reader = csv.DictReader(file)
            results = [row for row in reader if row.get(field_name) == value]
            
            if results:
                for result in results:
                    print(result)
                return results
            else:
                print(f"No results found for {field_name}: {value}")
                return None

    def get_database_as_dict(self, db_name):
        """Get the entire database as a list of dictionaries"""
        with open(db_name, 'r') as file:
            reader = csv.DictReader(file)
            return [row for row in reader]

# Example usage
db_manager = DatabaseManager()

# Initialize databases (this will create files if they don't exist)
db_manager.init_databases()

# Add a new receipt entry dynamically
db_manager.add_entry(db_manager.receipt_db, RECEIPT_FIELDS)

# Add a new guest entry dynamically
db_manager.add_entry(db_manager.guest_db, GUEST_FIELDS)

# Find a receipt by 'client_id'
db_manager.find_by_field(db_manager.receipt_db, 'client_id', '12345')

# Get the guest database as a list of dictionaries
guests = db_manager.get_database_as_dict(db_manager.guest_db)
print(guests)
