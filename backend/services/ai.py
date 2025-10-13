import os
import random
from typing import List, Optional
from backend.models.schemas import Draft, PriceSuggestion, Condition


class AIService:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.mock_mode = not self.openai_key
    
    def generate_listing(self, image_urls: List[str], uploaded_files: Optional[List[str]] = None) -> Draft:
        if self.mock_mode:
            return self._generate_mock_listing(image_urls)
        else:
            return self._generate_ai_listing(image_urls)
    
    def _generate_mock_listing(self, image_urls: List[str]) -> Draft:
        brands = ["Nike", "Adidas", "Zara", "H&M", "Ralph Lauren", "Tommy Hilfiger", "Lacoste", "Pull&Bear"]
        categories = ["T-shirt", "Pull", "Veste", "Pantalon", "Robe", "Jupe", "Chemise", "Hoodie"]
        sizes = ["XS", "S", "M", "L", "XL", "XXL"]
        conditions = [Condition.NEW_WITH_TAGS, Condition.NEW_WITHOUT_TAGS, Condition.VERY_GOOD, Condition.GOOD]
        
        brand = random.choice(brands)
        category = random.choice(categories)
        size = random.choice(sizes)
        condition = random.choice(conditions)
        
        title = f"{category} {brand} {size}"
        
        condition_texts = {
            Condition.NEW_WITH_TAGS: "neuf avec étiquette, jamais porté",
            Condition.NEW_WITHOUT_TAGS: "neuf sans étiquette, jamais porté",
            Condition.VERY_GOOD: "très bon état, porté quelques fois",
            Condition.GOOD: "bon état général, quelques signes d'usage"
        }
        
        materials = ["coton", "polyester", "laine", "lin", "coton bio", "mélange coton-polyester"]
        material = random.choice(materials)
        
        descriptions = [
            f"{category} {brand} en {material}, {condition_texts[condition]}. Coupe {random.choice(['droite', 'ajustée', 'ample', 'cintrée'])}. {random.choice(['Lavé et repassé', 'Nettoyé à sec', 'Lavé en machine'])}, prêt à porter !",
            f"Magnifique {category.lower()} de la marque {brand}, {condition_texts[condition]}. Matière {material} de qualité. {random.choice(['Parfait pour la saison', 'Intemporel', 'Tendance actuelle'])} !",
            f"{category} {brand} taille {size}, {condition_texts[condition]}. En {material}, très confortable. {random.choice(['Couleur fidèle aux photos', 'Belle finition', 'Détails soignés'])}."
        ]
        
        keywords = [brand.lower(), category.lower(), material, size.lower()]
        if random.random() > 0.5:
            keywords.extend(random.sample(["vintage", "authentique", "rare", "collection", "tendance"], k=2))
        
        base_price = random.randint(15, 80)
        min_price = base_price * 0.7
        max_price = base_price * 1.3
        
        sale_score = random.randint(60, 95)
        if brand in ["Nike", "Adidas", "Ralph Lauren"]:
            sale_score = min(95, sale_score + 10)
        
        return Draft(
            title=title,
            description=random.choice(descriptions),
            brand=brand,
            category_guess=category,
            condition=condition,
            size_guess=size,
            keywords=keywords,
            price_suggestion=PriceSuggestion(
                min=round(min_price, 2),
                max=round(max_price, 2),
                target=round(base_price, 2),
                justification=f"Prix basé sur la marque {brand}, état {condition.value}, et demande actuelle pour {category}"
            ),
            image_urls=image_urls,
            possible_duplicate=False,
            estimated_sale_score=sale_score
        )
    
    def _generate_ai_listing(self, image_urls: List[str]) -> Draft:
        return self._generate_mock_listing(image_urls)


ai_service = AIService()
