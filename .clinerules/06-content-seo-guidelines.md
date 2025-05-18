# Content Marketing & SEO Guidelines

## Overview

This document outlines the structure, guidelines, and processes for managing Pathlight's content marketing and SEO strategy. It covers the organization of blog posts, guides, and FAQ content, as well as the implementation of tracking codes for analytics platforms.

## Directory Structure

```
app/
├── templates/
│   ├── tracking_head.html       # Analytics code for <head> section
│   ├── tracking_body.html       # Analytics code for end of <body>
│   ├── blog/
│   │   ├── index.html           # Blog listing page
│   │   ├── post_template.html   # Template for individual posts
│   │   └── posts/               # Individual blog post content files
│   │       └── [post-slug].html # e.g., finding-your-purpose.html
│   ├── guides/
│   │   ├── index.html           # Guides listing page
│   │   ├── guide_template.html  # Template for individual guides
│   │   └── items/               # Individual guide content files
│   │       └── [guide-slug].html # e.g., purpose-discovery-process.html
│   └── faq/
│       ├── index.html           # Main FAQ page with all questions
│       └── categories/          # Category-specific FAQ pages
│           └── [category].html  # e.g., methodology.html
├── static/
│   ├── robots.txt               # Instructions for search engines
│   └── sitemap.xml              # XML sitemap for search engines
└── routers/
    └── web.py                   # Routes for content pages
```

## Analytics Integration

### Tracking Codes

Pathlight uses three main analytics platforms:

1. **Google Analytics (GA4)** - For general website analytics and user behavior tracking
2. **Google Search Console** - For monitoring search performance and indexing issues
3. **Microsoft Clarity** - For heatmaps, session recordings, and user experience insights

These tracking codes are implemented through template files:

- `tracking_head.html` - Contains code snippets that need to be in the `<head>` section
- `tracking_body.html` - Contains code snippets that need to be at the end of the `<body>` section

The base template (`base.html`) includes these files using Jinja2's include directive:

```html
<!-- In <head> section -->
{% include 'tracking_head.html' %}

<!-- At end of <body> section -->
{% include 'tracking_body.html' %}
```

### Updating Tracking Codes

To update tracking codes:

1. Edit the appropriate template file (`tracking_head.html` or `tracking_body.html`)
2. Replace the placeholder IDs with actual tracking IDs
3. Add any additional tracking code as needed

## Content Management

### Adding a New Blog Post

1. Create a new HTML file in `app/templates/blog/posts/` with a SEO-friendly filename (e.g., `why-purpose-matters.html`)
2. Extend the post template and set required variables:

```html
{% extends "blog/post_template.html" %}

{% set title = "Your Post Title" %}
{% set description = "SEO description of your post (150-160 characters)" %}
{% set keywords = "keyword1, keyword2, keyword3" %}
{% set image_url = "/static/images/your-image.png" %}
{% set published_date = "YYYY-MM-DD" %}
{% set modified_date = "YYYY-MM-DD" %}
{% set author = "Author Name" %}
{% set category = "Category Name" %}
{% set tags = ["tag1", "tag2", "tag3"] %}
{% set related_posts = [
    {
        "title": "Related Post Title",
        "image_url": "/static/images/related-image.png",
        "url": "/blog/posts/related-post-slug"
    }
] %}

{% block post_content %}
<!-- Your post content here -->
<h2>First Section Heading</h2>
<p>Your content paragraphs...</p>
{% endblock %}
```

3. Update `sitemap.xml` to include the new post URL

### Adding a New Guide

1. Create a new HTML file in `app/templates/guides/items/` with a SEO-friendly filename (e.g., `finding-your-strengths.html`)
2. Extend the guide template and set required variables:

