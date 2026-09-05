-- Run this in Supabase SQL Editor AFTER schema.sql.
-- Lets us do cosine-similarity search via supabase.rpc(), since the
-- Python client can't express "order by embedding <=> query" directly.

create or replace function match_chunks (
    query_embedding vector(1024),
    match_paper_id uuid default null,   -- optional: restrict search to one paper
    match_count int default 8
)
returns table (
    chunk_id uuid,
    section_id uuid,
    section_title text,
    paper_id uuid,
    chunk_text text,
    similarity float
)
language sql stable
as $$
    select
        c.id as chunk_id,
        s.id as section_id,
        s.title as section_title,
        s.paper_id,
        c.text as chunk_text,
        1 - (c.embedding <=> query_embedding) as similarity
    from chunks c
    join sections s on s.id = c.section_id
    where match_paper_id is null or s.paper_id = match_paper_id
    order by c.embedding <=> query_embedding
    limit match_count;
$$;