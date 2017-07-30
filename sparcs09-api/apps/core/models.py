from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import localtime


class Item(models.Model):
    """
    Represents a single 09 item.

    Attributes:
        title: the title of this item
        host: the manager of this item
        price: the default price - can be changed by option items
        join_type: the join type - one of JOIN_TYPE_CHOICES
        created_date: the created date
        deadline: the deadline - user cannot join 09 after this deadline
        delivery_date: expected delivery date (can be null)
        is_deleted: the deleted flag
    """

    JOIN_TYPE_OPEN = '0'
    JOIN_TYPE_CLOSED = '1'
    JOIN_TYPE_CHOICES = (
        (JOIN_TYPE_OPEN, 'Open'),
        (JOIN_TYPE_CLOSED, 'Closed')
    )
    title = models.CharField(max_length=100)
    host = models.ForeignKey(User, related_name='items')
    price = models.IntegerField()
    join_type = models.CharField(max_length=2, choices=JOIN_TYPE_CHOICES)
    created_date = models.DateTimeField()
    deadline = models.DateTimeField()
    delivery_date = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Content(models.Model):
    """
    Represents a text, image or video content of a 09 item.

    Attributes:
        item: the item that this content belongs to
        order: the order of this content in the item (starts from 1)
        type: the type of this content - one of CONTENT_TYPE_CHOICES
        content: the text messages (available iff type=0)
        image: the image file (available iff type=1)
        link: the link of the Youtube video (available iff type=2)
        is_hidden: the hidden flag - if true, it will be folded in the item
                   page as default
    """

    CONTENT_TYPE_TEXT = '0'
    CONTENT_TYPE_IMAGE = '1'
    CONTENT_TYPE_VIDEO = '2'
    CONTENT_TYPE_CHOICES = (
        (CONTENT_TYPE_TEXT, 'Text'),
        (CONTENT_TYPE_IMAGE, 'Image'),
        (CONTENT_TYPE_VIDEO, 'Video'),
    )
    item = models.ForeignKey(Item, related_name='contents',
                             on_delete=models.CASCADE)
    order = models.IntegerField()
    type = models.CharField(max_length=2, choices=CONTENT_TYPE_CHOICES)
    content = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='image_uploads/',
                              null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    is_hidden = models.BooleanField(default=False)


class Comment(models.Model):
    """
    Represents a single comment on a 09 item.

    Attributes:
        item: the item that this comment belongs to
        content: the text of this comment
        writer: the writer of this comment
        created_date: the created datetime
        is_deleted: the deleted flag
    """

    item = models.ForeignKey(Item, related_name='comments',
                             on_delete=models.CASCADE)
    content = models.TextField()
    writer = models.ForeignKey(User, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)


class OptionCategory(models.Model):
    """
    Represents a option category of a 09 item.

    Attributes:
        name: the name of the option category
        item: the item that this OptionCategory belongs to
    """
    name = models.CharField(max_length=100)
    item = models.ForeignKey(Item, related_name='option_categories',
                             on_delete=models.CASCADE)


class OptionItem(models.Model):
    """
    Represents an option item of an option category.

    Attributes:
        name: the name of the option item
        price_delta: price difference respected to the item price
        category: the option category that this option item belongs to
    """

    name = models.CharField(max_length=100)
    price_delta = models.IntegerField(default=0)
    category = models.ForeignKey(OptionCategory, related_name='option_items',
                                 on_delete=models.CASCADE)


class Record(models.Model):
    """
    Represents a participation record for an user + a 09 item + an option.

    Attributes:
        participant: the participated user
        item: the item that the user has been participated
        options: list of option item that the user was selected - they should
                 be selected exactly one in each option categories of the item
        quantity: the quantity for the fixed options
    """
    participant = models.ForeignKey(User, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    options = models.ManyToManyField(OptionItem)
    quantity = models.IntegerField()

    def cost(self):
        price = self.item.price
        for optItem in self.options.all():
            price += optItem.price_delta

        return price * self.quantity


class Payment(models.Model):
    """
    Represents a payment record for an user + a 09 item.

    Attributes:
        item: the item that the user has been particiapted
        participant: the participated user
        total: total amount to pay - summation of record.cost()
        status: payment status - one of STATUS_CHOICES
    """
    STATUS_PENDING = '0'
    STATUS_JOINED = '1'
    STATUS_PAID = '2'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_JOINED, 'Joined'),
        (STATUS_PAID, 'Paid')
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    participant = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.IntegerField()
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)

    def __str__(self):
        return f'{self.participant}: {self.total} for {self.item}'


class UserLog(models.Model):
    """
    Represents a single log for an user or global event.

    Attributes:
        user: the event user (none in case of global event)
        level: the event level - uses python log level convention
        time: the time of this event
        ip: the event ip (0.0.0.0 in case of unknown)
        group: the event group - one of GROUP_CHOICES
        text: the message of this event
        is_hidden: the hidden flag - hide from users iff true
    """
    GROUP_ACCOUNT = 'sparcs09.account'
    GROUP_CHOICES = [
        (GROUP_ACCOUNT, GROUP_ACCOUNT),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name='user_logs', blank=True, null=True)
    level = models.IntegerField()
    time = models.DateTimeField(auto_now=True)
    ip = models.GenericIPAddressField()
    group = models.CharField(max_length=100, choices=GROUP_CHOICES)
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
