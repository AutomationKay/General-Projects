from turtle import ht
from django.shortcuts import render
from .models import Post
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.core.paginator import EmptyPage, PageNotAnInteger,Paginator


# Create your views here.


# Retrieve all posts with the PUBLISHED status using the published manager
def post_list(request):
    post_list = Post.published.all()
    # Pagination with 3 post per page
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        # If page_number is not an integer then get the first page
        posts = paginator.page(1)
    except EmptyPage:
        # If page_number is out of range, get last page of results instead
        posts = paginator.page(paginator.num_pages)
    return render(
        request,
        'blog/post/list.html',
        {'posts' : posts}
        )

# If no fields matches the request, raise DoesNotExist error 
def post_detail(request, year, month, day, post):
    post = get_object_or_404(
        Post,
        status = Post.Status.PUBLISHED,
        slug=post,
        publish__year=year,
        publish__month=month,
        publish__day=day
        )
    return render(
        request,
        'blog/post/detail.html',
        {'post' : post}
        )
