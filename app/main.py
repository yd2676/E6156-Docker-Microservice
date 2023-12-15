from typing import List, Optional, Dict
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
import uvicorn
import json
import uuid
import boto3
import os
import os.path


app = FastAPI()

# In-memory structure to store posts
class Comment(BaseModel):
    commenter: str
    commenter_title: str
    content: str
    likes: int

class Post(BaseModel):
    author: str
    author_title: str
    company: str
    content: str
    likes: int
    comments: Dict[str, Comment] = {}


def load_json_data_to_model(file_path: str) -> Dict[int, Post]:
    with open(file_path, 'r') as file:
        posts_list = json.load(file)

        posts_dict = {}
        for post_data in posts_list:
            comments = {comment['comment_id']:
                            Comment(commenter=comment['commenter'],
                                    commenter_title=comment['commenter_title'],
                                    content=comment['content'],
                                    likes=comment['likes'])
                        for comment in post_data['comments']}

            post = Post(author=post_data['author'],
                        author_title=post_data['author_title'],
                        company=post_data['company'],
                        content=post_data['content'],
                        likes=post_data['likes'],
                        comments=comments)
            posts_dict[post_data['post_id']] = post

    return posts_dict


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

dPath = os.path.join(os.getcwd(), "sample_data.json")
posts = load_json_data_to_model(dPath)

topic_arn = "arn:aws:sns:us-east-2:538930638837:Send_email"
#topic_arn = "arn:aws:sns:us-east-2:538930638837:send_example"

@app.get("/posts", response_model=List[Post])
async def get_all_posts():
    return list(posts.values())

@app.get("/posts/{post_id}", response_model=Post)
async def get_post(post_id: int):
    if post_id not in posts:
        raise HTTPException(status_code=404, detail="Post not found")
    return posts[post_id]

@app.post("/posts", response_model=Post)
async def create_post(post: Post):
    new_id = max(posts) + 1
    posts[new_id] = post
    subject_text = f'A New Post(Post_id: {new_id}) was Posted'
    message_text = str(post)
    send_message_to_sns_topic(topic_arn, message_text, subject_text)
    return posts[new_id]


@app.post("/posts/{post_id}/comments", response_model=Comment)
async def create_comment(post_id: int, comment: Comment):
    if post_id not in posts:
        raise HTTPException(status_code=404, detail="Post not found")

    comment_id = str(uuid.uuid4())

    posts[post_id].comments[comment_id] = comment

    subject_text = f'A New Comment(Comment_id: {comment_id}) was Made to Post(Post_id: {post_id})'
    message_text = str(comment)
    send_message_to_sns_topic(topic_arn, message_text, subject_text)
    return posts[post_id].comments[comment_id]

@app.put("/posts/{post_id}", response_model=Post)
async def update_post(post_id: int, updated_post: Post):
    if post_id not in posts:
        raise HTTPException(status_code=404, detail="Post not found")

    posts[post_id] = updated_post

    subject_text = f'Post(Post_id: {post_id}) was Updated'
    message_text = str(updated_post)
    send_message_to_sns_topic(topic_arn, message_text, subject_text)
    return posts[post_id]

@app.delete("/posts/{post_id}")
async def delete_post(post_id: int):
    if post_id not in posts:
        raise HTTPException(status_code=404, detail="Post not found")
    del posts[post_id]

    subject_text = f'Post(Post_id: {post_id}) was Deleted'
    message_text = f'Post(Post_id: {post_id}) was Deleted'
    send_message_to_sns_topic(topic_arn, message_text, subject_text)
    return {"detail": "Post successfully deleted"}


@app.delete("/posts/{post_id}/comments/{comment_id}", response_model=dict)
async def delete_comment(post_id: int, comment_id: str):
    # Check if the post exists
    if post_id not in posts:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check if the comment exists
    if comment_id not in posts[post_id].comments:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Delete the comment from the post
    del posts[post_id].comments[comment_id]

    subject_text = f'Comment(Comment_id: {comment_id}) to Post(Post_id: {post_id}) was Deleted'
    message_text = f'Comment(Comment_id: {comment_id}) to Post(Post_id: {post_id}) was Deleted'
    send_message_to_sns_topic(topic_arn, message_text, subject_text)
    return {"detail": "Comment deleted successfully"}
"""
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8012)
"""