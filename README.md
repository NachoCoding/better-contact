# BetterContact Connector for StackSync Workflows

A production-ready connector that integrates BetterContact's lead enrichment API with StackSync Workflows. This connector enables you to enrich leads with email addresses and phone numbers using BetterContact's data enrichment service.

## 🚀 Features

- **Three Powerful Modules:**
  - **Enrich Lead** - Submit a single lead for asynchronous enrichment
  - **Get Enrichment Results** - Retrieve enrichment results using a request ID
  - **Enrich Lead (Sync)** - All-in-one synchronous enrichment with automatic polling
  
- **Smart Validation Logic** (Clay-style):
  - Person names required only when LinkedIn URL is not provided
  - Company name required only when company domain is not provided
  
- **Robust Error Handling:**
  - Clear, actionable error messages
  - Timeout handling with request IDs for manual checking
  - Network error recovery
  - API authentication validation

- **Production Features:**
  - Progressive polling with smart delays
  - Comprehensive request validation
  - Support for special characters in names
  - Docker containerization for easy deployment

## 📋 Prerequisites

- Docker installed on your system
- Python 3.10 or higher
- A BetterContact API key
- ngrok for local development (optional)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/NachoCoding/better-contact.git
   cd better-contact
   ```

2. **Create a `.env` file with your API key:**
   ```bash
   API_TESTING_KEY=your_bettercontact_api_key_here
   ```

3. **Build the Docker image:**
   ```bash
   docker build -t bettercontact-connector .
   ```

4. **Run the connector:**
   ```bash
   docker run -d --name bettercontact-connector -p 2003:8080 bettercontact-connector
   ```

## 🔧 Configuration

### App Configuration (`app_config.yaml`)

```yaml
app_settings:
  app_type: "bettercontact"
  app_name: "BetterContact"
  app_icon_svg_url: "https://asset.brandfetch.io/id9Bpy_H9O/id4UqT7J5-.svg"
  app_description: "BetterContact API Integration"
  routes_directory: "src/modules"
