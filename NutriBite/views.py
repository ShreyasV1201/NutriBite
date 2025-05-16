# NutriBite/views.py
from django.shortcuts       import render, redirect, get_object_or_404
from django.contrib.auth    import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.views.decorators.http    import require_POST
from django.core.cache      import cache
from django.urls            import reverse, reverse_lazy
from django.http            import HttpResponseBadRequest
from django.conf            import settings

import requests, random

from .models    import FavoriteRecipe, Recipe
from .forms     import SignInForm, RecipeForm, UserCreationForm

# —————————————————————————————————————————————————————————————
# 1) Landing pages, auth, dashboard, add/edit/delete recipes, etc.
# —————————————————————————————————————————————————————————————

def home(request):
    return render(request, 'home.html')

def sign_up(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'sign_up.html', {'form': form})

class NutriBiteLoginView(LoginView):
    template_name             = 'sign_in.html'
    authentication_form       = SignInForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('home')

    def form_valid(self, form):
        remember = self.request.POST.get('remember') == 'on'
        if not remember:
            self.request.session.set_expiry(0)
        return super().form_valid(form)

class MyLogoutView(LogoutView):
    pass


def dashboard(request):
    # ─── Trending Recipes (cached random meals) ────────────────────────────────
    cache_key = "trending_meals"
    meals = cache.get(cache_key)
    if not meals:
        meals = []
        for _ in range(10):
            try:
                resp = requests.get(
                    "https://www.themealdb.com/api/json/v1/1/random.php",
                    timeout=5
                )
                resp.raise_for_status()
                m = resp.json().get("meals", [None])[0]
                if m:
                    meals.append({
                        "title":     m["strMeal"],
                        "image":     m["strMealThumb"],
                        "sourceUrl": reverse("view_recipe", args=[m['idMeal']]),
                    })
            except requests.RequestException:
                # if one fetch fails, just skip it
                continue

        # cache whatever you managed to fetch (up to 10)
        if meals:
            cache.set(cache_key, meals, 300)

    # ensure we only ever give the template at most 10 items
    trending = meals[:10]

    # ─── Fun Facts (cached trivia) ─────────────────────────────────────────────
    trivia_cache_key = "nutrition_trivia"
    trivia_list = cache.get(trivia_cache_key)
    if trivia_list is None:
        trivia_list = [
            "Did you know? An average banana has about 105 calories and 3 grams of fiber.",
            "Tip: Almonds provide more calcium per ounce than milk!",
            "Fun fact: Chickpeas are a complete protein when paired with grains.",
        ]
        random.shuffle(trivia_list)
        cache.set(trivia_cache_key, trivia_list, 300)

    # ─── Favorites ──────────────────────────────────────────────────────────────
    if request.user.is_authenticated:
        favorites = FavoriteRecipe.objects.filter(user=request.user)
    else:
        favorites = FavoriteRecipe.objects.none()

    # ─── Render ─────────────────────────────────────────────────────────────────
    return render(request, "dashboard.html", {
        "trending":    trending,
        "trivia_list": trivia_list,
        "favorites":   favorites,
    })

def add_recipe(request):
    if not request.user.is_authenticated:
        return redirect('sign_in')

    if request.method == 'POST':
        form = RecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.ingredients = form.cleaned_data['ingredients'].strip()
            recipe.user = request.user
            recipe.save()
            return redirect('add_recipe')
    else:
        form = RecipeForm()

    recipes = Recipe.objects.filter(user=request.user).order_by("-id")
    return render(request, 'addRecipe.html', {
        'form': form,
        'recipes': recipes,
    })


def edit_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == 'POST':
        form = RecipeForm(request.POST, instance=recipe)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.ingredients = form.cleaned_data['ingredients'].strip()
            recipe.save()
            return redirect('add_recipe')
    else:
        form = RecipeForm(
            instance=recipe,
            initial={'ingredients': recipe.ingredients}
        )
    return render(request, 'addRecipe.html', {
        'form': form,
        'recipes': Recipe.objects.all(),
    })


def delete_recipe(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk)
    if request.method == 'POST':
        recipe.delete()
        return redirect('add_recipe')
    return render(request, 'confirmDelete.html', {'recipe': recipe})


