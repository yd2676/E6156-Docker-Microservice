from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import uvicorn
import json
import boto3
import os
import os.path
import pymysql

app = FastAPI()

class MySQLDataService:

    def __init__(self):
        self.conn = None

    def _get_connection(self):
        self.conn = pymysql.connect(
            user='admin',
            password='123456789',
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
            host='database1.cqjmsosmil2o.us-east-2.rds.amazonaws.com',
            port=3306
        )
        print("Connected!, conn=", self.conn.host)
        return self.conn

    def get_all_posts(self):

        conn = None

        try:

            sql = """
                    SELECT p.*, c.*
                    FROM forums.posts p
                    LEFT JOIN forums.comments c ON p.post_id = c.post_id
                    ORDER BY p.post_id, c.comment_id
                    """
            conn = self._get_connection()
            cur = conn.cursor()
            full_sql = cur.mogrify(sql)
            print("Full SQL = ", full_sql)
            # res = cur.execute(sql)
            cur.execute(sql)
            result = cur.fetchall()

            conn.close()
        except Exception as e:
            print("Exception = ", e)
            if conn:
                conn.close()
            result = None

        return result

    def get_single_post(self, post_id):

        conn = None
        try:
            # SQL query to fetch a single post and its comments
            sql = """
                SELECT p.*, c.*
                FROM forums.posts p
                LEFT JOIN forums.comments c ON p.post_id = c.post_id
                WHERE p.post_id = %s
                ORDER BY c.comment_id
                """
            conn = self._get_connection()
            cur = conn.cursor()
            full_sql = cur.mogrify(sql, (post_id,))
            print("Full SQL = ", full_sql)
            cur.execute(sql, (post_id,))
            result = cur.fetchall()
            conn.close()
        except Exception as e:
            print("Exception = ", e)
            if conn:
                conn.close()
            result = None

        return result

    def create_post(self, author, author_id, content):
        conn = None
        try:
            # SQL query to insert a new post
            sql = """
                INSERT INTO forums.posts (author, author_id, content)
                VALUES (%s, %s, %s)
                """
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(sql, (author, author_id, content))
            post_id = cur.lastrowid

            select_sql = "SELECT * FROM forums.posts WHERE post_id = %s"
            cur.execute(select_sql, (post_id,))
            new_post_info = cur.fetchall()

            conn.commit()
            conn.close()
            return post_id, new_post_info
        except Exception as e:
            print("Exception = ", e)
            if conn:
                conn.rollback()
                conn.close()
            return None

    def create_comment(self, post_id, commenter, commenter_id, content):
        conn = None
        try:
            # SQL query to insert a new comment
            sql = """
                INSERT INTO forums.comments (post_id, commenter, commenter_id, content)
                VALUES (%s, %s, %s, %s)
                """
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(sql, (post_id, commenter, commenter_id, content))
            comment_id = cur.lastrowid

            select_sql = "SELECT * FROM forums.comments WHERE comment_id = %s"
            cur.execute(select_sql, (comment_id,))
            new_comment_info = cur.fetchall()

            conn.commit()
            conn.close()
            return comment_id, new_comment_info
        except Exception as e:
            print("Exception = ", e)
            if conn:
                conn.rollback()
                conn.close()
            return None

    def update_post(self, post_id, updated_author=None, updated_author_id=None, updated_content=None):
        conn = None
        try:
            update_sql = """
                UPDATE forums.posts
                SET author = %s, author_id = %s, content = %s
                WHERE post_id = %s
                """
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(update_sql, (
            updated_author, updated_author_id, updated_content, post_id))

            if cur.rowcount == 0:
                raise Exception("Post not found or no change in data")

            select_sql = """
                SELECT p.*, c.*
                FROM forums.posts p
                LEFT JOIN forums.comments c ON p.post_id = c.post_id
                WHERE p.post_id = %s
                """
            cur.execute(select_sql, (post_id,))
            result = cur.fetchall()

            conn.commit()
            conn.close()
            return result
        except Exception as e:
            print("Exception = ", e)
            if conn:
                conn.rollback()
                conn.close()
            return None

    def delete_comment(self, post_id, comment_id):
        conn = None
        try:
            sql = "DELETE FROM forums.comments WHERE post_id = %s and comment_id = %s"
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(sql, (post_id, comment_id))

            # Check if the comment was actually deleted
            if cur.rowcount == 0:
                raise Exception("Comment not found or already deleted")

            conn.commit()
            conn.close()
            return "Comment deleted successfully"
        except Exception as e:
            print("Exception = ", e)
            if conn:
                conn.rollback()
                conn.close()
            return None

    def delete_post(self, post_id):
        conn = None
        try:
            delete_comments_sql = "DELETE FROM forums.comments WHERE post_id = %s"

            delete_post_sql = "DELETE FROM forums.posts WHERE post_id = %s"

            conn = self._get_connection()
            cur = conn.cursor()

            cur.execute(delete_comments_sql, (post_id,))

            cur.execute(delete_post_sql, (post_id,))

            if cur.rowcount == 0:
                raise Exception("Post not found or already deleted")

            conn.commit()
            conn.close()
            return "Post deleted successfully"
        except Exception as e:
            print("Exception = ", e)
            if conn:
                conn.rollback()
                conn.close()
            return None

