from sanic import Blueprint
from sanic.response import json, text, redirect
from sqlalchemy import insert, select, delete, func
from sqlalchemy.orm import joinedload
from database import async_session
from models import User, Post, Comment
from app import jinja
from markdown import markdown
import re
bp_user = Blueprint('user_routes')

@bp_user.route('/', methods=['GET'])
async def index(request):
    return redirect('/users')

@bp_user.route('/users', methods=['GET'])  
async def get_users(request):
    admin = request.args.get('admin', default='false')
    is_admin = admin.lower() == 'true'
    async with async_session() as session:
        async with session.begin():
            user_result = await session.execute(select(User))
            users = user_result.scalars().all()
            user_data = []
            for user in users:
                post_count_result = await session.execute(
                    select(func.count(Post.id)).where(Post.user_id == user.id)
                )
                post_count = post_count_result.scalar_one()
                comment_count_result = await session.execute(
                    select(func.count(Comment.id)).where(Comment.user_id == user.id)
                )
                comment_count = comment_count_result.scalar_one()
                user_data.append({
                    "username": user.username,
                    "post_count": post_count,
                    "comment_count": comment_count,
                })
    return jinja.render('users.html', request, users=user_data, is_admin=is_admin)


@bp_user.route('/users/add', methods=['GET', 'POST'])
async def add_user(request):
    if request.method == 'POST':
        data = request.form
        username = data.get('username')
        password = data.get('password')  # assuming you have a password field in your form
        if not username or not password:  # Check if the username or password is empty
            return json({"error": "Username and password cannot be empty"}, status=400)
        async with async_session() as session:
            async with session.begin():
                result = await session.execute(select(User).where(User.username == username))
                user = result.scalar_one_or_none()
        if user is not None:
            return text(f"User {username} already exists.", status=400)
        else:
            user = User(username=username, password=password)
            async with async_session() as session:
                async with session.begin():
                    session.add(user)
            return redirect('/users')  # redirect to users list after adding a user
    else:
        return jinja.render('add-user.html', request)

@bp_user.route('/<username>', methods=['GET'])
async def get_user(request, username):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(User)
                .options(joinedload(User.posts), joinedload(User.comments)) 
                .where(User.username == username)
            )
            user = result.unique().scalar_one_or_none()
            
            if user is None:
                return json({"error": "User not found"}, status=404)
                
    user_data = {
    'username': user.username,
    'posts': user.posts,
    'comments': user.comments
    }
    
    return jinja.render('user.html', request, user=user_data)


@bp_user.route('/<username>/delete', methods=['GET'])
async def delete_user(request, username):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(User).where(User.username == username))
            user = result.scalar_one_or_none()
    if user is not None:
        async with async_session() as session:
            async with session.begin():
                # Delete all posts and comments associated with the user
                await session.execute(delete(Post).where(Post.user_id == user.id))
                await session.execute(delete(Comment).where(Comment.user_id == user.id))
                # Delete the user
                await session.delete(user)
        return text(f"User {username} and all associated posts and comments deleted.")
    else:
        return json({"error": "User not found"}, status=404)


