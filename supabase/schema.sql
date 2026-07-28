-- GTA Running Deals — Supabase schema
-- Run this in the Supabase SQL editor to initialize the database.

-- ============================================================
-- Tables
-- ============================================================

create table if not exists retailers (
  id uuid primary key default gen_random_uuid(),
  name text not null unique,
  website text not null,
  lat numeric,
  lng numeric,
  city text default 'Toronto',
  created_at timestamptz default now()
);

create table if not exists products (
  id uuid primary key default gen_random_uuid(),
  retailer_id uuid references retailers(id) on delete cascade,
  name text not null,
  brand text,
  category text default 'road' check (category in ('road', 'trail', 'track')),
  url text not null,
  image_url text,
  first_seen timestamptz default now(),
  unique(retailer_id, url)
);

create table if not exists price_history (
  id uuid primary key default gen_random_uuid(),
  product_id uuid references products(id) on delete cascade,
  price numeric not null,
  sale_price numeric,
  in_stock boolean default true,
  scraped_at timestamptz default now()
);

create table if not exists watchlist (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references auth.users(id) on delete cascade,
  product_id uuid references products(id) on delete cascade,
  target_price numeric,
  created_at timestamptz default now(),
  unique(user_id, product_id)
);

-- ============================================================
-- Indexes
-- ============================================================

create index if not exists idx_price_history_product_scraped
  on price_history(product_id, scraped_at desc);

create index if not exists idx_price_history_scraped_at
  on price_history(scraped_at desc);

create index if not exists idx_products_retailer
  on products(retailer_id);

create index if not exists idx_products_brand
  on products(brand);

create index if not exists idx_watchlist_user
  on watchlist(user_id);

-- ============================================================
-- Row Level Security
-- ============================================================

alter table watchlist enable row level security;

do $$ begin
  create policy "Users can read their own watchlist"
    on watchlist for select using (auth.uid() = user_id);
exception when duplicate_object then null;
end $$;

do $$ begin
  create policy "Users can insert into their own watchlist"
    on watchlist for insert with check (auth.uid() = user_id);
exception when duplicate_object then null;
end $$;

do $$ begin
  create policy "Users can delete their own watchlist items"
    on watchlist for delete using (auth.uid() = user_id);
exception when duplicate_object then null;
end $$;

do $$ begin
  create policy "Users can update their own watchlist items"
    on watchlist for update using (auth.uid() = user_id);
exception when duplicate_object then null;
end $$;

-- Public read on products, retailers, price_history (no PII)
alter table products enable row level security;
alter table retailers enable row level security;
alter table price_history enable row level security;

do $$ begin
  create policy "Public read products" on products for select using (true);
exception when duplicate_object then null;
end $$;

do $$ begin
  create policy "Public read retailers" on retailers for select using (true);
exception when duplicate_object then null;
end $$;

do $$ begin
  create policy "Public read price_history" on price_history for select using (true);
exception when duplicate_object then null;
end $$;

-- Service role can write everything (used by scrapers only)
-- No additional policies needed — service role bypasses RLS.

-- ============================================================
-- RPC: get_deals — price drops in last N hours
-- ============================================================

create or replace function get_deals(
  p_since timestamptz,
  p_brand text default null,
  p_retailer_id uuid default null,
  p_category text default null,
  p_limit int default 50,
  p_offset int default 0
)
returns table(
  product_id uuid,
  name text,
  brand text,
  category text,
  url text,
  image_url text,
  retailer_id uuid,
  retailer_name text,
  current_price numeric,
  previous_price numeric,
  drop_percent numeric
)
language sql
stable
as $$
  with ranked as (
    select
      ph.product_id,
      ph.price,
      ph.sale_price,
      ph.scraped_at,
      row_number() over (partition by ph.product_id order by ph.scraped_at desc) as rn
    from price_history ph
    where ph.scraped_at >= p_since - interval '2 days'
  ),
  latest as (
    select product_id,
      coalesce(sale_price, price) as eff_price,
      scraped_at
    from ranked where rn = 1
  ),
  previous as (
    select product_id,
      coalesce(sale_price, price) as eff_price
    from ranked where rn = 2
  ),
  drops as (
    select
      l.product_id,
      l.eff_price as current_price,
      p.eff_price as previous_price,
      round(((p.eff_price - l.eff_price) / p.eff_price) * 100, 1) as drop_percent
    from latest l
    join previous p on l.product_id = p.product_id
    where l.eff_price < p.eff_price
      and l.scraped_at >= p_since
  )
  select
    pr.id as product_id,
    pr.name,
    pr.brand,
    pr.category,
    pr.url,
    pr.image_url,
    r.id as retailer_id,
    r.name as retailer_name,
    d.current_price,
    d.previous_price,
    d.drop_percent
  from drops d
  join products pr on pr.id = d.product_id
  join retailers r on r.id = pr.retailer_id
  where
    (p_brand is null or pr.brand ilike '%' || p_brand || '%')
    and (p_retailer_id is null or r.id = p_retailer_id)
    and (p_category is null or pr.category = p_category)
  order by d.drop_percent desc
  limit p_limit
  offset p_offset;
$$;

-- ============================================================
-- Seed: retailers
-- ============================================================

insert into retailers (name, website, lat, lng, city) values
  ('Sport Chek',         'https://www.sportchek.ca',           43.6534, -79.3803, 'Toronto'),
  ('Sporting Life',      'https://www.sportinglife.ca',        43.7116, -79.3975, 'Toronto'),
  ('Running Room',       'https://www.runningroom.com',        43.7108, -79.3975, 'Toronto'),
  ('BlackToe Running',   'https://www.blacktoerunning.com',    43.6444, -79.4028, 'Toronto'),
  ('The Runners Shop',   'https://www.therunnersshop.com',     43.6666, -79.4028, 'Toronto'),
  ('Running Free',       'https://www.runningfree.com',        43.8254, -79.3378, 'Markham'),
  ('SVP Sports',         'https://www.svpsports.ca',           43.7099, -79.4516, 'Toronto'),
  ('MEC',                'https://www.mec.ca',                 43.6503, -79.3924, 'Toronto'),
  ('New Balance',        'https://www.newbalance.com/en-CA',   43.6483, -79.3833, 'Toronto'),
  ('HOKA',               'https://www.hoka.com/en-ca',         43.6532, -79.3832, 'Toronto'),
  ('Nike CA',            'https://www.nike.com/ca',            43.6532, -79.3832, 'Toronto'),
  ('Culture Athletics',  'https://www.cultureathletics.com',   43.6614, -79.3339, 'Toronto')
on conflict (name) do update set
  website = excluded.website,
  lat     = excluded.lat,
  lng     = excluded.lng,
  city    = excluded.city;
