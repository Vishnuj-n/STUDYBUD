-- Queries for inspecting the StudyBud database (file_hashes.db)

-- View all processed files
-- This shows the hash, original filename, and when it was first added.
SELECT * FROM files;

-- View all unique videos stored in the database
-- This shows every unique video URL, its title, and the concept it was originally found for.
SELECT * FROM videos;

-- View the links between files and videos
-- This table shows which videos are associated with which files.
SELECT * FROM file_video_links;

-- Get all video details for a specific file hash
-- Replace 'YOUR_FILE_HASH_HERE' with an actual hash from the 'files' table.
/*
SELECT
    f.filename,
    v.concept,
    v.title,
    v.url
FROM files f
JOIN file_video_links fvl ON f.hash = fvl.file_hash
JOIN videos v ON fvl.video_id = v.id
WHERE f.hash = 'YOUR_FILE_HASH_HERE';
*/