```

### Local Development Settings

The connector runs on port 2003 (mapped to internal port 8080) by default. You can modify this in the Docker run command if needed.

## 📚 Module Documentation

### 1. Enrich Lead Module

**Purpose:** Submit a single lead for asynchronous enrichment.

**Endpoint:** `/enrich_leads/v1/execute`

**Input Fields:**
- `connection` (required): BetterContact API connection
- `first_name` (conditional): Required if LinkedIn URL not provided
- `last_name` (conditional): Required if LinkedIn URL not provided
- `linkedin_url` (optional): LinkedIn profile URL (alternative to providing names)
- `company` (conditional): Required if company domain not provided
- `company_domain` (optional): Company domain (alternative to company name)
- `enrich_email_address` (boolean): Whether to enrich email (default: true)
- `enrich_phone_number` (boolean): Whether to enrich phone (default: true)

**Example Request:**
```json
{
  "data": {
    "first_name": "John",
    "last_name": "Doe",
    "company": "Acme Corp",
    "enrich_email_address": true,
    "enrich_phone_number": true
  }
}
```

**Example Response:**
```json
{
  "data": {
    "request_id": "e66d7d067cd7c84582dc",
    "status": "submitted",
    "lead": {
      "first_name": "John",
      "last_name": "Doe",
      "company": "Acme Corp"
    }
  },
  "metadata": {
    "api_response": {
      "success": true,
      "id": "e66d7d067cd7c84582dc",
      "message": "Processing. Once done, data will be pushed to your webhook."
    }
  }
}
```

### 2. Get Enrichment Results Module

**Purpose:** Retrieve the results of a previously submitted enrichment request.

**Endpoint:** `/get_enrichment_results/v1/execute`

**Input Fields:**
- `connection` (required): BetterContact API connection
- `request_id` (required): The request ID from the Enrich Lead module

**Example Request:**
```json
{
  "data": {
    "request_id": "e66d7d067cd7c84582dc"
  }
}
```

**Example Response (Still Processing):**
```json
{
  "data": {
    "status": "processing",
    "message": "Enrichment is still in progress"
  },
  "metadata": {
    "status": "processing"
  }
}
```

**Example Response (Completed):**
```json
{
  "data": {
    "id": "e66d7d067cd7c84582dc",
    "status": "terminated",
    "credits_consumed": 1,
    "credits_left": "34.0",
    "data": [
      {
        "enriched": true,
        "contact_email_address": "john.doe@acme.com",
        "contact_phone_number": "+1 555-123-4567",
        "contact_full_name": "John Doe",
        "company_name": "Acme Corp",
        // ... additional enrichment data
      }
    ]
  }
}
```

### 3. Enrich Lead (Sync) Module

**Purpose:** Synchronously enrich a lead with automatic polling for results.

**Endpoint:** `/enrich_lead_sync/v1/execute`

**Input Fields:** Same as Enrich Lead module

**Features:**
- Automatically submits the lead and polls for results
- Smart polling: starts at 2-second intervals, increases up to 5 seconds
- 45-second timeout with helpful error message
- Returns full enrichment data when complete

**Example Request:**
```json
{
  "data": {
    "linkedin_url": "https://linkedin.com/in/johndoe",
    "company_domain": "acme.com",
    "enrich_email_address": true,
    "enrich_phone_number": false
  }
}
```

**Example Response:**
```json
{
  "data": {
    "id": "98a4f271f32f1068d43c",
    "status": "terminated",
    "credits_consumed": 1,
    "data": [
      {
        "enriched": true,
        "contact_email_address": "john@acme.com",
        "contact_linkedin_profile_url": "https://linkedin.com/in/johndoe",
        // ... full enrichment data
      }
    ]
  },
  "metadata": {
    "request_id": "98a4f271f32f1068d43c",
    "processing_time_seconds": 12.5,
    "poll_attempts": 6,
    "status": "completed"
  }
}
```

## 🔐 Authentication

The connector supports API key authentication. In production, the API key should be provided through the StackSync connection object. For testing, you can use the hardcoded test key in the `.env` file.

## ⚡ Validation Rules

### Clay-Style Logic:
1. **Person Identification:**
   - If LinkedIn URL is provided → Names are optional
   - If LinkedIn URL is NOT provided → Both first and last names are required

2. **Company Identification:**
   - If company domain is provided → Company name is optional
   - If company domain is NOT provided → Company name is required

### Error Messages:
- "First name and last name are required when LinkedIn URL is not provided"
- "Company name is required when company domain is not provided"
- "Invalid API key or unauthorized access"
- "Enrichment timeout after 45 seconds. Request ID: [id]"

## 🧪 Testing

### Local Testing with curl:

1. **Test Enrich Lead:**
```bash
curl -X POST http://localhost:2003/enrich_leads/v1/execute \
-H "Content-Type: application/json" \
-d '{
  "data": {
    "first_name": "John",
    "last_name": "Doe",
    "company": "Microsoft"
  }
}'
```

2. **Test Get Results:**
```bash
curl -X POST http://localhost:2003/get_enrichment_results/v1/execute \
-H "Content-Type: application/json" \
-d '{
  "data": {
    "request_id": "YOUR_REQUEST_ID_HERE"
  }
}'
```

3. **Test Sync Enrichment:**
```bash
curl -X POST http://localhost:2003/enrich_lead_sync/v1/execute \
-H "Content-Type: application/json" \
-d '{
  "data": {
    "linkedin_url": "https://linkedin.com/in/example",
    "company_domain": "example.com"
  }
}'
```

### Testing with ngrok:

1. **Install ngrok:**
   ```bash
   brew install ngrok
   ```

2. **Start ngrok tunnel:**
   ```bash
   ngrok http 2003
   ```

3. **Use the ngrok URL in StackSync Workflows**

## 🚨 Error Handling

The connector implements comprehensive error handling:

- **Network Errors:** Timeout and connection errors with descriptive messages
- **API Errors:** 400, 401, 404, 406 status codes handled appropriately
- **Validation Errors:** Clear messages for missing required fields
- **Timeout Handling:** Returns request ID for manual checking after timeout

## 📈 Performance Considerations

- **Polling Strategy:** Progressive delays from 2 to 5 seconds
- **Timeout:** 45 seconds for synchronous module
- **Request Limits:** BetterContact API supports up to 200 leads per batch (currently configured for single lead)

## 🐛 Troubleshooting

### Common Issues:

1. **406 "Not Acceptable" Error:**
   - Usually occurs when checking results too quickly
   - The connector now includes a 1-second initial delay

2. **Timeout Errors:**
   - Normal for leads that take longer to enrich
   - Use the provided request ID to check results later

3. **Container Port Issues:**
   ```bash
   # Check if port is in use
   docker ps | grep 2003
   
   # Stop existing container
   docker stop bettercontact-connector
   docker rm bettercontact-connector
   ```

### Debug Mode:

Check container logs:
```bash
docker logs bettercontact-connector --tail 50
```

## 📄 License

This connector is provided as-is for use with StackSync Workflows and BetterContact API.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For issues related to:
- **This connector:** Open an issue on GitHub
- **BetterContact API:** Contact BetterContact support
- **StackSync Workflows:** Contact StackSync support

---

Built with ❤️ for StackSync Workflows