# table relationships

## direct foreign keys
- `product_master.grape_variety -> grape_variety.grape_name`
- `product_master.wine_style -> wine_style.style_name`
- `product_master.spirit_style -> whisky_style.whisky_style`
- `product_master.food_pairing -> wine_food_pairing.food_name`
- `wine_food_pairing.recommended_wine_style -> wine_style.style_name`
- `wine_food_pairing.recommended_grape -> grape_variety.grape_name`

## dimensional usage for recommendations
- `product_master.flavor_profile` aligns with `wine_flavor_profile.flavor_tag` for wine recommendation vectors.
- `product_master.flavor_profile` can also map to `spirit_flavor_profile.flavor_tag` for spirits when product_type is a spirit.
- `product_master.country/region/subregion/appellation` is denormalized for fast search and should match `wine_region` values.

## ecommerce and ai matrix guidance
- use `wine_style`, `grape_variety`, `wine_flavor_profile`, and `wine_food_pairing` for wine suggestion matrix generation.
- use `spirit_type`, `whisky_style`, and `spirit_flavor_profile` for spirits sales-assist and cross-sell rules.
- use `taste_vector`, `pairing_vector`, and `recommendation_score` in `product_master` as model-ready features.
