# API Endpoints Count

## ✅ Total: **10 Endpoints**

### Breakdown by Category

#### Health (1)
1. `GET /health`

#### Book Content Ingestion (4)
2. `POST /ingest/unit` - Upload & preview unit
3. `POST /ingest/approve` - Store unit in Pinecone
4. `PUT /ingest/unit/{unitId}` - Update unit
5. `DELETE /ingest/unit/{unitId}` - Delete unit

#### Teacher Notes (3)
6. `POST /ingest/teacher-notes/pdf` - Upload teacher notes PDF
7. `POST /ingest/teacher-notes/text` - Upload teacher notes text
8. `POST /ingest/teacher-notes/approve` - Store teacher notes

#### Query (1)
9. `POST /qa/query` - Ask questions & get AI answers

#### Admin (1)
10. `GET /ingest/unit/{unit_id}/images` - Admin images endpoint

---

## Summary

| Category | Count |
|----------|-------|
| Health | 1 |
| Book Content | 4 |
| Teacher Notes | 3 |
| Query | 1 |
| Admin | 1 |
| **TOTAL** | **10** |

---

## Documentation

- Full details: See `API_ENDPOINTS.md`
- Swagger UI: http://localhost:8080/docs

