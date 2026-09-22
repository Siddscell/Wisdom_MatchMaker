-- Item photos: the image lives in Supabase Storage; the row keeps its public URL and the
-- CLIP embeddings used for visual matching (512 dims, clip-ViT-B-32).
alter table requirements
  add column image_url           text,
  add column image_embedding     vector(512),  -- CLIP image embedding (null without a photo)
  add column clip_text_embedding vector(512);  -- CLIP text embedding, for photo <-> text matching
alter table offerings
  add column image_url           text,
  add column image_embedding     vector(512),
  add column clip_text_embedding vector(512);

-- Public bucket for listing photos (Supabase only). Signed-in users may upload only into a
-- folder named after their own user id; anyone can view the images.
do $$
begin
  if exists (select 1 from information_schema.tables
             where table_schema = 'storage' and table_name = 'buckets') then
    insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
    values ('listing-images', 'listing-images', true, 5242880,
            array['image/jpeg', 'image/png', 'image/webp'])
    on conflict (id) do nothing;
    execute $p$create policy "upload own listing images" on storage.objects
             for insert to authenticated
             with check (bucket_id = 'listing-images'
                         and (storage.foldername(name))[1] = auth.uid()::text)$p$;
  end if;
end $$;
