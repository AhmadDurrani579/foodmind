#
# router/posts.py
# FoodMind Backend
#

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import json

from app.db.database import get_db
from app.db.models_post import PostDB
from app.models.user import User
from app.schemas.post import PostCreate, PostResponse
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/posts",
    tags=["posts"]
)

# ─────────────────────────────────────
# MARK: — Create Post (Share to Feed)
# POST /posts
# ─────────────────────────────────────
@router.post("", response_model=PostResponse)
def create_post(
    data:         PostCreate,
    current_user: User  = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    post = PostDB(
        user_id      = current_user.id,
        scan_id      = data.scan_id,
        caption      = data.caption,
        image_url    = data.image_url,
        dish_name    = data.dish_name,
        cuisine      = data.cuisine,
        calories     = data.calories,
        protein_g    = data.protein_g,
        carbs_g      = data.carbs_g,
        fat_g        = data.fat_g,
        health_score = data.health_score,
        tags         = data.tags
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    print(f"Post created: {post.dish_name} by {current_user.username}")
    return _build_response(post, current_user)


# ─────────────────────────────────────
# MARK: — Get Feed
# GET /posts/feed
# Returns all posts for feed
# ─────────────────────────────────────
@router.get("/feed", response_model=List[PostResponse])
def get_feed(
    limit:        int     = 20,
    offset:       int     = 0,
    current_user: User  = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    # Get posts with user info
    posts = db.query(PostDB)\
        .order_by(PostDB.created_at.desc())\
        .limit(limit)\
        .offset(offset)\
        .all()

    results = []
    for post in posts:
        user = db.query(User)\
            .filter(User.id == post.user_id)\
            .first()
        results.append(_build_response(post, user))

    return results


# ─────────────────────────────────────
# MARK: — Get My Posts
# GET /posts/me
# ─────────────────────────────────────
@router.get("/me", response_model=List[PostResponse])
def get_my_posts(
    limit:        int     = 20,
    offset:       int     = 0,
    current_user: User  = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    posts = db.query(PostDB)\
        .filter(PostDB.user_id == current_user.id)\
        .order_by(PostDB.created_at.desc())\
        .limit(limit)\
        .offset(offset)\
        .all()

    return [_build_response(p, current_user) for p in posts]


# ─────────────────────────────────────
# MARK: — Like Post
# POST /posts/{post_id}/like
# ─────────────────────────────────────
@router.post("/{post_id}/like")
def like_post(
    post_id:      UUID,
    current_user: User  = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    post = db.query(PostDB)\
        .filter(PostDB.id == post_id)\
        .first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post.likes_count += 1
    db.commit()

    return {"likes_count": post.likes_count}


# ─────────────────────────────────────
# MARK: — Delete Post
# DELETE /posts/{post_id}
# ─────────────────────────────────────
@router.delete("/{post_id}")
def delete_post(
    post_id:      UUID,
    current_user: User  = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    post = db.query(PostDB)\
        .filter(
            PostDB.id      == post_id,
            PostDB.user_id == current_user.id
        )\
        .first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    db.delete(post)
    db.commit()

    return {"message": "Post deleted"}


# ─────────────────────────────────────
# MARK: — Helper
# ─────────────────────────────────────
def _build_response(post: PostDB, user: User) -> PostResponse:
    return PostResponse(
        id             = post.id,
        user_id        = post.user_id,
        scan_id        = post.scan_id,
        caption        = post.caption,
        image_url      = post.image_url,
        dish_name      = post.dish_name,
        cuisine        = post.cuisine,
        calories       = post.calories,
        protein_g      = post.protein_g,
        carbs_g        = post.carbs_g,
        fat_g          = post.fat_g,
        health_score   = post.health_score,
        tags           = post.tags,
        likes_count    = post.likes_count,
        comments_count = post.comments_count,
        created_at     = post.created_at,
        username       = user.username   if user else None,
        first_name     = user.first_name if user else None,
        avatar_url     = user.avatar_url if user else None
    )