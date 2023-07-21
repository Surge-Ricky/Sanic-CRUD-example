from sanic import Blueprint
from sanic.response import json, redirect
from sqlalchemy import insert, select, delete
from sqlalchemy.orm import joinedload
from database import async_session
from models import User, Post, Comment
from app import jinja
from markdown import markdown
import re


bp_user_comments = Blueprint('user_comments')

@bp_user_comments.route('/<username>/comments/add', methods=['GET', 'POST'])
async def add_comment(request, username):
  async with async_session() as session:
    async with session.begin():
      try:
        user_result = await session.execute(
          select(User).where(User.username == username)
        )
        user = user_result.scalar_one()  
      except NoResultFound:
        return json({"error": "User not found"}, 404)
  if request.method == 'POST':
    data = request.form
    content = data.get('content') 
    comment = Comment(content=content, user_id=user.id)
    session.add(comment)
    await session.commit()
    return redirect(f'/{username}/comments')
  else:
    return jinja.render('add-comment.html', request, username=username)


@bp_user_comments.route('/<username>/comments', methods=['GET', 'POST']) 
async def get_user_comments(request, username):
    if request.method == 'POST':
        comment_id = request.form.get('delete_comment_id')
        if comment_id:
            comment_id = int(comment_id)
            async with async_session() as session:
                async with session.begin():
                    result = await session.execute(select(Comment).where(Comment.id == comment_id))
                    comment = result.scalar_one_or_none()
                    if comment is not None:
                        await session.delete(comment)
    async with async_session() as session:
        async with session.begin():
            user_result = await session.execute(select(User).where(User.username == username))
            user = user_result.scalar_one_or_none()
            if user is not None:
                comment_result = await session.execute(select(Comment).where(Comment.user_id == user.id))
                comments = comment_result.scalars().all()
            else:
                return json({"error": "User not found"}, status=404)
    return jinja.render('user-comments.html', request, username=username, comments=comments)


@bp_user_comments.route('/<username>/comments/<comment_id>/edit', methods=['GET', 'POST']) 
async def edit_comment(request, username, comment_id):
    comment_id = int(comment_id)
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(select(Comment).where(Comment.id == comment_id))
            comment = result.scalar_one_or_none()
            if comment is None:
                return json({"error": "Comment not found"}, status=404)

            if request.method == 'POST':
                comment.content = request.form.get('content')
                await session.commit()
                return redirect(f'/{username}/comments')
            else:
                return jinja.render('edit-comment.html', request, comment=comment)
