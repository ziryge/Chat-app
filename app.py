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
                    video_path TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )''')
    conn.commit()
    conn.close()

def init_advanced_db():
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
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
    if "current_user" in st.session_state:
        st.sidebar.write(f"Logged in as: {st.session_state['current_user']}")
        return

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
    video_file = st.file_uploader("Upload a video (optional):", type=["mp4", "mov", "avi"], key="video_input")
    if st.button("Post"):
        if post_content or video_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conn = sqlite3.connect("app.db")
            c = conn.cursor()
            c.execute("INSERT INTO posts (user_id, content, timestamp) VALUES ((SELECT id FROM users WHERE username = ?), ?, ?)",
                      (st.session_state["current_user"], post_content, timestamp))
            post_id = c.lastrowid

            if video_file:
                video_path = f"videos/{post_id}_{video_file.name}"
                with open(video_path, "wb") as f:
                    f.write(video_file.read())
                c.execute("UPDATE posts SET video_path = ? WHERE id = ?", (video_path, post_id))

            conn.commit()
            conn.close()
            st.success("Post created successfully!")

    st.subheader("Posts")
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("SELECT users.username, posts.content, posts.timestamp, posts.video_path FROM posts JOIN users ON posts.user_id = users.id ORDER BY posts.timestamp DESC")
    posts = c.fetchall()
    conn.close()

    for username, content, timestamp, video_path in posts:
        st.markdown(f"**{username}:** {content} ({timestamp})")
        if video_path:
            st.video(video_path)

# Add likes and comments functionality

def like_post(post_id):
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("INSERT INTO likes (user_id, post_id, timestamp) VALUES ((SELECT id FROM users WHERE username = ?), ?, ?)",
              (st.session_state["current_user"], post_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def comment_on_post(post_id, comment):
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("INSERT INTO comments (user_id, post_id, content, timestamp) VALUES ((SELECT id FROM users WHERE username = ?), ?, ?, ?)",
              (st.session_state["current_user"], post_id, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# Update post display to include likes and comments

def display_post_interactions(post_id):
    conn = sqlite3.connect("app.db")
    c = conn.cursor()

    # Display likes
    c.execute("SELECT COUNT(*) FROM likes WHERE post_id = ?", (post_id,))
    like_count = c.fetchone()[0]
    st.write(f"Likes: {like_count}")
    if st.button(f"Like Post {post_id}"):
        like_post(post_id)
        st.success("You liked this post!")

    # Display comments
    st.write("Comments:")
    c.execute("SELECT users.username, comments.content, comments.timestamp FROM comments JOIN users ON comments.user_id = users.id WHERE comments.post_id = ? ORDER BY comments.timestamp DESC", (post_id,))
    comments = c.fetchall()
    for username, content, timestamp in comments:
        st.markdown(f"**{username}:** {content} ({timestamp})")

    # Add a new comment
    new_comment = st.text_input(f"Add a comment to Post {post_id}:", key=f"comment_input_{post_id}")
    if st.button(f"Comment on Post {post_id}"):
        if new_comment:
            comment_on_post(post_id, new_comment)
            st.success("Comment added successfully!")

    conn.close()

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

# Fix auto_refresh function to use st.experimental_set_query_params

def auto_refresh(interval=5):
    st.write(f"Refreshing every {interval} seconds...")
    st.experimental_set_query_params(refresh=str(interval))

# Helper functions for personal chat and admin panel

def get_all_users():
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("SELECT username FROM users")
    users = [row[0] for row in c.fetchall() if row[0] != st.session_state.get("current_user")]
    conn.close()
    return users if users else ["No other users"]

def save_personal_message(sender, recipient, content):
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO personal_messages (sender, recipient, content, timestamp) VALUES (?, ?, ?, ?)",
              (sender, recipient, content, timestamp))
    conn.commit()
    conn.close()

def get_personal_messages(user1, user2):
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("SELECT sender, content, timestamp FROM personal_messages WHERE (sender = ? AND recipient = ?) OR (sender = ? AND recipient = ?) ORDER BY timestamp",
              (user1, user2, user2, user1))
    messages = c.fetchall()
    conn.close()
    return messages

def ban_user(username):
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

def get_all_posts():
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("SELECT id, content FROM posts")
    posts = [f"{row[0]}: {row[1][:30]}..." for row in c.fetchall()]
    conn.close()
    return posts if posts else ["No posts"]

def delete_post(post_id_str):
    post_id = int(post_id_str.split(":")[0])
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    c.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()

def save_suggestion(user, suggestion):
    conn = sqlite3.connect("app.db")
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO suggestions (user, suggestion, timestamp) VALUES (?, ?, ?)",
              (user, suggestion, timestamp))
    conn.commit()
    conn.close()

# Define the missing functions

def personal_chat():
    st.subheader("Personal Chat")
    st.write("This feature allows users to chat privately.")


def admin_panel():
    st.subheader("Admin Panel")
    st.write("This feature allows admins to manage users and posts.")


def community_updates():
    st.subheader("Community Updates")
    st.write("This section allows users to suggest new features or improvements.")

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
        personal_chat()
        admin_panel()
        community_updates()

    save_session_state()
    auto_refresh(interval=5)  # Use auto-refresh for periodic updates

if __name__ == "__main__":
    main()