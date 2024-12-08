
# Supabase SQL Table Documentation

## 0. Users Table (`users`)
- **Managed by Supabase Authentication**.
- **Fields**:
  - `id`: UUID (Primary Key, auto-generated).
  - `email`: String (auto-generated).
  - `created_at`: Timestamp (auto-generated).

---

## 1. User Data Table (`user_data`)
Stores information about users.

```sql
create table user_data (
  id uuid default uuid_generate_v4() primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  first_name text not null,
  last_name text not null,
  email text not null unique,
  created_at timestamp default now(),
  updated_at timestamp default now()
);
```

## 2. Tournaments Table (`tournaments`)
Stores information about tournaments.

```sql
create table tournaments (
  id uuid default uuid_generate_v4() primary key,
  host_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  description text,
  code text not null unique,
  settings jsonb,
  status text default 'pending', -- can be 'pending', 'active', 'completed'
  created_at timestamp default now()
);
```

### Fields:
- `id`: UUID (Primary Key).
- `host_id`: UUID (Foreign Key to `auth.users`).
- `name`: Text (Tournament name).
- `description`: Text (Optional tournament description).
- `code`: Text (Unique tournament code for joining).
- `settings`: JSONB (Stores tournament settings like number of rounds, round time, etc.).
- `status`: Text (`pending`, `active`, `completed`).
- `created_at`: Timestamp.

---

## 3. Participants Table (`participants`)
Tracks which users have joined a tournament.

```sql
create table participants (
  id uuid default uuid_generate_v4() primary key,
  tournament_id uuid not null references tournaments(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  created_at timestamp default now(),
  unique (tournament_id, user_id) -- prevent duplicate entries
);
```

### Fields:
- `id`: UUID (Primary Key).
- `tournament_id`: UUID (Foreign Key to `tournaments`).
- `user_id`: UUID (Foreign Key to `auth.users`).
- `created_at`: Timestamp (When the user joined the tournament).

---


## SQL functions created:
```sql
CREATE OR REPLACE FUNCTION get_tournament_participant_counts()
RETURNS TABLE(tournament_id uuid, participant_count bigint) AS $$
BEGIN
  RETURN QUERY
  SELECT
    participants.tournament_id,
    COUNT(*) AS participant_count
  FROM
    participants
  GROUP BY
    participants.tournament_id;
END;
$$ LANGUAGE plpgsql;
```