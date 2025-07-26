# database_module.py

import sqlite3
import numpy as np
import datetime
import os
from config import DATABASE_PATH # Import the database path from config.py

class DatabaseManager:
    """
    Manages all interactions with the SQLite database for the Smart Attendance System.
    This includes creating tables, adding/retrieving users, and logging attendance.
    """

    def __init__(self, db_path=DATABASE_PATH):
        """
        Initializes the DatabaseManager with the path to the SQLite database.
        Ensures the database file exists and creates tables if they don't.
        """
        self.db_path = db_path
        self._create_tables() # Call internal method to ensure tables are created on initialization

    def _get_connection(self):
        """
        EstablishesEstablishes and returns a connection to the SQLite database.
        Includes a row_factory to access columns by name.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row # Allows accessing columns by name
        return conn

    def _create_tables(self):
        """
        Creates the 'users' and 'attendance' tables in the database if they do not already exist.
        The 'users' table stores user details and their facial encodings.
        The 'attendance' table records attendance events.
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Create users table
            # user_id: Primary Key for users
            # name: Name of the user
            # face_encoding: Stores the 128-D face embedding as a BLOB (binary data)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    face_encoding BLOB NOT NULL
                )
            ''')

            # Create attendance table
            # id: Primary Key for attendance records
            # user_id: Foreign Key referencing the users table
            # timestamp: Date and time of attendance
            # status: Attendance status (e.g., 'Present', 'Absent' - though system only logs 'Present')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            conn.commit()
            print("Database tables 'users' and 'attendance' ensured to exist.")
        except sqlite3.Error as e:
            print(f"Database error during table creation: {e}")
        finally:
            if conn:
                conn.close()

    def add_user(self, user_id, name, face_encoding):
        """
        Adds a new user to the 'users' table.
        The face_encoding (NumPy array) is converted to bytes for BLOB storage.

        Args:
            user_id (str): Unique identifier for the user.
            name (str): Full name of the user.
            face_encoding (numpy.ndarray): 128-D face embedding array.

        Returns:
            bool: True if user was added successfully, False otherwise.
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if user_id already exists
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            if cursor.fetchone():
                print(f"User with ID '{user_id}' already exists. Please use a unique ID.")
                return False

            # Convert numpy array to bytes for BLOB storage
            face_encoding_bytes = face_encoding.tobytes()

            cursor.execute(
                "INSERT INTO users (user_id, name, face_encoding) VALUES (?, ?, ?)",
                (user_id, name, face_encoding_bytes)
            )
            conn.commit()
            print(f"User '{name}' (ID: {user_id}) added successfully.")
            return True
        except sqlite3.Error as e:
            print(f"Error adding user '{name}' (ID: {user_id}): {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_all_users(self):
        """
        Retrieves all registered users from the 'users' table.
        Converts the stored BLOB face_encoding back to a NumPy array.

        Returns:
            list: A list of dictionaries, where each dictionary represents a user
                  with keys 'user_id', 'name', and 'face_encoding'.
                  Returns an empty list if no users are found or on error.
        """
        conn = None
        users = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, name, face_encoding FROM users")
            rows = cursor.fetchall()
            for row in rows:
                user_id = row['user_id']
                name = row['name']
                # Convert BLOB back to numpy array
                face_encoding = np.frombuffer(row['face_encoding'], dtype=np.float64) # Assuming float64 for 128-D encoding
                users.append({
                    'user_id': user_id,
                    'name': name,
                    'face_encoding': face_encoding
                })
            return users
        except sqlite3.Error as e:
            print(f"Error retrieving users: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def log_attendance(self, user_id, status="Present"):
        """
        Logs an attendance record for a given user.
        The timestamp is automatically generated at the time of logging.

        Args:
            user_id (str): The ID of the user whose attendance is being logged.
            status (str): The attendance status (default is 'Present').

        Returns:
            bool: True if attendance was logged successfully, False otherwise.
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute(
                "INSERT INTO attendance (user_id, timestamp, status) VALUES (?, ?, ?)",
                (user_id, timestamp, status)
            )
            conn.commit()
            print(f"Attendance logged for user ID '{user_id}' at {timestamp}.")
            return True
        except sqlite3.Error as e:
            print(f"Error logging attendance for user ID '{user_id}': {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_attendance_records(self, start_date=None, end_date=None):
        """
        Retrieves attendance records within a specified date range.
        If no dates are provided, all records are returned.

        Args:
            start_date (str, optional): Start date in 'YYYY-MM-DD' format.
            end_date (str, optional): End date in 'YYYY-MM-DD' format.

        Returns:
            list: A list of dictionaries, where each dictionary represents an
                  attendance record with keys 'id', 'user_id', 'timestamp', 'status',
                  and 'name' (joined from users table).
                  Returns an empty list if no records are found or on error.
        """
        conn = None
        records = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            query = """
                SELECT
                    a.id,
                    a.user_id,
                    u.name,
                    a.timestamp,
                    a.status
                FROM attendance a
                JOIN users u ON a.user_id = u.user_id
            """
            params = []

            if start_date and end_date:
                query += " WHERE DATE(a.timestamp) BETWEEN ? AND ?"
                params.append(start_date)
                params.append(end_date)
            elif start_date:
                query += " WHERE DATE(a.timestamp) >= ?"
                params.append(start_date)
            elif end_date:
                query += " WHERE DATE(a.timestamp) <= ?"
                params.append(end_date)
            
            query += " ORDER BY a.timestamp DESC" # Order by most recent first

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            for row in rows:
                records.append(dict(row)) # Convert Row object to dictionary
            return records
        except sqlite3.Error as e:
            print(f"Error retrieving attendance records: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_user_by_id(self, user_id):
        """
        Retrieves a single user by their user_id.

        Args:
            user_id (str): The ID of the user to retrieve.

        Returns:
            dict or None: A dictionary representing the user if found, None otherwise.
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, name, face_encoding FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                face_encoding = np.frombuffer(row['face_encoding'], dtype=np.float64)
                return {
                    'user_id': row['user_id'],
                    'name': row['name'],
                    'face_encoding': face_encoding
                }
            return None
        except sqlite3.Error as e:
            print(f"Error retrieving user by ID '{user_id}': {e}")
            return None
        finally:
            if conn:
                conn.close()

    def delete_user(self, user_id):
        """
        Deletes a user and all their associated attendance records.

        Args:
            user_id (str): The ID of the user to delete.

        Returns:
            bool: True if user was deleted successfully, False otherwise.
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Delete attendance records first due to foreign key constraint
            cursor.execute("DELETE FROM attendance WHERE user_id = ?", (user_id,))
            conn.commit()
            print(f"Deleted attendance records for user ID '{user_id}'.")

            # Then delete the user
            cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()
            print(f"User '{user_id}' deleted successfully.")
            return True
        except sqlite3.Error as e:
            print(f"Error deleting user '{user_id}': {e}")
            return False
        finally:
            if conn:
                conn.close()

# Example usage (for testing purposes, can be removed in final integration)
if __name__ == "__main__":
    # Clean up previous db for a fresh start for testing
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        print(f"Removed existing database: {DATABASE_PATH}")

    db_manager = DatabaseManager()

    # 1. Add some dummy users
    print("\n--- Adding Users ---")
    dummy_encoding_john = np.random.rand(128).astype(np.float64) # 128-D float64 array
    dummy_encoding_jane = np.random.rand(128).astype(np.float64)
    dummy_encoding_doe = np.random.rand(128).astype(np.float64)

    db_manager.add_user("U001", "John Doe", dummy_encoding_john)
    db_manager.add_user("U002", "Jane Smith", dummy_encoding_jane)
    db_manager.add_user("U003", "Peter Jones", dummy_encoding_doe)
    db_manager.add_user("U001", "John Doe Duplicate", dummy_encoding_john) # Attempt to add duplicate ID

    # 2. Get all users
    print("\n--- All Registered Users ---")
    users = db_manager.get_all_users()
    for user in users:
        print(f"ID: {user['user_id']}, Name: {user['name']}, Encoding Shape: {user['face_encoding'].shape}")
    
    # 3. Get a specific user
    print("\n--- Get User by ID ---")
    user_u002 = db_manager.get_user_by_id("U002")
    if user_u002:
        print(f"Found user: {user_u002['name']} (ID: {user_u002['user_id']})")
    else:
        print("User U002 not found.")

    # 4. Log attendance
    print("\n--- Logging Attendance ---")
    db_manager.log_attendance("U001")
    db_manager.log_attendance("U002")
    # Simulate attendance on a different day for reporting
    conn = db_manager._get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO attendance (user_id, timestamp, status) VALUES (?, ?, ?)",
                   ("U001", "2025-07-20 09:00:00", "Present"))
    cursor.execute("INSERT INTO attendance (user_id, timestamp, status) VALUES (?, ?, ?)",
                   ("U003", "2025-07-20 09:05:00", "Present"))
    conn.commit()
    conn.close()
    db_manager.log_attendance("U001") # John attends again today

    # 5. Get attendance records
    print("\n--- All Attendance Records ---")
    all_attendance = db_manager.get_attendance_records()
    for record in all_attendance:
        print(f"ID: {record['id']}, User: {record['name']} ({record['user_id']}), Time: {record['timestamp']}, Status: {record['status']}")

    print("\n--- Attendance Records for 2025-07-20 ---")
    daily_attendance = db_manager.get_attendance_records(start_date="2025-07-20", end_date="2025-07-20")
    for record in daily_attendance:
        print(f"ID: {record['id']}, User: {record['name']} ({record['user_id']}), Time: {record['timestamp']}, Status: {record['status']}")

    print("\n--- Deleting a User ---")
    db_manager.delete_user("U003")
    
    print("\n--- All Registered Users After Deletion ---")
    users_after_delete = db_manager.get_all_users()
    for user in users_after_delete:
        print(f"ID: {user['user_id']}, Name: {user['name']}")
    
    print("\n--- Attendance Records After User Deletion (U003 should be gone) ---")
    all_attendance_after_delete = db_manager.get_attendance_records()
    for record in all_attendance_after_delete:
        print(f"ID: {record['id']}, User: {record['name']} ({record['user_id']}), Time: {record['timestamp']}, Status: {record['status']}")


