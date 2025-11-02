# AWS S3 Configuration Guide

## ✅ Image Uploads Require S3

Your image extraction **works correctly** (detected xref=248), but uploading to S3 requires proper AWS configuration.

---

## 🔧 Configure AWS S3

### Step 1: Create `.env` File

Create a `.env` file in your project root with:

```env
# AWS S3 Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
S3_BUCKET=edu-rag-images

# Other required configs...
OPENAI_API_KEY=sk-...
PINECONE_API_KEY=...
```

### Step 2: Get AWS Credentials

**Option A: AWS Account (Recommended)**
1. Sign up at https://aws.amazon.com/
2. Create an IAM user with S3 permissions
3. Generate access keys
4. Create an S3 bucket

**Option B: Test Without S3 (Skip Images)**
- Images won't upload
- Text extraction still works
- Embeddings stored in Pinecone
- Images skipped in student queries

**Option C: Local Storage (Temporary)**
- Store images locally for testing
- Will need to implement alternative storage

---

## 🪣 Create S3 Bucket

### Via AWS Console:
1. Go to S3 in AWS Console
2. Click "Create bucket"
3. Name: `edu-rag-images` (or your choice)
4. Region: `us-east-1` (or your choice)
5. Uncheck "Block all public access" (or configure properly)
6. Click "Create bucket"

### Via AWS CLI:
```bash
aws s3 mb s3://edu-rag-images --region us-east-1
aws s3api put-bucket-cors \
  --bucket edu-rag-images \
  --cors-configuration file://cors.json
```

---

## 🔑 IAM Permissions

Your IAM user needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::edu-rag-images/*"
    }
  ]
}
```

---

## ✅ Verify Configuration

After setting `.env`, restart your app and try uploading again.

**You should see:**
```
INFO - Uploaded image {id} to S3: books/1/chapters/1/units/1/images/{id}.png
```

**Not:**
```
ERROR - Failed to upload image xref=248 to S3: Invalid endpoint
```

---

## 🔍 Common Issues

### Issue: "Invalid endpoint: https://s3..amazonaws.com"
**Cause:** AWS_REGION is empty or invalid  
**Fix:** Set `AWS_REGION=us-east-1` in `.env`

### Issue: "Access Denied"
**Cause:** Invalid credentials or insufficient permissions  
**Fix:** Check AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and IAM permissions

### Issue: "Bucket does not exist"
**Cause:** S3_BUCKET name is wrong or bucket not created  
**Fix:** Create bucket in AWS Console first

---

## 💡 Alternative: Test Without S3

If you can't set up S3 right now:

1. Images will be detected ✅
2. Images won't upload ⚠️
3. Preview will work ✅
4. Approval will skip images ⚠️
5. QA won't return images ⚠️

**You can still test the PDF extraction and text RAG functionality!**

---

## 📋 Quick Checklist

- [ ] Created `.env` file
- [ ] Set AWS_REGION
- [ ] Set AWS_ACCESS_KEY_ID
- [ ] Set AWS_SECRET_ACCESS_KEY
- [ ] Set S3_BUCKET
- [ ] Created S3 bucket in AWS
- [ ] Configured IAM permissions
- [ ] Restarted app
- [ ] Tried uploading PDF
- [ ] Checked logs for errors

---

## 🚀 Ready to Test

Once `.env` is configured, run:
```bash
python -m uvicorn app.app.main:app --host 0.0.0.0 --port 8080 --reload
```

Upload your PDF and check logs!