# —————————————————————————————————————————————————————————————
# 2) Browse MealDB recipes & toggle favorites
# —————————————————————————————————————————————————————————————

def browse_recipes(request):
    cats = cache.get("mealdb_categories")
    if not cats:
        r = requests.get(
            "https://www.themealdb.com/api/json/v1/1/list.php?c=list",
            timeout=5
        )
        r.raise_for_status()
        cats = [c["strCategory"] for c in r.json().get("meals", [])]
        cache.set("mealdb_categories", cats, 600)

    selected_cat = request.GET.get("category", "")
    results = []
    if selected_cat:
        resp = requests.get(
            "https://www.themealdb.com/api/json/v1/1/filter.php",
            params={"c": selected_cat},
            timeout=5
        )
        resp.raise_for_status()
        for m in resp.json().get("meals", []):
            results.append({
                "mealdb_id": m["idMeal"],
                "fdc_id":    None,
                "title":     m["strMeal"],
                "image":     m["strMealThumb"],
            })

    favourited_ids = set()
    if request.user.is_authenticated:
        favourited_ids = set(
            FavoriteRecipe.objects
                          .filter(user=request.user)
                          .values_list("mealdb_id", flat=True)
        )

    return render(request, "browseRecipes.html", {
        "categories":     cats,
        "selected_cat":   selected_cat,
        "results":        results,
        "favourited_ids": favourited_ids,
    })



# —————————————————————————————————————————————————————————————
# 3) USDA search & detail, MealDB detail, and view‐recipe
# —————————————————————————————————————————————————————————————

def search_usda(query):
    url = f"{settings.FDC_BASE_URL}/foods/search"
    params = {
        "api_key": settings.USDA_API_KEY,
        "query":   query,
        "pageSize": 12,
    }
    resp = requests.get(url, params=params, timeout=5)
    resp.raise_for_status()
    return resp.json().get("foods", [])


def nutrition_info(request):
    q         = request.GET.get("q", "").strip()
    mealdb_id = request.GET.get("mealdb_id")
    fdc_id    = request.GET.get("fdc_id")

    # A) free‐text USDA search
    if q and not mealdb_id and not fdc_id:
        foods = search_usda(q)
        seen, unique = set(), []
        for f in foods:
            key = f["description"].strip().lower()
            if key in seen:
                continue
            seen.add(key)
            unique.append({
                "description": f["description"],
                "fdcId":       f["fdcId"],
                "dataType":    f.get("dataType",""),
                "image":       fetch_image_for(f["description"]),
            })

        favourited_ids = set()
        if request.user.is_authenticated:
            favourited_ids = set(
                FavoriteRecipe.objects
                              .filter(user=request.user)
                              .values_list("fdc_id", flat=True)
            )

        return render(request, "NutritionInfo.html", {
            "search_query":   q,
            "foods":          unique,
            "favourited_ids": favourited_ids,
        })

    # B) MealDB detail lookup → mealDetail.html w/ favorite button
    if mealdb_id:
        resp = requests.get(
            "https://www.themealdb.com/api/json/v1/1/lookup.php",
            params={"i": mealdb_id},
            timeout=5
        )
        resp.raise_for_status()
        meal = resp.json().get("meals", [None])[0]
        if not meal:
            return HttpResponseBadRequest("Meal not found.")

        favourited_ids = set()
        if request.user.is_authenticated:
            favourited_ids = set(
                FavoriteRecipe.objects
                              .filter(user=request.user)
                              .values_list("mealdb_id", flat=True)
            )

        # extract up to 20 ingredients
        ingredients = []
        for i in range(1, 21):
            name = meal.get(f"strIngredient{i}")
            amt  = meal.get(f"strMeasure{i}")
            if name and name.strip():
                ingredients.append({"name": name.strip(), "measure": amt.strip()})

        return render(request, "mealDetail.html", {
            "meal":           meal,
            "ingredients":    ingredients,
            "favourited_ids": favourited_ids,
        })

    # C) USDA detail lookup (guard against fdc_id="None" or empty)
    if fdc_id and fdc_id not in ("None", ""):
        resp = requests.get(
            f"https://api.nal.usda.gov/fdc/v1/food/{fdc_id}",
            params={"api_key": settings.USDA_API_KEY},
            timeout=5
        )
        resp.raise_for_status()
        food = resp.json()

        nutrients = []
        for n in food.get("foodNutrients", []):
            name  = n.get("nutrientName") or n.get("nutrient", {}).get("name")
            value = n.get("value")         or n.get("amount")
            unit  = n.get("unitName")      or n.get("nutrient", {}).get("unitName")
            if name and value is not None and unit:
                nutrients.append({"name": name, "value": value, "unit": unit})

        steps = get_cooking_steps(food.get("description",""))

        favourited_ids = set()
        if request.user.is_authenticated:
            favourited_ids = set(
                FavoriteRecipe.objects
                              .filter(user=request.user)
                              .values_list("fdc_id", flat=True)
            )

        return render(request, "NutritionInfo.html", {
            "food":            food,
            "nutrients":       nutrients,
            "steps":           steps,
            "favourited_ids":  favourited_ids,
        })

    # D) blank
    return render(request, "NutritionInfo.html", {
        "foods":          [],
        "search_query":   "",
        "favourited_ids": set(),
    })

