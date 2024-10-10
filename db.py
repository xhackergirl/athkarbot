import sqlite3

# Database setup
def setup_database():
    conn = sqlite3.connect('channels_groups.db')  # Ensure consistent database name
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY, 
            user_id INTEGER NOT NULL,
            channel_id TEXT NOT NULL,
            channel_name TEXT,
            phrases TEXT,
            frequency INTEGER,
            last_message_id INTEGER,
            last_content TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP  -- Add this column to store when channel was added
        )
    ''')
    conn.commit()
    conn.close()

# Database functions
def save_channel_data(user_id, channel_id, channel_name, phrases, frequency, last_message_id, last_content):
    conn = sqlite3.connect('channels_groups.db')  # Ensure consistent database name
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO channels (user_id, channel_id, channel_name, phrases, frequency, last_message_id, last_content)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, channel_id, channel_name, phrases, frequency, last_message_id, last_content))
    conn.commit()
    conn.close()

def get_channel_data(user_id):
    conn = sqlite3.connect('channels_groups.db')  # Ensure consistent database name
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM channels WHERE user_id = ?', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows
    
def fetch_last_channel_group(user_id):
    # Ensure consistent database name
    connection = sqlite3.connect('channels_groups.db')
    cursor = connection.cursor()
    
    cursor.execute("""
        SELECT channel_id, channel_name FROM channels 
        WHERE user_id = ? 
        ORDER BY added_at DESC LIMIT 1
    """, (user_id,))
    
    result = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if result:
        return {'channel_group_id': result[0]}
    return None

def fetch_channel_phrases(user_id, channel_id):
    conn = sqlite3.connect('channels_groups.db')
    cursor = conn.cursor()
    cursor.execute('SELECT phrases FROM channels WHERE user_id = ? AND channel_id = ?', (user_id, channel_id))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0].split(',')  # Assuming phrases are stored as a comma-separated string
    return []  # Return an empty list if no phrases found

def fetch_channel_data_phrases(user_id, channel_group_id):
    conn = sqlite3.connect('channels_groups.db')
    cursor = conn.cursor()
    cursor.execute('SELECT phrases FROM channels WHERE user_id = ? AND channel_id = ?', (user_id, channel_group_id))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {'phrases':result[0]}
    return None

def fetch_channel_data_frequency(user_id, channel_group_id):
    conn = sqlite3.connect('channels_groups.db')
    cursor = conn.cursor()
    cursor.execute('SELECT frequency FROM channels WHERE user_id = ? AND channel_id = ?', (user_id, channel_group_id))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {'frequency': result[0]}
    return None

def fetch_channel_data_message_id(user_id, channel_group_id):
    conn = sqlite3.connect('channels_groups.db')
    cursor = conn.cursor()
    cursor.execute('SELECT last_message_id FROM channels WHERE user_id = ? AND channel_id = ?', (user_id, channel_group_id))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {'last_message_id':result[0]}
    return None

def delete_channel_data(user_id, channel_group_id):
    conn = sqlite3.connect('channels_groups.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM channels WHERE user_id = ? AND channel_id = ?", (user_id, channel_group_id))
    conn.commit()
    conn.close()

def fetch_channel_group_id(user_id):
    conn = sqlite3.connect('channels_groups.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT channel_id FROM channels 
        WHERE user_id = ? 
        ORDER BY id DESC LIMIT 1
    """, (user_id,))
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        return result[0]  # Return the channel ID
    return None

def fetch_channel_group_name(user_id):
    conn = sqlite3.connect('channels_groups.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT channel_name FROM channels 
        WHERE channel_id = ? 
        ORDER BY id DESC LIMIT 1
    """, (user_id,))
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        return result[0]  # Return the channel ID
    return None

def fetch_channel_data(user_id, channel_group_id):
    conn = sqlite3.connect('channels_groups.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT phrases, frequency 
        FROM channels 
        WHERE user_id = ? AND channel_id = ? 
        ORDER BY id DESC LIMIT 1
    """, (user_id, channel_group_id))
    
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        return {
            'phrases': result[0] if result[0] is not None else '',
            'frequency': result[1] if result[1] is not None else 0
        }
    return {'phrases': '', 'frequency': 0}  # Default return if no result

def fetch_all_channels():
    # Connect to the database
    conn = sqlite3.connect('channels_groups.db')
    cursor = conn.cursor()

    # Execute a query to select all channels
    cursor.execute("SELECT user_id, channel_id, phrases, frequency FROM channels")

    # Fetch all rows
    rows = cursor.fetchall()
    conn.close()

    # Convert the fetched rows into a list of dictionaries for easy access
    channels = []
    for row in rows:
        channels.append({
            'user_id': row[0],
            'channel_id': row[1],
            'phrases': row[2] if row[2] else '',
            'frequency': row[3]
        })
    return channels
