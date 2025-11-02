# S3 Configuration Required

## 🎯 Issue

```
Failed to upload image xref=248 to S3: Invalid endpoint: https://s3..amazonaws.com
```

## ✅ Good News

**Your image extraction is working perfectly!**  
- ✅ Images detected (xref=248 is valid)
- ✅ Image data extracted successfully
- ⚠️ Only S3 upload is failing due to missing AWS configuration

## 🔧 Quick Fix

You need to configure AWS S3 credentials in your `.env` file.

### Create `.env` File

In your `app/app/` directory, create a `.env` file with:

```env
# OpenAI
OPENAI_API_KEY=your_openai_key_here

# Pinecone
PINECONE_API_KEY=your_pinecone_key_here
PINECONE_TEXT_INDEX=edu-text-chunks
PINECONE_IMAGE_INDEX=edu-image-chunks

# AWS S3 - FILL THESE IN!
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
S3_BUCKET=your_bucket_name_here

# Optional
OCR_ENABLED=true
ENABLE_IMAGE_CAPTIONS=true
```

### Get AWS Credentials

**If you have AWS account:**
1. Go to https://console.aws.amazon.com/
2. Create S3 bucket
3. Create IAM user with S3 permissions
4. Generate access keys

**If you don't have AWS yet:**
1. Sign up at https://aws.amazon.com/free/
2. Follow AWS_S3_SETUP.md for detailed steps

---

## 📋 What's Working Now

Your system successfully:
- ✅ Detects images in PDF
- ✅ Extracts image data
- ✅ Filters invalid xrefs
- ✅ Generates captions
- ⚠️ Needs S3 config to store

---

## 🚀 After Configuration

Once `.env` is configured:

1. Restart your app
2. Upload PDF again
3. Check logs for: `"Uploaded image {id} to S3"`
4. Images will be stored and searchable!

---

## 💡 Temporarily Skip S3

If you want to test without S3:

The code will:
- ✅ Still detect images
- ✅ Still extract text
- ✅ Still generate chunks
- ⚠️ Skip image upload
- ⚠️ Skip image embeddings in approve

**You can still test the text RAG functionality!**

---

**Fix:** Add AWS credentials to `.env` file. See AWS_S3_SETUP.md for details.

