from django.conf import settings
from django.db import models
from django.utils import timezone
# Create your models here.



# Custom manager class
#
class PublishedManager(models.Manager):
    def get_queryset(self):
        return (
            super().get_queryset().filter(status = Post.Status.PUBLISHED)
            )


# New class to define a Post model
# for storing blog posts in the database
class Post(models.Model):
    
    # Class to allow blog posts to be saved as drafts until ready for publishing
    class Status(models.TextChoices):
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'

    # Field for the post title (CharField that translates into a VARCHAR column)
    title = models.CharField(max_length=250)

    # Short label that contains only letters, numbers, underscores, or hyphens
    slug = models.SlugField(max_length=250)

    # Author field defining a many-to-one relationship 
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, # used to delete all posts related to referenced user when the user account is deleted
        related_name= 'blog_posts'
        )

    # Field for storing the body of the post (TextField that translates into a TEXT column)
    body = models.TextField()

    # DataTimeField that translates into a DATETIME column (used to store the date and time of post)
    publish = models.DateTimeField(default=timezone.now)

    # Automatically save the date and time when post is created
    created = models.DateTimeField(auto_now_add=True)

    # Automatically save the date and time when the post was last updated
    updated = models.DateTimeField(auto_now=True)

    status = models.CharField(
        max_length=2,
        choices=Status,
        default=Status.DRAFT
        )

    objects = models.Manager() # The default manager
    published = PublishedManager() # Custom manager

    # Class to define the metadate for the model, used for ordering
    # the results by the publish field
    class Meta:
        ordering = ['-publish']
        indexes =  [
            models.Index(fields=['-publish']),    
        ]


    # Method for returning a string object
    def __str__(self):
        return self.title
