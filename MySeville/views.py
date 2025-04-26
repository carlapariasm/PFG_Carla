from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from .forms import RegistroForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from .models import TouristPlace
import googlemaps
from django.http import JsonResponse
from .models import TouristGuide
import re
import math
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
from django.core.mail import send_mail
from django.conf import settings
from .models import ContactMessage  
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .forms import EditarPerfilForm
from django.shortcuts import get_object_or_404
from .models import Review
from datetime import datetime
import requests_cache
from retry_requests import retry
import openmeteo_requests
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from unidecode import unidecode
from django.template.loader import render_to_string
from weasyprint import HTML
from django.conf import settings
from django.shortcuts import render

gmaps = googlemaps.Client(key="AIzaSyB1FuoR7NYuLmY7T0fJrwNY6kn7nlSLlxs")

api_key="AIzaSyB1FuoR7NYuLmY7T0fJrwNY6kn7nlSLlxs"

def home(request):
    return render(request, 'home.html')

@csrf_protect
def registro(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data['email']  
            user.save()
            return redirect('login')  
    else:
        form = RegistroForm()
    return render(request, 'register.html', {'form': form})

@csrf_protect
def iniciar_sesion(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('welcome_page')  
        else:
            return render(request, 'login.html', {'error': 'Incorrect username or password'})
    return render(request, 'login.html')


def cerrar_sesion(request):
    response = redirect('login')  
    logout(request)
    response.delete_cookie('cookiesAccepted')  
    return response


@login_required
def welcome_view(request):
    return render(request, 'welcome_page.html', {'user': request.user})


@login_required
def tourist_guides_view(request):
    user = request.user
    latest_guides = TouristGuide.objects.filter(user=user).order_by('-created_at')[:3]

    return render(request, 'tourist_guides.html', {
        'user': user,
        'latest_guides': latest_guides
    })


def guide_detail(request, pk):
    guide = get_object_or_404(TouristGuide, pk=pk)
    return render(request, 'guide_detail.html', {'guide': guide})


@login_required
def contact_view(request):
    return render(request, 'contact.html')  

@login_required
def new_tourist_guide(request):
    return render(request, 'new_tourist_guide.html', {'user': request.user})
  
@login_required
def generate_tour(request):

    def extract_coords(google_maps_url):
            """
            Extract the (latitude, longitude) coordinates from a Google Maps URL. Assume the URL contains a pattern like @lat,lng. 
            """
            m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', google_maps_url)
            if m:
                return float(m.group(1)), float(m.group(2))
            return None, None

    
    def extract_city(address):
        """Extract the city name from a postal address."""

        #Normalizes and separates
        address = unidecode(address.lower())

        #Cities I have in the BBDD
        known_cities = ['sevilla', 'san sebastian', 'donostia', 'madrid', 'barcelona', 'valencia', 'granada', 'seville']

        for city in known_cities:
            if city in address:
                return city

        return 'desconocido'


    if request.method == "POST":
        guide_title = request.POST.get('guide_title')
        tour_date = request.POST.get('tour_date')
        starting_point = request.POST.get('starting_point')
        ending_point = request.POST.get('ending_point')
        #Extract city from starting point
        city_raw = extract_city(starting_point)
        city = unidecode(city_raw.strip().lower())

        all_places = TouristPlace.objects.all()
        places = [p for p in all_places if unidecode(p.city.strip().lower()) == city]

        print(f"Selected city (normalized): {city}")
        print(f"Total places after city filter: {len(places)}")
        
        #Tour date in datatime format
        tour_date_parsed = datetime.strptime(tour_date, "%Y-%m-%d").date()

        #Obtain weather data from the city
        city_coords = {
                unidecode("Sevilla".lower()): (37.3886, -5.9823),
                unidecode("Madrid".lower()): (40.4165, -3.7026),
                unidecode("Barcelona".lower()): (41.3851, 2.1734),
                unidecode("San Sebastián".lower()): (43.31283, -1.97499),
                unidecode("Granada".lower()): (37.18817, -3.60667),
                unidecode("Valencia".lower()): (39.47391, -0.37966)
            }
        lat, lon = city_coords.get(city, (41.3851, 2.1734))  
        print(f"Ciudad: {city} | Coordenadas: ({lat}, {lon})")


        #API Open-Meteo configuration
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=3, backoff_factor=0.1)
        openmeteo = openmeteo_requests.Client(session=retry_session)

        weather_url = "https://api.open-meteo.com/v1/forecast"
        weather_params = {
            "latitude": lat,
            "longitude": lon,
            "daily": ["precipitation_probability_max", "rain_sum"],
            "timezone": "Europe/Madrid",
            "forecast_days": 16
        }

        weather_response = openmeteo.weather_api(weather_url, params=weather_params)[0]
        weather_daily = weather_response.Daily()

        dates = pd.date_range(
            start=pd.to_datetime(weather_daily.Time(), unit="s", utc=True),
            end=pd.to_datetime(weather_daily.TimeEnd(), unit="s", utc=True),
            freq="D",
            inclusive="left"
        )

        weather_df = pd.DataFrame({
            "date": dates.date,
            "precipitation_probability": weather_daily.Variables(0).ValuesAsNumpy(),
            "rain_sum": weather_daily.Variables(1).ValuesAsNumpy()
        })

        print(weather_df)


        #Manage dates if they are not in the range of the forecast (16 days)
        max_forecast_date = weather_df["date"].max()
        if tour_date_parsed > max_forecast_date:
            # More than 16 days from now:
            print(f"Date {tour_date_parsed} ot of forecast range (hasta {max_forecast_date}), no rain.")
            rain_prob = 0.0
            rain_amount = 0.0
            transport_mode = "walking"
        else:
            weather_today = weather_df[weather_df["date"] == tour_date_parsed]
            if not weather_today.empty:
                rain_prob   = float(weather_today.iloc[0]["precipitation_probability"])
                rain_amount = float(weather_today.iloc[0]["rain_sum"])
                print(f"Forecast for {tour_date_parsed}: {rain_prob}% rain, {rain_amount}mm rain")
                transport_mode = "driving" if rain_prob >= 40 or rain_amount > 0 else "walking"
            else:
                print("No prediction for that day, walking.")
                rain_prob = 0.0
                rain_amount = 0.0
                transport_mode = "walking"
        

        # If it rains, dont take into account outdoor activities selected by the user
        if rain_prob > 0 or rain_amount > 0:
            original_len = len(places)
            places = [p for p in places if p.activity_type != 'outdoor']
            print(f"Filtrados {original_len - len(places)} lugares outdoor por lluvia.")

 
        activity_type = request.POST.getlist('interests')  
        travel_type = request.POST.get('travel_type') 
        budget = request.POST.get('tour_budget')  
        available_time = request.POST.get('available-time')  

        interests_str = ",".join(activity_type)

        TouristGuide.objects.create(
            user=request.user,
            guide_title=guide_title,
            tour_date=tour_date,
            available_time=available_time,
            starting_point=starting_point,
            ending_point=ending_point,
            interests=interests_str,
            travel_type=travel_type,
            tour_budget=budget,
            city=city
        )

        if available_time:
            available_time = int(available_time)
        else:
            available_time = 0
        max_time = available_time * 60  

        print(f"Available time: {available_time} hours ({max_time} mins)")
        print(f"Starting point: {starting_point}")
        print(f"Ending point: {ending_point}")


        if activity_type:
            places = [p for p in places if p.activity_type in activity_type]
        else:
            print("No activity type selected.")
        print(f"Total places after activity type filter: {len(places)}")

        adequacy_values = []
        if travel_type == "1":
            adequacy_values = [0, 1]
        elif travel_type == "2":
            adequacy_values = [0, 2]
        elif travel_type == "3":
            adequacy_values = [0, 3]
        elif travel_type == "4":
            adequacy_values = [0, 4]

        if adequacy_values:
            places = [p for p in places if p.adequacy in adequacy_values]
        print(f"Total places after travel type filter: {len(places)}")

        budget_ranges = {
            'high': (26, 100),
            'moderate': (11, 25),
            'low': (1, 10),
            'free': (0, 0)
        }

        #User budget
        budget_priority = ['high', 'moderate', 'low', 'free']

        selected_budget_places = []
        remaining_places_by_budget = []

        #Take up places from the corresponding category
        for b in budget_priority[budget_priority.index(budget):]:
            min_cost, max_cost = budget_ranges[b]
            budget_group = [p for p in places if min_cost <= p.cost <= max_cost]
            print(f"Lugares encontrados en categoría '{b}': {[p.name for p in budget_group]}")
            if not selected_budget_places:
                #First with the group of activities in the budget
                selected_budget_places = sorted(budget_group, key=lambda x: -x.cost)
            else:
                #Save the rest of activities in case needed to fill spare time
                remaining_places_by_budget.extend(sorted(budget_group, key=lambda x: -x.cost))

        #Cities inside the budget and remaining ones
        combined = selected_budget_places + remaining_places_by_budget

        #Group by activity type
        activity_groups = {atype: [] for atype in activity_type}
        for p in combined:
            if p.activity_type in activity_groups:
                activity_groups[p.activity_type].append(p)

        #Round-robin: change the type of 2 activities that are one after the other
        balanced_places = []
        while any(activity_groups.values()):
            for atype in activity_type:
                if activity_groups[atype]:
                    balanced_places.append(activity_groups[atype].pop(0))

        places = balanced_places

        #Calculate coordinates of the remaining_places_by_budget
        for place in remaining_places_by_budget:
            lat, lng = extract_coords(place.google_maps_url)
            if lat and lng:
                place.coords = (lat, lng)
            else:
                place.coords = None

        print(f"Total places after adaptive budget filter: {len(places)}")
        

        def haversine(coord1, coord2):
            """Calculate the distance (in km) between two coordinates (lat, lon) using the Haversine formula."""
            lat1, lon1 = coord1
            lat2, lon2 = coord2
            R = 6371  
            dLat = math.radians(lat2 - lat1)
            dLon = math.radians(lon2 - lon1)
            a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c

        def get_travel_time(origin, destination, mode="walking"):
            try:
                matrix = gmaps.distance_matrix(
                    origins=[origin],
                    destinations=[destination],
                    mode=mode
                )
                element = matrix['rows'][0]['elements'][0]
                if element['status'] == "OK":
                    return (element['duration']['value'] / 60.0) * 0.8  # Aplica tu factor si quieres
            except Exception as e:
                print("Error en get_travel_time:", e)
            return 0


        def order_places_nn(start_coords, places_list):
            """Order the locations using the nearest neighbor algorithm starting from start_coords."""
            ordered = []
            current = start_coords
            remaining = [p for p in places_list if hasattr(p, 'coords') and p.coords is not None]
            while remaining:
                nearest = min(remaining, key=lambda p: haversine(current, p.coords))
                ordered.append(nearest)
                current = nearest.coords
                remaining.remove(nearest)
            return ordered

        start_geocode = gmaps.geocode(starting_point)
        end_geocode = gmaps.geocode(ending_point)
        if start_geocode and end_geocode:
            starting_coords = (
                start_geocode[0]['geometry']['location']['lat'],
                start_geocode[0]['geometry']['location']['lng']
            )
            ending_coords = (
                end_geocode[0]['geometry']['location']['lat'],
                end_geocode[0]['geometry']['location']['lng']
            )
        else:
            starting_coords = None
            ending_coords = None

        for place in places:
            lat, lng = extract_coords(place.google_maps_url)
            print(f"Place: {place.name} - Coordinates: {lat}, {lng}")
            if lat and lng:
                place.coords = (lat, lng)
            else:
                place.coords = None

        ordered_places = order_places_nn(starting_coords, places)
        print("Ordered places:", ordered_places)


        cumulative_time = 0  
        selected_places = []
        leg_times = []       

        remaining_places = ordered_places[:] 

        remaining = ordered_places[:]   
        selected_places = []
        leg_times = []
        current_coords = starting_coords
        time_used = 0.0

        type_counts = {t: 0 for t in activity_type}

        needed_unique = set(activity_type)

        last_type = selected_places[-1].activity_type if selected_places else None
        second_last_type = selected_places[-2].activity_type if len(selected_places) >= 2 else None

        while remaining and time_used < max_time:
            remaining.sort(key=lambda p: haversine(current_coords, p.coords))

            pick = None
            pick_travel = 0

            for candidate in remaining:
                t = candidate.activity_type

                # Evita más de 1 shopping o gastronomy (excepto si son los únicos tipos)
                if t in ("shopping", "gastronomy") and type_counts[t] >= 1 and len(activity_type) > 1:
                    continue

                # Evita 3 repetidos seguidos
                if last_type == second_last_type == t:
                    continue

                travel = get_travel_time(current_coords, candidate.coords, mode=transport_mode)
                back = get_travel_time(candidate.coords, ending_coords, mode=transport_mode)
                if time_used + travel + candidate.visit_duration + back <= max_time:
                    pick = candidate
                    pick_travel = travel
                    break

            if not pick:
                break  # nada cabe

            selected_places.append(pick)
            leg_times.append(pick_travel)
            time_used += pick_travel + pick.visit_duration
            current_coords = pick.coords
            type_counts[pick.activity_type] += 1
            needed_unique.discard(pick.activity_type)
            remaining.remove(pick)


        last = current_coords if selected_places else starting_coords
        final_leg = get_travel_time(last, ending_coords, mode=transport_mode)
        leg_times.append(final_leg)
        time_used += final_leg
        cumulative_time = time_used

        #Add url of the images
        for place in selected_places:
            if place.image:
                place.image_url = request.build_absolute_uri(place.image.url)
            else:
                place.image_url = ""

        #CREO QUE ESTO SE PUEDE ELIMINAR
        if activity_type:
            print(f"Aplicando round-robin forzado con actividades: {activity_type}")

            # Agrupar lugares por tipo
            activity_groups_final = {atype: [] for atype in activity_type}
            for p in selected_places:
                if p.activity_type in activity_groups_final:
                    activity_groups_final[p.activity_type].append(p)
                else:
                    print(f"Advertencia: lugar '{p.name}' con tipo inesperado '{p.activity_type}'")

            # Intercalar lugares en orden round-robin
            intercalated = []
            exhausted = False
            while not exhausted:
                exhausted = True
                for atype in activity_type:
                    if activity_groups_final[atype]:
                        intercalated.append(activity_groups_final[atype].pop(0))
                        exhausted = False

            selected_places = intercalated
            print("Orden intercalado final:", [p.name for p in selected_places])

        # Recalcular leg_times por el nuevo orden
        leg_times = []
        if selected_places:
            coords_list = [starting_coords] + [p.coords for p in selected_places] + [ending_coords]
            for i in range(len(coords_list) - 1):
                travel_time = get_travel_time(coords_list[i], coords_list[i + 1], mode=transport_mode)
                leg_times.append(travel_time)


        return render(request, "tour_results.html", {
            "places": selected_places,
            "places_data": [
                f"{p.name}||{p.visit_duration}||{p.cost}||{p.activity_type}||{p.image_url}" for p in selected_places
            ],
            "starting_point": starting_point,
            "ending_point": ending_point,
            "leg_times": leg_times,
            "max_time": max_time,
            "used_time": cumulative_time,
            "transport_mode": transport_mode
        })

    else:
        return redirect('new_tourist_guide')


def extract_coords(google_maps_url):
    m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', google_maps_url)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None, None


def get_travel_time(origin, destination, mode="walking"):
    try:
        matrix = gmaps.distance_matrix(
            origins=[origin],
            destinations=[destination],
            mode=mode
        )
        element = matrix['rows'][0]['elements'][0]
        if element['status'] == "OK":
            return (element['duration']['value'] / 60.0) * 0.8  # Aplica tu factor si quieres
    except Exception as e:
        print("Error en get_travel_time:", e)
    return 0


def order_places_nn(start_coords, places_list):
    ordered = []
    current = start_coords
    remaining = [p for p in places_list if p.coords is not None]
    while remaining:
        nearest = min(remaining, key=lambda p: haversine(current, p.coords))
        ordered.append(nearest)
        current = nearest.coords
        remaining.remove(nearest)
    return ordered


def haversine(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371  
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c  

@login_required
def legal_view(request):
    return render(request, 'legal.html')

@login_required
def privacy_view(request):
    return render(request, 'privacy.html')


@login_required
def contact_view(request):
    if request.method == 'POST':
        # Retrieve form data
        name = request.POST['name']
        email = request.POST['email']
        message = request.POST['message']

        # Save the message to the database
        contact_message = ContactMessage(name=name, email=email, message=message)
        contact_message.save()  # Save the form data to the database

        # Format the email message
        full_message = f"From: {name} <{email}>\n\n{message}"

        # Send the email
        send_mail(
            subject="Contact Form - MySeville",
            message=full_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['mysevilleapp@gmail.com'],  
        )

        # Return success response to the user
        return render(request, 'contact.html', {'success': True})

    return render(request, 'contact.html')


@login_required
def dashboard_view(request):
    user = request.user
    print("USER IN SESSION:", user)
    latest_guides = TouristGuide.objects.filter(user=user)
    print("GUIDES FOUND:", latest_guides)

    return render(request, 'tourist_guides.html', {
        'user': user,
        'latest_guides': latest_guides
    })

@csrf_exempt
def aceptar_cookies(request):
    return JsonResponse({'status': 'ok'})

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated correctly.')
            return redirect('profile')
    else:
        form = EditarPerfilForm(instance=request.user)
    
    print("Fields of the form:", form.fields)

    return render(request, 'profile.html', {'form': form})


@login_required
def FAQs(request):
    return render(request, 'FAQs.html')


def reviews_view(request):
    if request.method == 'POST':
        user = request.POST.get('user')
        content = request.POST.get('content')
        if user and content:
            Review.objects.create(user=user, content=content)
            return redirect('reviews')  

    all_reviews = Review.objects.order_by('-created_at')
    return render(request, 'reviews.html', {'reviews': all_reviews})


@csrf_protect
def download_pdf_html(request):
    if request.method == "POST":
        starting_point = request.POST.get("starting_point")
        ending_point   = request.POST.get("ending_point")
        transport_mode = request.POST.get("transport_mode")
        places_data    = request.POST.getlist("places")
        legs           = request.POST.getlist("legs")

        detailed_places = []
        for entry in places_data:
            try:
                name, duration, cost, activity, maps_url, image_url = entry.split("||")
            except ValueError:
                continue
            detailed_places.append({
                "name": name,
                "visit_duration": duration,
                "cost": cost,
                "activity_type": activity,
                "google_maps_url": maps_url,
                "image_url": image_url,
            })

        leg_times = [float(x) for x in legs]

        html_content = render_to_string("tour_result_pdf.html", {
            "starting_point": starting_point,
            "ending_point":   ending_point,
            "transport_mode": transport_mode,
            "places":         detailed_places,
            "leg_times":      leg_times,
        })

        pdf_file = HTML(string=html_content, base_url=request.build_absolute_uri('/')).write_pdf()

        response = HttpResponse(pdf_file, content_type="application/pdf")
        response['Content-Disposition'] = 'attachment; filename="tour_guide.pdf"'
        return response

    return HttpResponse("Invalid request", status=400)

