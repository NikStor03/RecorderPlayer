
from tortoise import fields
from tortoise.models import Model
from database.tools import Services, Languages


class Guilds(Model):

    id = fields.BigIntField(pk=True)
    premium = fields.BooleanField(default=False)
    premium_activate_on = fields.DateField(null=True)
    lang: Languages = fields.TextField(default=Languages.english)  # Lang server
    service: Services = fields.TextField(default=Services.youtube)
    dj_role_id = fields.BigIntField(null=True)
    ban = fields.BooleanField(default=False)
    queue = fields.ManyToManyField(model_name='models.Songs')
    queue_loop = fields.BooleanField(default=False)

    class Meta:
        table = "guilds"
        table_description = "Table about guild where bot is state"

    def __str__(self):
        return f'{self.id}'


class Users(Model):

    user_banned_id = fields.BigIntField(pk=True)

    class Meta:
        table = 'Users'
        table_description = "Table about users short need info"

    def __str__(self):
        return f"{self.user_banned_id}"


class Songs(Model):

    title = fields.TextField()
    serves: Services = fields.TextField()
    link = fields.TextField()
    song_id = fields.TextField()
    loop = fields.BooleanField(default=False)
    thumbnail = fields.TextField()
    author = fields.TextField()
    duration = fields.TextField()
    order = fields.BigIntField()

    class Meta:
        table = 'Songs'
        table_description = "Table about songs which was added to some queueButtons"

    def __str__(self):
        return f"{self.title}"