# In-memory structure to store posts
class Comment(BaseModel):
    commenter: str
    commenter_id: int
    content: str

class Post(BaseModel):
    author: str
    author_id: int
    content: str


def send_message_to_sns_topic(topic_arn, message, subject=None):

    # Initialize an SNS client
    sns_client = boto3.client('sns')

    try:
        # Send a message to the specified topic
        response = sns_client.publish(
            TopicArn=topic_arn,
            Message=message,
            Subject=subject
        )

        # Print the response
        print("Message sent. MessageId:", response['MessageId'])
        print('Subject: ', subject)
        print('Message:', message)

        return response

    except Exception as e:
        print(f"An error occured: {e}")
        return None

my_sql_data_service = MySQLDataService()

#topic_arn = "arn:aws:sns:us-east-2:538930638837:Send_email"
topic_arn = "arn:aws:sns:us-east-2:538930638837:send_example"

@app.get("/")
async def read_main():
    return {"Docker Microservice: Version 1.0"}

@app.get("/posts")
async def get_all_posts():
    result = my_sql_data_service.get_all_posts()
    formatted_data = {}

    for item in result:
        post_id = item['post_id']
        if post_id not in formatted_data:
            formatted_data[post_id] = {
                "post_id": post_id,
                "author": item["author"],
                "author_id": item["author_id"],
                "content": item["content"],
                "comments": []
            }
        formatted_data[post_id]["comments"].append({
            "comment_id": item["comment_id"],
            "post_id": item["c.post_id"],
            "commenter": item["commenter"],
            "commenter_id": item["commenter_id"],
            "content": item["c.content"]
        })
    return jsonable_encoder(formatted_data)

@app.get("/posts/{post_id}")
async def get_post(post_id: int):
    result = my_sql_data_service.get_single_post(post_id)
    formatted_data = {}

    for item in result:
        post_id = item['post_id']
        if post_id not in formatted_data:
            formatted_data[post_id] = {
                "post_id": post_id,
                "author": item["author"],
                "author_id": item["author_id"],
                "content": item["content"],
                "comments": []
            }
        formatted_data[post_id]["comments"].append({
            "comment_id": item["comment_id"],
            "post_id": item["c.post_id"],
            "commenter": item["commenter"],
            "commenter_id": item["commenter_id"],
            "content": item["c.content"]
        })
    return jsonable_encoder(formatted_data)

@app.post("/posts", response_model=Post)
async def create_post(post: Post):
    post_id, result = my_sql_data_service.create_post(post.author, post.author_id, post.content)
    subject_text = f'A New Post(Post_id: {post_id}) was Posted'
    message_text = str(result[0])
    send_message_to_sns_topic(topic_arn, message_text, subject_text)
    return jsonable_encoder(result[0])


@app.post("/posts/{post_id}/comments", response_model=Comment)
async def create_comment(post_id: int, comment: Comment):
    comment_id, result = my_sql_data_service.create_comment(post_id, comment.commenter, comment.commenter_id, comment.content)

    subject_text = f'A New Comment(Comment_id: {comment_id}) was Made to Post(Post_id: {post_id})'
    message_text = str(result[0])
    send_message_to_sns_topic(topic_arn, message_text, subject_text)
    return jsonable_encoder(result[0])


@app.put("/posts/{post_id}")
async def update_post(post_id: int, updated_post: Post):
    result = my_sql_data_service.update_post(post_id, updated_post.author, updated_post.author_id, updated_post.content)

    subject_text = f'Post(Post_id: {post_id}) was Updated'
    message_text = str(updated_post)
    send_message_to_sns_topic(topic_arn, message_text, subject_text)
    print(result)
    formatted_data = {}

    for item in result:
        post_id = item['post_id']
        if post_id not in formatted_data:
            formatted_data[post_id] = {
                "post_id": post_id,
                "author": item["author"],
                "author_id": item["author_id"],
                "content": item["content"],
                "comments": []
            }
        formatted_data[post_id]["comments"].append({
            "comment_id": item["comment_id"],
            "post_id": item["c.post_id"],
            "commenter": item["commenter"],
            "commenter_id": item["commenter_id"],
            "content": item["c.content"]
        })
    return jsonable_encoder(formatted_data)

@app.delete("/posts/{post_id}")
async def delete_post(post_id: int):
    result = my_sql_data_service.delete_post(post_id)

    subject_text = f'Post(Post_id: {post_id}) was Deleted'
    message_text = f'Post(Post_id: {post_id}) was Deleted'
    send_message_to_sns_topic(topic_arn, message_text, subject_text)
    return result


@app.delete("/posts/{post_id}/comments/{comment_id}")
async def delete_comment(post_id: int, comment_id: str):
    result = my_sql_data_service.delete_comment(post_id, comment_id)

    subject_text = f'Comment(Comment_id: {comment_id}) to Post(Post_id: {post_id}) was Deleted'
    message_text = f'Comment(Comment_id: {comment_id}) to Post(Post_id: {post_id}) was Deleted'
    send_message_to_sns_topic(topic_arn, message_text, subject_text)
    return result
'''
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8012)
'''
