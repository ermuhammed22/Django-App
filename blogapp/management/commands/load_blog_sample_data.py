from django.core.management import BaseCommand
from blogapp.models import Author, Category, Tag, Article
from django.utils import timezone


class Command(BaseCommand):
    help = 'Load sample data into the blog'

    def handle(self, *args, **options):
        # Создаём автора
        author = Author.objects.create(name='John Doe', bio='Пример автора.')

        # Создаём категорию
        category = Category.objects.create(name='Django')

        # Создаём теги
        tag1 = Tag.objects.create(name='web')
        tag2 = Tag.objects.create(name='python')

        # Создаём статью
        article = Article.objects.create(
            title='Работа с Django ORM',
            content='Пример статьи о Django ORM.',
            pub_date=timezone.now(),
            author=author,
            category=category,
        )

        # Назначаем теги
        article.tags.add(tag1, tag2)

        self.stdout.write(self.style.SUCCESS('Демо-данные успешно загружены.'))
