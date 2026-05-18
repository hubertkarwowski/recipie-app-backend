from bs4 import BeautifulSoup
from app.celery_app import celery
import requests 
import json
import time
import random
from sqlmodel import Session, select
from app.db.engine import engine
from app.models.Recipe import Recipe, Ingredient
from app.services.scraper_schema import Diet, IngredientData, RecipeData
def get_content():
        url = 'https://aniagotuje.pl/pomysl-na/obiad'
        website_content = requests.get(url)
        soup = BeautifulSoup(website_content.content, 'html.parser')
        return soup

def get_pages():
        soup = get_content()
        page_items = soup.select("li.page-item a.page-link")
        last_page = page_items[-2].get_text(strip=True) 
        return int(last_page)


def get_recipe_links(soup):
    for script in soup.select("script[type='application/ld+json']"):
        try:
            data = json.loads(script.string)
            if data.get("@type") == "ItemList":
                return [item["url"] for item in data["itemListElement"]]
        except:
            Exception
    return []
        
    
def get_all_links():
    all_links = []
    total_pages = get_pages()
    print(f"Liczba stron: {total_pages}")
    
    for page in range(1, total_pages + 1):
        if page == 1:
            url = 'https://aniagotuje.pl/pomysl-na/obiad'
        else:
            url = f'https://aniagotuje.pl/pomysl-na/obiad/strona/{page}'
        
        soup = BeautifulSoup(requests.get(url).content, 'html.parser')
        links = get_recipe_links(soup)
        all_links.extend(links)
        print(f"Strona {page}/{total_pages} — znaleziono {len(links)} linków")
    
    print(f"Łącznie: {len(all_links)} przepisów")
    return all_links



def parse_recipe(url):
    time.sleep(random.uniform(1.5, 3.0))
    soup = BeautifulSoup(requests.get(url).content, 'html.parser')
    
    title = soup.select_one("h1").get_text(strip=True)
    
    img_tag = soup.select_one("div.article-main-google-img-wrapper img")
    img = img_tag.get("src") if img_tag else None

    calories = soup.select_one("span[itemprop='calories']")
    carbs    = soup.select_one("span[itemprop='carbohydrateContent']")
    protein  = soup.select_one("span[itemprop='proteinContent']")
    fat      = soup.select_one("span[itemprop='fatContent']")

    DIET_MAP = {
        "VegetarianDiet": "vegetarian",
        "VeganDiet":      "vegan",
        "GlutenFreeDiet": "gluten_free",
        "RestrictedDiet": "low_sugar",
        "LowCalorieDiet": "low_calorie",
        "LowFatDiet":     "low_fat",
    }
    diets: list[Diet] = []
    for link in soup.select("link[itemprop='suitableForDiet']"):
        href = link.get("href", "")
        for key, label in DIET_MAP.items():
            if key in href:
                diets.append(label)

    # składniki
    ingredients: list[IngredientData] = []
    for li in soup.select("#recipeIngredients li"):
        name = li.select_one("span.ingredient")
        qty  = li.select_one("span.qty")
        if name:
            ingredients.append({
                "name": name.get_text(strip=True),
                "qty":  qty.get_text(strip=True) if qty else None
            })

    return RecipeData(
        title=title,
        img=img,
        calories=calories.get_text(strip=True) if calories else None,
        carbs=carbs.get_text(strip=True) if carbs else None,
        protein=protein.get_text(strip=True) if protein else None,
        fat=fat.get_text(strip=True) if fat else None,
        diets=diets,
        ingredients=ingredients,
    )

def save_recipe(data:RecipeData, url:str):
    with Session(engine) as db:
        existing = db.exec(select(Recipe).where(Recipe.source_url == url)).first()
        if existing:
            print(f"Przepis już istnieje w bazie: {data.title}")
            return
        
        recipe = Recipe(
            name       = data.title,
            image_url  = data.img,
            source_url = url,
            labels     = [diet.value for diet in data.diets],
            calories   = data.calories,
            carbs      = data.carbs,
            protein    = data.protein,
            fat        = data.fat,
        )
        db.add(recipe)
        db.flush()
        
        for ing in data.ingredients:
            db.add(Ingredient(
                recipe_id =recipe.id,
                name = ing.name,
                qty = ing.qty
            ))

        db.commit()
        print(f"Zapisano przepis: {data.title}")


@celery.task
def scrape_recipes():
    links = get_all_links()
    for i, url in enumerate(links[:5], 1):
        print(f"{i}/{len(links)} — {url}")
        data = parse_recipe(url)
        save_recipe(data, url)