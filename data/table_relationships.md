# table relationships

## direct foreign keys
- `product_master.grape_variety -> grape_variety.grape_name`
- `product_master.wine_style -> wine_style.style_name`
- `product_master.spirit_style -> whisky_style.whisky_style`
- `product_master.food_pairing -> wine_food_pairing.food_name`
- `wine_food_pairing.recommended_wine_style -> wine_style.style_name`
- `wine_food_pairing.recommended_grape -> grape_variety.grape_name`

## professional wine geography + classification model
- `wine_region` is geography-first and stores `country`, `region`, `subregion`, and `geo_level`.
- `wine_region.classification_id -> wine_classification.classification_id` links each geography row to a governed legal/quality tier.
- `wine_region.classification_system` + `wine_region.quality_tier` are denormalized text mirrors for fast filtering/search UX.
- `wine_classification` stores classification taxonomy with hierarchy (`tier_rank`, `parent_id`) for analytics and governance.

## recommendation matrix usage
- use `wine_style`, `grape_variety`, `wine_flavor_profile`, and `wine_food_pairing` for wine suggestion matrix generation.
- use `spirit_type`, `whisky_style`, and `spirit_flavor_profile` for spirits sales-assist and cross-sell rules.
- use `taste_vector`, `pairing_vector`, and `recommendation_score` in `product_master` as model-ready features.
