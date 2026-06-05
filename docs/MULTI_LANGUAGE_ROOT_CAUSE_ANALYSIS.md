# Multi-Language Feature - Root Cause Analysis & Fix

## 🔍 ROOT CAUSE ANALYSIS

### Problem 1: UI Not Changing Language
**Root Cause:** Frontend i18n is NOT integrated
- Translation files exist but are NOT being used
- No NextIntlClientProvider wrapper
- No middleware for locale detection
- Components use hardcoded English strings
- No `useTranslations()` hooks implemented

**Impact:** UI remains in English regardless of language selection

### Problem 2: Chatbot Answers in English
**Root Cause:** Frontend does NOT send language parameter to chat API
- Chat component doesn't read user's language preference
- Chat requests don't include `language` field
- Backend receives no language instruction
- LLM defaults to English

**Impact:** Chatbot always responds in English

### Problem 3: Language Not Enforced
**Root Cause:** No integration between saved preference and active components
- Language saved to database ✓
- But NOT read by chat component
- NOT read by voice component
- NOT used in UI rendering

**Impact:** Language selection has no effect on user experience

## 📊 CURRENT STATE vs EXPECTED STATE

### Current State
```
User selects Hindi → Saved to DB ✓
User speaks Hindi → Transcribed ✓
Chat request → { question: "...", language: "en" } ❌ (hardcoded)
LLM prompt → "You are a helpful AI assistant" ❌ (no language instruction)
Response → English ❌
UI → English ❌
```

### Expected State
```
User selects Hindi → Saved to DB ✓
User speaks Hindi → Transcribed ✓
Chat request → { question: "...", language: "hi" } ✓ (from user profile)
LLM prompt → "Always respond in Hindi" ✓
Response → Hindi ✓
UI → Hindi ✓
```

## 🛠️ REQUIRED FIXES

### Fix 1: Frontend Must Send Language to Chat API
**File:** `apps/web/components/chat-workspace.tsx`
**Change:** Read user's language_preference and include in chat requests

### Fix 2: Frontend Must Send Language to Transcription API
**File:** `apps/web/components/chat-workspace.tsx`
**Change:** Include language parameter in transcription requests

### Fix 3: Integrate i18n into Next.js App
**Files:** 
- `apps/web/next.config.ts` - Add i18n plugin
- `apps/web/middleware.ts` - Add locale detection
- `apps/web/app/layout.tsx` - Add NextIntlClientProvider

### Fix 4: Update All Components to Use Translations
**Files:** All component files
**Change:** Replace hardcoded strings with `useTranslations()` hooks

## 🎯 IMPLEMENTATION PRIORITY

### CRITICAL (Must Fix Now)
1. ✅ Chat component sends language parameter
2. ✅ Voice component sends language parameter
3. ✅ Verify backend receives and uses language

### HIGH (Should Fix Soon)
4. ⚠️ Next.js i18n configuration
5. ⚠️ Root layout with provider
6. ⚠️ Middleware for locale

### MEDIUM (Can Fix Later)
7. 📝 Update all components with translation hooks
8. 📝 Test all UI strings in all languages

## 📝 DETAILED FIX PLAN

### Step 1: Update Chat Component to Send Language
The chat component must:
1. Fetch user profile to get language_preference
2. Include language in every chat request
3. Pass language to transcription API

### Step 2: Verify Backend Prompt Builder
Confirm that `build_rag_prompt()` receives language and adds instruction

### Step 3: Configure Next.js i18n
Add next-intl configuration to Next.js

### Step 4: Update Components
Replace all hardcoded strings with translation hooks

## 🔬 TESTING REQUIREMENTS

### Test Case 1: Hindi Chat
```
1. Select Hindi in Account Settings
2. Go to Chat page
3. Ask: "स्काईब्रश क्या है?"
4. Expected: Hindi response with citations
```

### Test Case 2: Hindi Voice
```
1. Select Hindi in Account Settings
2. Go to Chat page
3. Click voice button
4. Speak: "आप कैसे हैं?"
5. Expected: Hindi transcription + Hindi response
```

### Test Case 3: UI Translation
```
1. Select Hindi in Account Settings
2. Navigate to all pages
3. Expected: All buttons, labels, menus in Hindi
```

## ⚠️ CRITICAL GAPS IDENTIFIED

1. **Chat Component**: Does NOT read user's language preference
2. **Chat Request**: Does NOT include language parameter
3. **Voice Component**: Does NOT send language to transcription
4. **UI Components**: Do NOT use translation hooks
5. **Next.js Config**: Missing i18n setup
6. **Middleware**: Missing locale detection

## 🚀 IMMEDIATE ACTION ITEMS

1. Update `chat-workspace.tsx` to fetch and use language preference
2. Update chat API calls to include language parameter
3. Update transcription API calls to include language parameter
4. Verify backend prompt builder is working correctly
5. Test end-to-end with Hindi

## 📋 FILES THAT NEED MODIFICATION

### Critical (Now)
- `apps/web/components/chat-workspace.tsx` - Add language support
- `apps/web/lib/api.ts` - Update sendChatMessage to accept language

### High Priority (Soon)
- `apps/web/next.config.ts` - Add i18n config
- `apps/web/middleware.ts` - Add locale detection
- `apps/web/app/layout.tsx` - Add provider

### Medium Priority (Later)
- All component files - Add translation hooks

## ✅ WHAT'S ALREADY WORKING

- ✅ Database stores language preference
- ✅ Backend API accepts language parameter
- ✅ Backend prompt builder adds language instruction
- ✅ Backend transcription uses language-specific model
- ✅ Translation files exist for 6 languages
- ✅ Account page saves language preference

## ❌ WHAT'S NOT WORKING

- ❌ Chat component doesn't send language
- ❌ UI doesn't change language
- ❌ Chatbot responds in English (because no language sent)
- ❌ No integration between saved preference and active components

## 🎯 SUCCESS CRITERIA

After fixes:
1. User selects Hindi → UI becomes Hindi
2. User asks question → Chatbot responds in Hindi
3. User speaks Hindi → Transcribed and answered in Hindi
4. All pages respect selected language
5. Language persists across sessions
6. RAG pipeline unchanged

---

**Status**: Root cause identified, fixes in progress
**Next**: Implement critical fixes to chat component