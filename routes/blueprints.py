from routes.user_routes import bp_user
from routes.user_comments import bp_user_comments
from routes.user_posts import bp_user_posts

# from .other_routes import bp_other  # import other blueprints as needed

blueprints = [
    bp_user, 
    bp_user_comments,
    bp_user_posts
    ]