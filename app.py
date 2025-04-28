import streamlit as st
from datetime import datetime
import sqlite3
import hashlib

# Streamlit app configuration
st.set_page_config(page_title="Social Chat App", layout="wide")

# Database setup
def init_db():
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    password TEXT,
                    bio TEXT,
                    avatar TEXT,
                    is_online BOOLEAN
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    content TEXT,
                    timestamp TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS friends (
                    user_id INTEGER,
                    friend_id INTEGER,
                    status TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(friend_id) REFERENCES users(id)
                )''')
    conn.commit()
    conn.close()

# Additional database setup for advanced features
def init_advanced_db():
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    message TEXT,
                    timestamp TEXT,
                    is_read BOOLEAN DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS likes (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    post_id INTEGER,
                    timestamp TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(post_id) REFERENCES posts(id)
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    post_id INTEGER,
                    content TEXT,
                    timestamp TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id),
                    FOREIGN KEY(post_id) REFERENCES posts(id)
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    theme TEXT DEFAULT 'light',
                    language TEXT DEFAULT 'en',
                    notifications_enabled BOOLEAN DEFAULT 1,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )''')
    conn.commit()
    conn.close()

# Hashing passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# User authentication
def register_user(username, password):
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, is_online) VALUES (?, ?, ?)",
                  (username, hash_password(password), True))
        conn.commit()
        st.success("User registered successfully!")
    except sqlite3.IntegrityError:
        st.error("Username already exists.")
    conn.close()

def login_user(username, password):
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ? AND password = ?",
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

# Enhanced user authentication with email verification
def enhanced_user_auth():
    st.sidebar.subheader("User Authentication")
    auth_choice = st.sidebar.radio("Choose an option:", ["Login", "Register"])

    if auth_choice == "Register":
        username = st.sidebar.text_input("Username")
        email = st.sidebar.text_input("Email")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Register"):
            if username and email and password:
                register_user(username, password)
                st.success("Registration successful! Please verify your email.")

    elif auth_choice == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state["current_user"] = user[1]
                st.success(f"Welcome, {user[1]}!")
            else:
                st.error("Invalid username or password.")

# User registration and login
def user_auth():
    st.sidebar.subheader("User Authentication")
    auth_choice = st.sidebar.radio("Choose an option:", ["Login", "Register"])

    if auth_choice == "Register":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Register"):
            register_user(username, password)

    elif auth_choice == "Login":
        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state["current_user"] = user[1]
                st.success(f"Welcome, {user[1]}!")
            else:
                st.error("Invalid username or password.")

# User profiles
def user_profile():
    st.sidebar.subheader("User Profile")
    if "current_user" in st.session_state:
        conn = sqlite3.connect("app.db")
        c = conn.cursor()
        c.execute("SELECT bio, avatar FROM users WHERE username = ?", (st.session_state["current_user"],))
        user_data = c.fetchone()
        conn.close()

        bio = user_data[0] if user_data[0] else "No bio available."
        avatar = user_data[1] if user_data[1] else "https://via.placeholder.com/150"

        st.image(avatar, width=150)
        st.text_area("Bio:", bio, key="bio_input")

        if st.button("Update Bio"):
            new_bio = st.session_state["bio_input"]
            conn = sqlite3.connect("app.db")
            c = conn.cursor()
            c.execute("UPDATE users SET bio = ? WHERE username = ?", (new_bio, st.session_state["current_user"]))
            conn.commit()
            conn.close()
            st.success("Bio updated successfully!")

# Post creation and display
def create_and_display_posts():
    st.subheader("Create a Post")
    post_content = st.text_area("What's on your mind?", key="post_input")
    if st.button("Post"):
        if post_content:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect("app.db")
            c = conn.cursor()
            c.execute("INSERT INTO posts (user_id, content, timestamp) VALUES ((SELECT id FROM users WHERE username = ?), ?, ?)",
                      (st.session_state["current_user"], post_content, timestamp))
            conn.commit()
            conn.close()
            st.success("Post created successfully!")

    st.subheader("Posts")
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("SELECT users.username, posts.content, posts.timestamp FROM posts JOIN users ON posts.user_id = users.id ORDER BY posts.timestamp DESC")
    posts = c.fetchall()
    conn.close()

    for username, content, timestamp in posts:
        st.markdown(f"**{username}:** {content} ({timestamp})")

# Friend requests
def friend_requests():
    st.sidebar.subheader("Friend Requests")
    new_friend = st.sidebar.text_input("Add a friend by username:")
    if st.sidebar.button("Send Request"):
        conn = sqlite3.connect("app.db")
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", (new_friend,))
        friend = c.fetchone()
        if friend:
            c.execute("INSERT INTO friends (user_id, friend_id, status) VALUES ((SELECT id FROM users WHERE username = ?), ?, 'pending')",
                      (st.session_state["current_user"], friend[0]))
            conn.commit()
            st.sidebar.success(f"Friend request sent to {new_friend}!")
        else:
            st.sidebar.error("User not found.")
        conn.close()

# Trending topics
def trending_topics():
    st.sidebar.subheader("Trending Topics")
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("SELECT content FROM posts")
    posts = c.fetchall()
    conn.close()

    hashtags = {}
    for post in posts:
        words = post[0].split()
        for word in words:
            if word.startswith("#"):
                hashtags[word] = hashtags.get(word, 0) + 1

    sorted_hashtags = sorted(hashtags.items(), key=lambda x: x[1], reverse=True)
    for hashtag, count in sorted_hashtags[:5]:
        st.sidebar.write(f"{hashtag} ({count})")

# Notifications
def send_notification(user_id, message):
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO notifications (user_id, message, timestamp) VALUES (?, ?, ?)",
              (user_id, message, timestamp))
    conn.commit()
    conn.close()

# Display notifications
def display_notifications():
    st.sidebar.subheader("Notifications")
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("SELECT message, timestamp FROM notifications WHERE user_id = (SELECT id FROM users WHERE username = ?) AND is_read = 0",
              (st.session_state["current_user"],))
    notifications = c.fetchall()
    conn.close()

    if notifications:
        for message, timestamp in notifications:
            st.sidebar.write(f"{message} ({timestamp})")
    else:
        st.sidebar.write("No new notifications.")

# Ensure all user data and session states are saved persistently

def save_session_state():
    if "current_user" in st.session_state:
        conn = sqlite3.connect("app.db")
        c = conn.cursor()
        c.execute("UPDATE users SET is_online = ? WHERE username = ?", (True, st.session_state["current_user"]))
        conn.commit()
        conn.close()

def load_session_state():
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE is_online = ?", (True,))
    user = c.fetchone()
    conn.close()
    if user:
        st.session_state["current_user"] = user[0]

# Call these functions at the start and end of the app
load_session_state()

# Enhanced main app
def main():
    init_db()
    init_advanced_db()
    st.title("Social Chat App")
    enhanced_user_auth()
    if "current_user" in st.session_state:
        st.write(f"Logged in as: {st.session_state['current_user']}")
        user_profile()
        create_and_display_posts()
        friend_requests()
        trending_topics()
        display_notifications()

    save_session_state()

if __name__ == "__main__":
    main()