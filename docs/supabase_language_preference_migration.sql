-- Migration: Add language preference support to users table
-- Purpose: Enable multi-language UI, chatbot, and voice support
-- Date: 2026-06-05

-- Add language preference column to users table
-- Default to 'en' (English) for existing users
-- Supported languages: en, hi, es, fr, de, ja
alter table users
add column language_preference text not null default 'en';

-- Add constraint to ensure only valid language codes are stored
alter table users
add constraint users_language_preference_check
check (language_preference in ('en', 'hi', 'es', 'fr', 'de', 'ja'));

-- Add comment for documentation
comment on column users.language_preference is 'User preferred language for UI, chatbot responses, and voice input. Supported: en (English), hi (Hindi), es (Spanish), fr (French), de (German), ja (Japanese)';

-- Create index for potential language-based queries (optional, for analytics)
create index users_language_preference_idx on users (language_preference);

-- Made with Bob
