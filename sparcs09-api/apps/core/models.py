from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import localtime


class Item(models.Model):
    OPEN = '0'
    CLOSED = '1'
    TYPES = (
        (OPEN, 'Open'),
        (CLOSED, 'Closed')
    )
    title = models.CharField(max_length=100)
    host = models.ForeignKey(User, related_name='items')
    price = models.IntegerField()
    join_type = models.CharField(max_length=2, choices=TYPES)
    created_date = models.DateTimeField()
    deadline = models.DateTimeField()
    delivery_date = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Content(models.Model):
    TEXT = '0'
    IMAGE = '1'
    VIDEO = '2'
    TYPES = (
        (TEXT, 'Text'),
        (IMAGE, 'Image'),
        (VIDEO, 'Video'),
    )
    item = models.ForeignKey(Item, related_name='contents',
                             on_delete=models.CASCADE)
    order = models.IntegerField()
    type = models.CharField(choices=TYPES, max_length=2)
    content = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='image_uploads/',
                              null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    is_hidden = models.BooleanField(default=False)


class Comment(models.Model):
    item = models.ForeignKey(Item, related_name='comments',
                             on_delete=models.CASCADE)
    content = models.TextField()
    writer = models.ForeignKey(User, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)


class OptionCategory(models.Model):
    name = models.CharField(max_length=100)
    item = models.ForeignKey(Item, related_name='option_categories',
                             on_delete=models.CASCADE)


class OptionItem(models.Model):
    name = models.CharField(max_length=100)
    price_delta = models.IntegerField(default=0)
    category = models.ForeignKey(OptionCategory, related_name='option_items',
                                 on_delete=models.CASCADE)


class Record(models.Model):
    participant = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    options= models.ManyToManyField(OptionItem)
    quantity = models.IntegerField()

    def cost(self):
        price = self.item.price
        for optItem in self.options.all():
            price += optItem.price_delta

        return price * self.quantity


class Payment(models.Model):
    PENDING = '0'
    JOINED = '1'
    PAID = '2'
    STATUS = (
        (PENDING, 'Pending'),
        (JOINED, 'Joined'),
        (PAID, 'Paid')
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    participant = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.IntegerField()
    status = models.CharField(max_length=2, choices=STATUS)

    def __str__(self):
        return f'{self.participant}: {self.total} for {self.item}'


class UserLog(models.Model):
    """
    denotes single log for an user or global event
    - user:  user object
    - level: level of log; python log level
    - time:  event time
    - ip:    event ip
    - group: log group
    - text:  detail log message
    - is_hidden:  hide log in user log page
    """
    GROUP_ACCOUNT = 'sparcs09.account'
    GROUPS = [
        (GROUP_ACCOUNT, GROUP_ACCOUNT),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='user_logs', blank=True, null=True)
    level = models.IntegerField()
    time = models.DateTimeField(auto_now=True)
    ip = models.GenericIPAddressField()
    group = models.CharField(max_length=100, choices=GROUPS)
    text = models.CharField(max_length=500)
    is_hidden = models.BooleanField(default=False)

    def pretty(self):
        username = self.user.username if self.user else 'undefined'
        time_str = localtime(self.time).isoformat()
        return (f'{username}/{time_str} ({self.level}, {self.ip}) '
                '{self.group}.{self.text}')

    def __str__(self):
        time_str = localtime(self.time).isoformat()
        return (f'{time_str}/{self.level} ({self.user}) '
                '{self.group}.{self.text}')