# API Documentation

## AutoAttendance REST API

AutoAttendance provides a comprehensive REST API for programmatic access to the attendance system.

### Base URL

```
http://localhost:8000
```

### Authentication

Currently, the API uses no authentication. In production, implement JWT or API key authentication.

---

## Endpoints

### Health Check

#### `GET /health`

Check API server status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

### Attendance

#### `POST /attendance/mark`

Mark attendance for a person with face data.

**Request Body:**
```json
{
  "face_embedding": [0.1, 0.2, ..., 0.5],
  "timestamp": "2026-05-09T10:00:00Z"
}
```

**Response (Success):**
```json
{
  "success": true,
  "person_id": 1,
  "name": "John Doe",
  "timestamp": "2026-05-09T10:00:00Z",
  "confidence": 0.95
}
```

**Response (Unknown Person):**
```json
{
  "success": false,
  "error": "unknown_person",
  "confidence": 0.45
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid request
- `500` - Server error

---

#### `GET /attendance/records`

Get attendance records with optional filtering.

**Query Parameters:**
- `date` (string, optional): Filter by date (YYYY-MM-DD)
- `person_id` (integer, optional): Filter by person
- `limit` (integer, optional, default=100): Max records to return
- `offset` (integer, optional, default=0): Pagination offset

**Example Request:**
```
GET /attendance/records?date=2026-05-09&limit=50
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "person_id": 1,
      "name": "John Doe",
      "timestamp": "2026-05-09T09:00:00Z",
      "confidence": 0.98
    },
    {
      "id": 2,
      "person_id": 2,
      "name": "Jane Smith",
      "timestamp": "2026-05-09T09:15:00Z",
      "confidence": 0.96
    }
  ],
  "total": 2
}
```

---

#### `GET /attendance/summary`

Get attendance summary statistics.

**Query Parameters:**
- `date_from` (string, optional): Start date (YYYY-MM-DD)
- `date_to` (string, optional): End date (YYYY-MM-DD)

**Response:**
```json
{
  "success": true,
  "data": {
    "total_attendees": 45,
    "present_today": 42,
    "absent_today": 3,
    "average_arrival_time": "09:15",
    "latest_arrival": "10:30"
  }
}
```

---

### People Management

#### `GET /people`

List all registered people.

**Query Parameters:**
- `limit` (integer, optional, default=100): Max records
- `offset` (integer, optional, default=0): Pagination offset

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "embedding_count": 85,
      "registered_date": "2026-01-15"
    }
  ],
  "total": 1
}
```

---

#### `POST /people`

Register a new person.

**Request Body:**
```json
{
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "metadata": {
    "department": "Engineering",
    "role": "Developer"
  }
}
```

**Response:**
```json
{
  "success": true,
  "id": 3,
  "name": "Alice Johnson",
  "message": "Person registered successfully"
}
```

---

#### `GET /people/{id}`

Get person details.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "embedding_count": 85,
    "registered_date": "2026-01-15",
    "total_attendance": 120,
    "last_seen": "2026-05-09T16:30:00Z"
  }
}
```

---

#### `PUT /people/{id}`

Update person information.

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "metadata": {
    "department": "Marketing"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Person updated successfully"
}
```

---

#### `DELETE /people/{id}`

Delete a person and their records.

**Response:**
```json
{
  "success": true,
  "message": "Person deleted successfully"
}
```

---

### Training Data

#### `POST /training/collect`

Start face collection for a person.

**Request Body:**
```json
{
  "person_id": 1,
  "target_samples": 100
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "sess_123",
  "message": "Face collection started"
}
```

---

#### `GET /training/status/{session_id}`

Get collection status.

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "sess_123",
    "person_id": 1,
    "collected_samples": 45,
    "target_samples": 100,
    "progress": 45,
    "status": "in_progress"
  }
}
```

---

#### `POST /training/train`

Trigger model retraining.

**Response:**
```json
{
  "success": true,
  "message": "Training started",
  "job_id": "job_456"
}
```

---

### Reports

#### `GET /reports/daily`

Get daily attendance report.

**Query Parameters:**
- `date` (string, required): Date (YYYY-MM-DD)

**Response:**
```json
{
  "success": true,
  "data": {
    "date": "2026-05-09",
    "total_students": 45,
    "present": 42,
    "absent": 3,
    "details": [
      {"id": 1, "name": "John Doe", "status": "present", "time": "09:00"},
      {"id": 2, "name": "Jane Smith", "status": "absent", "time": null}
    ]
  }
}
```

---

#### `GET /reports/monthly`

Get monthly statistics.

**Query Parameters:**
- `year` (integer, required)
- `month` (integer, required)

**Response:**
```json
{
  "success": true,
  "data": {
    "month": "May 2026",
    "total_days": 21,
    "average_attendance_rate": 92.5,
    "details": [...]
  }
}
```

---

#### `GET /reports/export`

Export attendance data.

**Query Parameters:**
- `format` (string): csv or excel
- `date_from` (string): Start date
- `date_to` (string): End date

**Response:** File download (CSV or Excel format)

---

### System

#### `GET /system/stats`

Get system statistics.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_people": 50,
    "total_embeddings": 5000,
    "total_attendance_records": 2500,
    "database_size_mb": 25.5,
    "uptime_seconds": 86400
  }
}
```

---

#### `POST /system/backup`

Create database backup.

**Response:**
```json
{
  "success": true,
  "backup_file": "attendance_backup_20260509.zip",
  "size_mb": 15.2,
  "timestamp": "2026-05-09T10:00:00Z"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "success": false,
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {}
}
```

### Common Error Codes

| Code | Meaning | Status |
|------|---------|--------|
| `invalid_request` | Request parameters are invalid | 400 |
| `not_found` | Resource not found | 404 |
| `duplicate_entry` | Entry already exists | 409 |
| `spoof_detected` | Face spoofing detected | 403 |
| `internal_error` | Server error | 500 |

---

## Rate Limiting

- API rate limit: 1000 requests/hour per IP
- Batch size limit: 100 records per request

---

## WebSocket Events

Real-time face detection events via WebSocket:

```
ws://localhost:8000/ws/detection
```

**Event Format:**
```json
{
  "type": "face_detected",
  "timestamp": "2026-05-09T10:00:00Z",
  "faces": [
    {
      "id": 1,
      "name": "John Doe",
      "confidence": 0.98,
      "bbox": [100, 100, 150, 150]
    }
  ]
}
```

---

## Example Client Code

### Python
```python
import requests

BASE_URL = "http://localhost:8000"

# Get attendance records
response = requests.get(
    f"{BASE_URL}/attendance/records",
    params={"date": "2026-05-09"}
)
data = response.json()
print(data)
```

### JavaScript
```javascript
const baseUrl = 'http://localhost:8000';

// Get people list
fetch(`${baseUrl}/people`)
  .then(response => response.json())
  .then(data => console.log(data));
```

### cURL
```bash
# Mark attendance
curl -X POST http://localhost:8000/attendance/mark \
  -H "Content-Type: application/json" \
  -d '{
    "face_embedding": [0.1, 0.2, ...],
    "timestamp": "2026-05-09T10:00:00Z"
  }'
```

---

## Security Considerations

1. **HTTPS**: Use HTTPS in production
2. **Authentication**: Implement API key or JWT authentication
3. **Rate Limiting**: Enforce rate limits
4. **Input Validation**: All inputs are validated
5. **CORS**: Configure CORS appropriately
6. **Logging**: All API calls are logged

---

## Support

For API issues, please visit: https://github.com/Mahfujul-01726/AutoAttendance/issues
