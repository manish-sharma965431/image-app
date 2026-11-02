# Image Vision API

A secure REST API for image processing, built with **FastAPI** and **MongoDB**. Users register, log in, upload images, and then watermark them, classify the room type, or remove a watermark.

## Features

- **Authentication:** JWT (bcrypt-hashed passwords), enforced by middleware
- **Add watermark:** text watermark with adjustable opacity (Pillow)
- **Room classification:** zero-shot classification with CLIP (Bedroom, Kitchen, Drawing Area, Bathroom, and more). Labels are easy to edit.
- **Watermark removal:** OpenCV inpainting with a region and mask mode (`bright` or `box`)
- **Image storage:** files on local disk; filename, CDN URL, created date and processed date stored in MongoDB
- **Request logging:** request time, response time and status for every call, with a request ID
- **Centralized error handling:** one consistent JSON error format
- **CORS:** configurable allowed origins

## Tech stack

| Area | Tools |
|---|---|
| API | FastAPI, Uvicorn, Pydantic |
| Database | MongoDB (PyMongo async client) |
| Auth | PyJWT, bcrypt |
| Image processing | Pillow, OpenCV, NumPy |
| ML | PyTorch, Hugging Face Transformers (CLIP) |

## Architecture

The project follows an MVC-style layered structure:

```
app/
├── main.py            # app setup, middleware order, routers
├── routes/            # HTTP layer (thin)
├── controllers/       # business logic, step order, ownership checks
├── services/          # file handling, Pillow, OpenCV, CLIP
├── models/            # MongoDB access
├── schemas/           # Pydantic request/response shapes (the "view")
├── middleware/        # JWT auth, request logging
├── core/              # config, security, logger, exceptions
└── db/                # Mongo connection
```

Request flow: `CORS -> logging -> auth -> route -> controller -> service / model`

## Getting started

### Requirements
- Python 3.12+
- MongoDB (local 7.0, or a free MongoDB Atlas cluster)

### Setup
```bash
git clone [your-repo-url]
cd [repo-folder]
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
```
JWT_SECRET=<generate with: python -c "import secrets; print(secrets.token_urlsafe(48))">
MONGO_URI=mongodb://localhost:27017
MONGO_DB=image_app
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
CDN_BASE_URL=https://cdn.example.com/images
CLASSIFIER_MODEL=openai/clip-vit-base-patch32
```

### Run
```bash
uvicorn app.main:app --reload
```
Open **http://localhost:8000/docs**, register, log in, click **Authorize** and paste the token.

The first classification call downloads the CLIP model, so it is slow once.

## API endpoints

All routes are under `/api/v1` and need a Bearer token unless marked public.

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create an account (public) |
| POST | `/auth/login` | Get a JWT (public) |
| GET | `/auth/me` | Current user |
| POST | `/images` | Upload an image |
| GET | `/images` | List your images (pagination) |
| GET | `/images/{id}` | Image details |
| GET | `/images/{id}/file?variant=original\|processed\|cleaned` | Download a file |
| POST | `/images/{id}/watermark` | Add a text watermark |
| POST | `/images/{id}/classify?top_k=3` | Classify the room type |
| POST | `/images/{id}/remove-watermark` | Remove a watermark from a region |
| DELETE | `/images/{id}` | Delete an image and its files |

### Example: remove a watermark
```json
{
  "x": 580, "y": 590, "width": 420, "height": 110,
  "mode": "bright",
  "confirm_ownership": true
}
```

### Error format
```json
{ "error": { "code": "not_found", "message": "Image not found", "details": null, "request_id": "a1b2c3d4e5f6" } }
```

## Security notes

- Passwords are hashed with bcrypt, and login errors don't reveal whether an email exists
- Uploads are validated by image content, limited in size, and saved under server-generated names
- Users can only access their own images (other users' IDs return 404)
- Secrets live in `.env`, which is not committed
- Watermark removal requires `confirm_ownership: true`. Only edit images you own or have permission to edit.

## Limitations

- Inpainting works best on small watermarks over smooth backgrounds. Large opaque logos can't be recovered.
- Classification only knows the labels in `ROOM_LABELS` and can be wrong on close-ups
- Files are stored on local disk, which isn't suitable for multiple servers

## Roadmap

- [ ] Image enhance / deblur endpoint
- [ ] Pytest test suite
- [ ] Docker and docker-compose
- [ ] Rate limiting on login
- [ ] Background job queue for heavy processing
- [ ] LangChain agent for natural-language control

## Author

[Your name], [LinkedIn or portfolio link]