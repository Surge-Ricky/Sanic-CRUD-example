from sanic import Blueprint
from sanic.response import json, redirect
from sqlalchemy import insert, select, delete
from sqlalchemy.orm import joinedload
from database import async_session
from models import User, Post, Comment
from app import jinja
from markdown import markdown
import re
bp_user_posts = Blueprint('user_posts')

@bp_user_posts.route('/<username>/posts/add', methods=['GET', 'POST'])
async def add_post(request, username):
  if request.method == 'POST':
    # Get user
    async with async_session() as session:
      async with session.begin():
        result = await session.execute(
          select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        if not user:
          return json({"error": "User not found"}, status=404)  
    # Create post
    data = request.form
    title = data.get('title') 
    content = data.get('content')
    
    post = Post(title=title, content=content, user_id=user.id)
    session.add(post)
    await session.commit()
    return redirect(f'/{username}/posts')
  else:  
    # No need to query user on GET
    return jinja.render('add-post.html', request, username=username)

@bp_user_posts.route('/<username>/posts', methods=['GET', 'POST']) 
async def get_user_posts(request, username):
    if request.method == 'POST':
        post_id = request.form.get('delete_post_id')
        if post_id:
            post_id = int(post_id)
            async with async_session() as session:
                async with session.begin():
                    result = await session.execute(select(Post).where(Post.id == post_id))
                    post = result.scalar_one_or_none()
                    if post is not None:
                        await session.delete(post)
    async with async_session() as session:
        async with session.begin():
            user_result = await session.execute(select(User).where(User.username == username))
            user = user_result.scalar_one_or_none()
            if user is not None:
                post_result = await session.execute(select(Post).where(Post.user_id == user.id))
                posts = post_result.scalars().all()
                # Markdown is not implemented on every page yet lol.
                # This replaces outer <p> tags because markdown adds it in. 
                posts = [{'title': re.sub(r'<p>|</p>', '', markdown(post.title)), 'content': re.sub(r'<p>|</p>', '', markdown(post.content)), 'id': post.id} for post in posts]
            else:
                return json({"error": "User not found"}, status=404)
    return jinja.render('user-posts.html', request, username=username, posts=posts)


@bp_user_posts.route('/<username>/posts/<post_id>/edit', methods=['GET', 'POST']) 
async def edit_post(request, username, post_id):
    post_id = int(post_id)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(Post).where(Post.id == post_id))
            post = result.scalar_one_or_none()
            if post is None:
                return json({"error": "Post not found"}, status=404)

            if request.method == 'POST':
                post.title = request.form.get('title')
                post.content = request.form.get('content')
                await session.commit()
                return redirect(f'/{username}/posts')
            else:
                return jinja.render('edit-post.html', request, post=post)
