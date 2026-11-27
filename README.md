# News Platform

A full-stack Django news and publishing platform with role-based access, article moderation, social interactions, REST API support, Redis caching, PostgreSQL, Docker, and automated tests.

The project is designed around a complete publishing workflow: a registered user can become an author, create a draft, submit it for moderation, and publish it after staff approval. Readers can browse published articles, search and filter content, like articles, save bookmarks, and participate in discussions.

## Features

### Accounts and roles

The platform supports several access levels:

- **Guest** — can browse published articles and use search/filtering.
- **Registered user** — can manage a profile, like articles, save bookmarks, and comment.
- **Author** — has all registered-user capabilities and can create, edit, submit, and manage their own articles.
- **Staff** — can review submitted articles and approve or reject them.

Authentication supports login with either a **username or email address**.

### Article workflow

Articles follow a controlled moderation lifecycle:

```text
Draft
  ↓
Submitted
  ↓
Moderation
  ├── Published
  └── Rejected
        ↓
      Edit and resubmit
```

Authors can:

- create articles as drafts;
- add a title, slug, summary, body, cover image, categories, and tags;
- edit drafts and rejected articles;
- submit articles for moderation;
- delete their own articles;
- view the current status of each article.

Staff users can:

- access the moderation queue;
- review submitted content;
- publish or reject an article;
- leave a moderation comment;
- preserve moderation history.

### Reader interactions

Authenticated readers can:

- like and unlike published articles;
- save and remove bookmarks;
- add comments;
- edit their own comments;
- delete their own comments;
- view author profiles.

Likes, bookmarks, and comments are updated through the REST API without requiring a full page reload.

### Search and discovery

The article feed supports:

- text search;
- category filtering;
- tag filtering;
- API-backed live updates;
- pagination.

Only published articles are exposed publicly.

### Author profiles

Author pages include:

- profile information;
- specialization and portfolio link when available;
- published articles;
- total published article count;
- total likes;
- total comments.

## UI

The interface uses a responsive editorial/social design with:

- featured article layouts;
- article cover images;
- responsive article grids;
- dedicated reading views;
- profile and author pages;
- styled authentication and editing forms;
- moderation screens;
- bookmarks;
- comments and reaction controls;
- custom error pages.

The frontend is implemented with Django templates, CSS, and vanilla JavaScript.

## REST API

The project includes a Django REST Framework API.

Main endpoints:

```text
/api/articles/
/api/categories/
/api/tags/
/api/comments/
```

JWT authentication:

```text
/api/token/
/api/token/refresh/
```

API documentation:

```text
/api/docs/
/api/schema/
```

The API enforces the same core business rules as the web interface, including article visibility, author permissions, published-article restrictions, comment ownership, and draft protection.

## Technology stack

### Backend

- Python 3.14
- Django 6.1.2
- Django REST Framework 3.18.3
- SimpleJWT
- django-filter
- drf-spectacular

### Database and infrastructure

- PostgreSQL 17
- Redis 8
- Docker
- Docker Compose
- WhiteNoise

### Frontend

- Django Templates
- HTML5
- CSS3
- Vanilla JavaScript

### Development and quality

- Django Debug Toolbar
- Django test framework
- DRF test utilities
- GitHub Actions

## Project structure

```text
news-platform/
├── accounts/
│   ├── migrations/
│   ├── templates/
│   ├── backends.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── articles/
│   ├── migrations/
│   ├── templates/
│   ├── api_permissions.py
│   ├── api_views.py
│   ├── filters.py
│   ├── forms.py
│   ├── models.py
│   ├── serializers.py
│   ├── signals.py
│   ├── tests.py
│   ├── tests_system.py
│   ├── urls.py
│   └── views.py
│
├── interactions/
│   ├── migrations/
│   ├── templates/
│   ├── api_permissions.py
│   ├── api_views.py
│   ├── forms.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── core/
│   ├── api_urls.py
│   ├── middleware.py
│   ├── settings.py
│   ├── urls.py
│   ├── views.py
│   ├── asgi.py
│   └── wsgi.py
│
├── static/
│   ├── css/
│   └── js/
│
├── templates/
│   ├── errors/
│   └── base.html
│
├── .github/
│   └── workflows/
│       └── tests.yml
│
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── manage.py
└── requirements.txt
```

### Application responsibilities

`accounts` contains authentication, the custom user model, profiles, author profiles, and the username-or-email authentication backend.

`articles` contains the publishing domain: articles, categories, tags, moderation, article permissions, API endpoints, filters, serializers, and the publication workflow.

`interactions` contains reader activity such as comments, likes, and bookmarks.

`core` contains project-level configuration, routing, middleware, API routing, and custom error handlers.

This keeps account, publishing, interaction, and project infrastructure concerns separated into independent Django applications.

## Local setup

### Requirements

Install:

- Docker
- Docker Compose
- Git

Clone the repository:

```bash
git clone https://github.com/sali-sultanova1/blog-prog.git
cd blog-prog
```

Create the local environment file:

```bash
cp .env.example .env
```

The default `.env.example` is configured for local development.

Build and start the services:

```bash
docker compose up -d --build
```

Apply database migrations:

```bash
docker compose exec web python manage.py migrate
```

Create an administrator account:

```bash
docker compose exec web python manage.py createsuperuser
```

The application is then available at:

```text
http://localhost:8000/
```

Django admin:

```text
http://localhost:8000/admin/
```

Swagger API documentation:

```text
http://localhost:8000/api/docs/
```

## Environment variables

The project reads configuration from `.env`.

Example:

```env
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=blog_db
POSTGRES_USER=blog_user
POSTGRES_PASSWORD=change-me
POSTGRES_HOST=db
POSTGRES_PORT=5432

REDIS_URL=redis://redis:6379/1

EMAIL_HOST_USER=your-email@yahoo.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@yahoo.com
```

The real `.env` file is ignored by Git and must not be committed.

## Testing

The repository contains **23 automated tests** covering unit, integration, API, authentication, permission, and workflow behaviour.

The suite currently includes:

- 2 authentication tests;
- 7 article/web integration tests;
- 11 REST API integration tests;
- 2 serializer unit tests;
- 1 complete publishing workflow system test.

Run the complete suite with:

```bash
docker compose exec web python manage.py test
```

Other useful checks:

```bash
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web python manage.py migrate --check
```

## Continuous integration

GitHub Actions is configured in:

```text
.github/workflows/tests.yml
```

On every push and pull request, the workflow:

1. checks out the repository;
2. creates `.env` from `.env.example`;
3. builds the Docker web image;
4. starts PostgreSQL and Redis;
5. runs the Django test suite.

## Static and media files

Static assets are stored in:

```text
static/
```

WhiteNoise is configured for collected static files, and Docker runs `collectstatic` before starting the development server.

User-uploaded files such as avatars and article cover images are stored under `media/`. The `media/` directory is intentionally excluded from Git.

For a production deployment, user-uploaded media should be served by a dedicated web server or object-storage service.

## Security notes

Secrets are loaded through environment variables and the real `.env` file is excluded from version control.

Production deployment should use:

```env
DJANGO_DEBUG=False
```

and should additionally configure HTTPS-related Django security settings, secure cookies, production host names, and production-grade media hosting.

The Docker Compose configuration in this repository is intended primarily for local development and project demonstration.

## Error handling

The project defines custom pages for:

- `400 Bad Request`
- `403 Forbidden`
- `404 Not Found`
- `500 Internal Server Error`

Templates are located in:

```text
templates/errors/
```

## License

This project was created as an educational final project.