```html
{% extends "guides/guide_template.html" %}

{% set title = "Your Guide Title" %}
{% set description = "SEO description of your guide (150-160 characters)" %}
{% set keywords = "keyword1, keyword2, keyword3" %}
{% set image_url = "/static/images/your-image.png" %}
{% set difficulty = "Beginner" %}  <!-- Beginner, Intermediate, or Advanced -->
{% set time_minutes = 20 %}  <!-- Estimated reading/completion time -->
{% set category = "Category Name" %}
{% set introduction = "Brief introduction to your guide..." %}
{% set tags = ["tag1", "tag2", "tag3"] %}
{% set steps = [
    {
        "name": "Step 1 Title",
        "text": "Brief description of step 1"
    },
    {
        "name": "Step 2 Title",
        "text": "Brief description of step 2"
    }
] %}
{% set resources = [
    {
        "title": "Resource Title",
        "description": "Resource description",
        "url": "#",
        "link_text": "Access Resource"
    }
] %}
{% set related_guides = [
    {
        "title": "Related Guide Title",
        "image_url": "/static/images/related-image.png",
        "url": "/guides/items/related-guide-slug"
    }
] %}

{% block guide_content %}
<!-- Your guide content here -->
<h2>First Section Heading</h2>
<p>Your content paragraphs...</p>

<div id="step-1" class="step-container">
    <div class="step-header">
        <div class="step-number">1</div>
        <h3 class="step-title">Step 1 Title</h3>
    </div>
    <div class="step-content">
        <p>Step 1 content...</p>
    </div>
</div>
{% endblock %}
```

3. Update `sitemap.xml` to include the new guide URL

### Adding a New FAQ Category

1. Create a new HTML file in `app/templates/faq/categories/` with a category name (e.g., `technical.html`)
2. Extend the base template and follow the structure of existing FAQ category pages
3. Update `sitemap.xml` to include the new FAQ category URL

## SEO Best Practices

### Meta Tags

Each content page should include:

- Title tag (unique, 50-60 characters)
- Meta description (unique, 150-160 characters)
- Meta keywords (relevant to the content)
- Open Graph tags (for social sharing)
- Twitter Card tags (for Twitter sharing)
- Schema.org markup (for rich search results)

### URL Structure

Follow these URL patterns for content:

- Blog posts: `/blog/posts/[post-slug]`
- Guides: `/guides/items/[guide-slug]`
- FAQ categories: `/faq/categories/[category]`

Use descriptive, keyword-rich slugs separated by hyphens.

### Sitemap Updates

When adding new content, update `app/static/sitemap.xml` to include the new URLs:

```xml
<url>
  <loc>https://followpathlight.com/[path]</loc>
  <lastmod>YYYY-MM-DD</lastmod>
  <changefreq>monthly</changefreq>
  <priority>0.7</priority>
</url>
```

### AI Language Guidelines

When referring to Pathlight's technology in marketing materials and content, follow these guidelines:

1. **De-emphasize AI references**: Avoid highlighting AI as a primary feature in marketing materials, meta descriptions, and general content. It's not a secret, but we don't want to call attention to it.

2. **Preferred terminology**: Instead of "AI-powered" or direct AI references, use these alternatives:
   - "Research-backed purpose discovery tool"
   - "Purpose discovery process that combines philosophical wisdom with modern technology"
   - "Technology-enhanced analysis"
   - "Purpose insights drawn from human experience and philosophical wisdom"
   - "Human wisdom-guided purpose discovery process"

3. **FAQ content**: It's acceptable to mention AI in the FAQ section, but still prefer terms like:
   - "Combines human wisdom with technology"
   - "Our system analyzes patterns" (instead of "Our AI analyzes")
   - "Processing costs" (instead of "AI processing costs")
   - "Technology processing" (instead of "AI processing")

4. **Emphasize human elements**: Focus on how our technology manifests the wisdom and research of human philosophy, psychology, and experience, rather than on the AI technology itself.

5. **Schema.org markup**: In structured data, use descriptions like "Purpose discovery tool that combines human wisdom and research" rather than mentioning AI directly.

## Navigation

The main navigation and footer have been updated to include links to the new content sections:

- Blog
- Guides
- Research
- FAQ

This ensures users can easily discover and access all content areas.

## Maintenance

Regularly review and update:

1. Analytics tracking codes when new features are needed
2. Content for accuracy and relevance
3. SEO metadata for optimization opportunities
4. Sitemap.xml when adding or removing content
5. robots.txt if crawling directives need to change