def get_cooking_steps(dish_name):
    """
    Search TheMealDB by name and split the instructions into steps.
    """
    resp = requests.get(
        "https://www.themealdb.com/api/json/v1/1/search.php",
        params={"s": dish_name},
        timeout=5
    )
    resp.raise_for_status()
    meals = resp.json().get("meals")
    if not meals:
        return []
    raw = meals[0].get("strInstructions", "")
    return [step.strip() for step in raw.split("\r\n") if step.strip()]


def fetch_image_for(name):
    try:
        resp = requests.get(
            "https://www.themealdb.com/api/json/v1/1/search.php",
            params={"s": name}, timeout=5
        )
        resp.raise_for_status()
        data = resp.json().get("meals")
        if not data:
            return None
        return data[0].get("strMealThumb")
    except requests.RequestException:
        return None


def view_recipe(request, mealdb_id):
    try:
        resp = requests.get(
            "https://www.themealdb.com/api/json/v1/1/lookup.php",
            params={"i": mealdb_id}, timeout=5
        )
        resp.raise_for_status()
        meal = resp.json()["meals"][0]
    except Exception:
        return render(request, "viewRecipe.html", {
            "error": "Sorry, could not load that recipe."
        })

    ingredients = []
    for i in range(1, 21):
        name = meal.get(f"strIngredient{i}")
        amt  = meal.get(f"strMeasure{i}")
        if name and name.strip():
            ingredients.append({"name": name.strip(), "measure": amt.strip()})

    favourited_ids = set()
    if request.user.is_authenticated:
        favourited_ids = set(
            FavoriteRecipe.objects
                          .filter(user=request.user)
                          .values_list("mealdb_id", flat=True)
        )

    return render(request, "viewRecipe.html", {
        "meal":           meal,
        "ingredients":    ingredients,
        "favourited_ids": favourited_ids,
    })

@require_POST
@login_required
def toggle_favourite(request):
    """
    Add or remove a FavoriteRecipe for the logged-in user,
    based on whether it already exists.
    """
    mealdb_id = request.POST.get("mealdb_id")
    fdc_id    = request.POST.get("fdc_id")
    title     = request.POST.get("title", "")
    image     = request.POST.get("image", "")

    # Build lookup dict for either MealDB or FDC favorites
    lookup = {"user": request.user}
    if mealdb_id:
        lookup["mealdb_id"] = mealdb_id
    else:
        lookup["fdc_id"] = fdc_id

    existing = FavoriteRecipe.objects.filter(**lookup)
    if existing.exists():
        # If already a favorite, delete it (i.e. “remove”)
        existing.delete()
    else:
        # Otherwise create a new favorite
        FavoriteRecipe.objects.create(
            user      = request.user,
            mealdb_id = mealdb_id,
            fdc_id    = fdc_id,
            title     = title,
            image     = image,
        )

    # Redirect back to wherever the form was submitted from
    return redirect(request.META.get("HTTP_REFERER", "dashboard"))
