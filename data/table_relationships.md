# table relationships

## direct foreign keys
- `product_master.grape_variety -> grape_variety.grape_name`
- `product_master.wine_style -> wine_style.style_name`
- `product_master.spirit_style -> whisky_style.whisky_style`
- `product_master.food_pairing -> wine_food_pairing.food_name`
- `wine_food_pairing.recommended_wine_style -> wine_style.style_name`
- `wine_food_pairing.recommended_grape -> grape_variety.grape_name`

## wine geography and classification design
- `wine_region` now stores only practical geography: `country`, `region`, `subregion` (no synthetic directional placeholders).
- `wine_region.classification_level` and `wine_region.sub_classification` carry market/legal hierarchy labels directly at row level.
- `wine_classification` is a reusable lookup table for country-level classification systems (AOP, DOCG, AVA, etc.).
- recommended join: `wine_region.country = wine_classification.country` and `wine_region.classification_level = wine_classification.classification_level`.

## recommendation matrix usage
- use `wine_style`, `grape_variety`, `wine_flavor_profile`, and `wine_food_pairing` for wine suggestion matrix generation.
- use `spirit_type`, `whisky_style`, and `spirit_flavor_profile` for spirits sales-assist and cross-sell rules.
- use `taste_vector`, `pairing_vector`, and `recommendation_score` in `product_master` as model-ready features.
