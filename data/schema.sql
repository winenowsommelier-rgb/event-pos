-- product intelligence schema (expanded taxonomy)

create table wine_type (
  wine_type_id integer primary key,
  wine_type text not null unique,
  description text not null
);

create table grape_variety (
  grape_id integer primary key,
  grape_name text not null unique,
  grape_class text,
  origin_country text,
  primary_regions text,
  typical_style text,
  body text,
  acidity text,
  tannin text
);

create table wine_region (
  region_id integer primary key,
  country text not null,
  region text not null,
  subregion text,
  classification_level text,
  sub_classification text
);

create table wine_classification (
  classification_id integer primary key,
  country text not null,
  classification_level text not null,
  sub_classification text,
  description text,
  parent_id integer
);

create table wine_style (
  style_id integer primary key,
  style_name text not null unique,
  body text,
  acidity text,
  tannin text,
  sweetness text,
  typical_grapes text
);

create table wine_flavor_profile (
  flavor_id integer primary key,
  flavor_tag text not null unique,
  flavor_category text not null
);

create table wine_food_pairing (
  pairing_id integer primary key,
  food_name text not null unique,
  food_category text,
  recommended_wine_style text references wine_style(style_name),
  recommended_grape text references grape_variety(grape_name),
  pairing_reason text
);

create table spirit_type (
  spirit_type_id integer primary key,
  spirit_type text not null unique,
  base_ingredient text,
  origin text
);

create table whisky_style (
  style_id integer primary key,
  whisky_style text not null unique,
  country text,
  region text,
  flavor_profile text,
  typical_abv text
);

create table spirit_flavor_profile (
  flavor_id integer primary key,
  flavor_tag text not null unique,
  category text,
  typical_spirits text
);

create table product_master (
  product_id integer primary key,
  sku text not null unique,
  product_name text not null,
  brand text not null,
  producer text,
  product_type text not null,
  category text,
  sub_category text,
  country text,
  region text,
  subregion text,
  appellation text,
  grape_variety text references grape_variety(grape_name),
  grape_class text,
  wine_style text references wine_style(style_name),
  spirit_style text references whisky_style(whisky_style),
  flavor_profile text,
  food_pairing text references wine_food_pairing(food_name),
  alcohol numeric(4,1),
  vintage integer,
  bottle_size text,
  price_segment text,
  critic_score integer,
  critic_source text,
  taste_vector text,
  pairing_vector text,
  recommendation_score numeric(4,2),
  constraint ck_product_master_brand check (brand in ('wine_now','liq9')),
  constraint ck_price_segment check (price_segment in ('entry','premium','super_premium','luxury'))
);

create index idx_product_master_region on product_master(region);
create index idx_product_master_country on product_master(country);
create index idx_product_master_grape on product_master(grape_variety);
create index idx_product_master_wine_style on product_master(wine_style);
create index idx_product_master_spirit_style on product_master(spirit_style);
create index idx_product_master_type on product_master(product_type);

create index idx_wine_region_country_region on wine_region(country, region);
