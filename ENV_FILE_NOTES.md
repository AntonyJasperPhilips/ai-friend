# .env File Configuration Notes

## AWS_SECRET_ACCESS_KEY Format

**Yes, AWS_SECRET_ACCESS_KEY can contain `#` symbol!**

It's a 40-character alphanumeric string that can contain special characters including `#`.

---

## Correct Format

```env
# ✅ Correct - # in the middle is fine
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/b#xRfiCYEXAMPLEKEY

# ✅ Also correct - # at the end
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY#

# ✅ Also correct - no #
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

---

## Common Issues

### ❌ Problem: Comment After Value

```env
# ❌ WRONG - everything after # is treated as a comment
AWS_SECRET_ACCESS_KEY=your_key # This is my AWS key

# Result: Key value is "your_key " (with trailing space, then comment ignored)
```

### ✅ Solution: No Comments on Same Line

```env
# ✅ CORRECT - put comment on separate line
AWS_SECRET_ACCESS_KEY=your_key
# This is my AWS key
```

---

## .env File Rules

1. **No spaces around `=`**: `KEY=value` not `KEY = value`
2. **No quotes needed**: `KEY=value` not `KEY="value"` (unless value has spaces)
3. **Comments start with `#`**: On separate lines only
4. **No trailing spaces**: `KEY=value` not `KEY=value `
5. **Special characters OK**: `#` `$` `%` etc. are fine

---

## Example .env File

```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE

# Secret key can contain # symbol
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/b#xRfiCYEXAMPLEKEY

S3_BUCKET=edu-rag-images

# OpenAI
OPENAI_API_KEY=sk-proj-your-key-here

# Pinecone
PINECONE_API_KEY=your-key-here
```

---

## Troubleshooting

**If you have issues with `#` in secret key:**

1. ✅ Keep it on the same line as the key name
2. ✅ Don't add comments after it
3. ✅ No spaces before or after the `=`
4. ✅ Restart your app after changing .env

---

**In summary:** `#` is perfectly valid in AWS_SECRET_ACCESS_KEY, just don't use it to start a comment on the same line!


