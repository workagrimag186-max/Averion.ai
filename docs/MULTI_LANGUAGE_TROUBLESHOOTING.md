# Multi-Language Feature - Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: "notFound() is not allowed to use in root layout"

**Cause:** Next.js 15+ with next-intl doesn't allow `notFound()` in root layout when using async server components.

**Solution:** ✅ Fixed
- Updated `apps/web/i18n.ts` to handle undefined locale with default fallback
- Simplified `apps/web/app/layout.tsx` to not use locale params
- Changed middleware `localePrefix` to "never" to avoid URL-based locale routing

### Issue 2: Frontend not restarting after changes

**Solution:** Restart the Next.js development server:
```bash
cd apps/web
npm run dev
```

### Issue 3: Language not persisting

**Check:**
1. Database migration ran successfully
2. User profile has `language_preference` column
3. Account page saves language correctly

**Verify:**
```sql
SELECT user_id, email, language_preference FROM users;
```

### Issue 4: Chatbot still responds in English

**Check:**
1. Chat component fetches language preference (check browser console)
2. Chat request includes language parameter (check Network tab)
3. Backend receives language parameter (check API logs)

**Debug:**
```javascript
// In chat-workspace.tsx, add console.log
console.log("User language:", userLanguage);
console.log("Sending chat with language:", { question, language: userLanguage });
```

### Issue 5: Voice transcription not working in selected language

**Check:**
1. Language parameter passed to `transcribeAudio()`
2. Backend receives language query parameter
3. Whisper API called with correct language

**Debug:**
```python
# In apps/api/app/api/transcription.py
print(f"Transcription language: {language}")
```

### Issue 6: TypeScript errors in components

**Solution:** Install dependencies:
```bash
cd apps/web
npm install
```

### Issue 7: Translation keys not found

**Check:**
1. Translation files exist in `apps/web/messages/`
2. Keys match between files
3. Component uses correct translation namespace

**Example:**
```typescript
const t = useTranslations("navigation"); // namespace
return <span>{t("chat")}</span>; // key
```

## Testing Checklist

### Backend Testing
- [ ] Database migration successful
- [ ] Profile endpoint returns language_preference
- [ ] Profile update saves language_preference
- [ ] Chat endpoint accepts language parameter
- [ ] Transcription endpoint accepts language parameter
- [ ] LLM prompt includes language instruction

### Frontend Testing
- [ ] Account page shows language dropdown
- [ ] Language selection saves successfully
- [ ] Language persists after page refresh
- [ ] Chat component fetches language preference
- [ ] Chat requests include language parameter
- [ ] Voice transcription uses language parameter

### Integration Testing
- [ ] User selects Hindi → Chat responds in Hindi
- [ ] User selects Spanish → Chat responds in Spanish
- [ ] Voice input transcribes in selected language
- [ ] Citations still work correctly
- [ ] RAG retrieval unchanged
- [ ] Security filters still active

## Quick Fixes

### Reset to English
```sql
UPDATE users SET language_preference = 'en' WHERE user_id = 'YOUR_USER_ID';
```

### Clear browser cache
```javascript
// In browser console
localStorage.clear();
sessionStorage.clear();
location.reload();
```

### Restart all services
```bash
# Terminal 1: Backend
cd apps/api
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd apps/web
npm run dev
```

## Verification Commands

### Check database
```sql
-- Verify column exists
\d users

-- Check user language preferences
SELECT user_id, email, language_preference FROM users;
```

### Test API endpoints
```bash
# Get profile
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer YOUR_TOKEN"

# Update language
curl -X PATCH http://localhost:8000/users/me \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "job_title": "Engineer", "language_preference": "hi"}'

# Test chat
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": null, "question": "What is Skybrush?", "language": "hi"}'
```

## Support

If issues persist:
1. Check browser console for errors
2. Check API logs for errors
3. Verify all files were modified correctly
4. Ensure dependencies are installed
5. Restart both frontend and backend servers

## Files to Check

If something isn't working, verify these files were modified:

**Backend:**
- `apps/api/app/schemas/users.py`
- `apps/api/app/db/users.py`
- `apps/api/app/api/users.py`
- `apps/api/app/schemas/chat.py`
- `apps/api/app/ai/prompt_builder.py`
- `apps/api/app/api/chat.py`
- `apps/api/app/ai/transcription_service.py`
- `apps/api/app/api/transcription.py`

**Frontend:**
- `apps/web/i18n.ts`
- `apps/web/next.config.ts`
- `apps/web/middleware.ts`
- `apps/web/app/layout.tsx`
- `apps/web/lib/api.ts`
- `apps/web/components/chat-workspace.tsx`
- `apps/web/components/account-summary.tsx`