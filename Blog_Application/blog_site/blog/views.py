from turtle import ht
from django.shortcuts import render
from .models import Post
from django.http import Http404
from django.shortcuts import get_object_or_404, render


# Create your views here.


# Retrieve all posts with the PUBLISHED status using the published manager
def post_list(request):
    posts = Post.published.all()
    return render(
        request,
        'blog/post/list.html',
        {'posts' : posts}
        )

# If no ID matches the request, raise DoesNotExist error 
def post_detail(request, id):
    post = get_object_or_404(
        Post,
        id=id,
        status = Post.Status.PUBLISHED
        )
    return render(
        request,
        'blod/post/detail.html',
        {'post' : post}
        )
