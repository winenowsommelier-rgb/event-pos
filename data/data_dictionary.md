# data dictionary

## product_master
- `product_id`: numeric primary key.
- `sku`: unique SKU string for inventory and order integration.
- `product_name`: normalized product display name.
- `brand`: commerce brand (`wine_now` or `liq9`).
- `producer`: winery, distillery, brewery, or accessory maker.
- `product_type`: specific catalog class (`wine`, `whisky`, `gin`, `beer`, `glassware`, etc.).
- `category`: top-level group used by navigation and faceting.
- `sub_category`: merchandising subgroup used by landing pages and bundles.
- `country`, `region`, `subregion`, `appellation`: marketable place hierarchy.
- `grape_variety`: wine grape foreign key to `grape_variety`.
- `grape_class`: broad color/category class for segmentation.
- `wine_style`: foreign key to `wine_style` for wine products.
- `spirit_style`: foreign key to `whisky_style` for whisky/cognac style segmentation.
- `flavor_profile`: canonical flavor tag used in recommendation matching.
- `food_pairing`: foreign key to `wine_food_pairing` for meal suggestions.
- `alcohol`: ABV percentage.
- `vintage`: production year (mainly wine).
- `bottle_size`: sales unit size.
- `price_segment`: pricing tier (`entry`, `premium`, `super_premium`, `luxury`).
- `critic_score`: normalized quality score.
- `critic_source`: review source.
- `taste_vector`: compact model feature vector for taste similarity.
- `pairing_vector`: compact model feature vector for food-pairing similarity.
- `recommendation_score`: ranking confidence signal.

## wine dimensions
- `wine_type`: broad wine taxonomy labels.
- `grape_variety`: major grape records with structure and sensory dimensions.
- `wine_region`: geography table with `geo_level` and mapped professional classification (`classification_id`).
- `wine_classification`: professional legal/quality taxonomy table using `classification_system`, `tier_code`, `tier_name`, `tier_rank`, and `parent_id`.
- `wine_style`: core style templates for faceting and recommendation defaults.
- `wine_flavor_profile`: standardized flavor tags and flavor categories.
- `wine_food_pairing`: cuisine-to-style pairing matrix with rationale.

## spirits dimensions
- `spirit_type`: spirit class and base ingredient taxonomy.
- `whisky_style`: whisky family styles with region and ABV ranges.
- `spirit_flavor_profile`: normalized spirit flavor vocabulary.
