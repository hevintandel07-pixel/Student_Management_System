import sqlite3

DATABASE = "student_management.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def add_column_if_missing(connection, table, column, definition):
    columns = connection.execute(
        f"PRAGMA table_info({table})"
    ).fetchall()

    existing_columns = [column_info["name"] for column_info in columns]

    if column not in existing_columns:
        connection.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


def create_tables():

    connection = get_db_connection()

    # Student table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            branch TEXT,
            semester INTEGER,
            email TEXT,
            mobile TEXT,
            attendance REAL DEFAULT 0
        )
    """)

    # Add P4 related fields if they do not exist
    add_column_if_missing(
        connection,
        "students",
        "club",
        "TEXT DEFAULT 'None'"
    )

    add_column_if_missing(
        connection,
        "students",
        "permissions",
        "INTEGER DEFAULT 0"
    )

    # Marks table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            subject1 REAL DEFAULT 0,
            subject2 REAL DEFAULT 0,
            subject3 REAL DEFAULT 0,
            subject4 REAL DEFAULT 0,
            subject5 REAL DEFAULT 0,
            total REAL DEFAULT 0,
            percentage REAL DEFAULT 0,
            grade TEXT,
            result TEXT,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)

    # Attendance table
    connection.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            total_days INTEGER NOT NULL,
            present_days INTEGER NOT NULL,
            attendance_percentage REAL DEFAULT 0,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    """)

    connection.commit()
    connection.close()