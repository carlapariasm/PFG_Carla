from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class CustomUser(AbstractUser):
    NATIONALITY_CHOICES = [
        ('ES', 'Spanish'),
        ('FR', 'French'),
        ('IT', 'Italian'),
        ('DE', 'German'),
        ('UK', 'British'),
        ('US', 'American'),
        ('MX', 'Mexican'),
        ('AR', 'Argentinian'),
        ('BR', 'Brazilian'),
        ('CA', 'Canadian'),
        ('JP', 'Japanese'),
        ('CN', 'Chinese'),
        ('IN', 'Indian'),
        ('RU', 'Russian'),
        ('NL', 'Dutch'),
        ('SE', 'Swedish'),
        ('NO', 'Norwegian'),
        ('PT', 'Portuguese'),
        ('AU', 'Australian'),
        ('BE', 'Belgian'),
        ('CH', 'Swiss'),
        ('CL', 'Chilean'),
        ('CO', 'Colombian'),
        ('PE', 'Peruvian'),
        ('VE', 'Venezuelan'),

    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField()
    nationality = models.CharField(max_length=100, choices=NATIONALITY_CHOICES, default='ES')  # Cambiado a choices
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username


class TouristPlace(models.Model):
    name = models.CharField(max_length=255)
    
    HISTORICAL_SITES = 'historical-sites'
    CULTURAL_EXPERIENCES = 'cultural-experiences'
    GASTRONOMY = 'gastronomy'
    SHOPPING = 'shopping'
    OUTDOOR_ACTIVITIES = 'outdoor'
    LITERARY = 'literary'
    SCIENTIFIC = 'scientific'
    ENTERTAINMENT = 'entertainment'


    ACTIVITY_TYPE_CHOICES = [
        (HISTORICAL_SITES, 'historical-sites'),
        (CULTURAL_EXPERIENCES, 'cultural-experiences'),
        (GASTRONOMY, 'gastronomy'),
        (SHOPPING, 'shopping'),
        (OUTDOOR_ACTIVITIES, 'outdoor'),
        (LITERARY, 'literary'),
        (SCIENTIFIC, 'scientific'),
        (ENTERTAINMENT, 'entertainment'),
    ]
    
    activity_type = models.CharField(
        max_length=50,
        choices=ACTIVITY_TYPE_CHOICES,
    )
    
    visit_duration = models.PositiveIntegerField(help_text="Duration in minutes")
    cost = models.DecimalField(max_digits=10, decimal_places=2)

    ADEQUACY_CHOICES = [
        (0, 'Adequate for all types of tourists'),
        (1, 'Adequate only for people traveling for work'),
        (2, 'Adequate only for people traveling in partners'),
        (3, 'Adequate only for people traveling with family (18+ years old)'),
        (4, 'Adequate only for people traveling with family (children below 18)'),
    ]

    adequacy = models.IntegerField(choices=ADEQUACY_CHOICES, default=0)

    latitude = models.FloatField()

    longitude = models.FloatField()

    google_maps_url = models.URLField(max_length=200, blank=True, null=True)

    city = models.CharField(max_length=255, default='Sevilla')  

    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)

    image = models.ImageField(upload_to='tourist_place_images/', null=True, blank=True)


    def __str__(self):
        return self.name




class TouristGuide(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='tourist_guides',
        null=True,  
        blank=True  
    )

    guide_title = models.CharField(max_length=255, null=True)
    tour_date = models.DateField(null=True)
    available_time = models.IntegerField(null=False, default=1)  
    starting_point = models.CharField(max_length=255, null=True)
    ending_point = models.CharField(max_length=255, null=True)
    interests = models.TextField(null=True)  
    travel_type = models.CharField(max_length=255, null=True)
    tour_budget = models.CharField(max_length=50, null=True)
    city = models.CharField(max_length=255, null=False, blank=False, default="Seville")  
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False)

    def __str__(self):
        return f"{self.guide_title} - {self.tour_date}"

    @property
    def location(self):
        return f"{self.latitude},{self.longitude}"


    
class ContactMessage(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return f"Message from {self.name} ({self.email})"


class Review(models.Model):
    user = models.CharField(max_length=100)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.created_at.strftime('%Y-%m-%d')}"
