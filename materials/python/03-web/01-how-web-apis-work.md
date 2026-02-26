# How Web APIs Work

You've spent this course working with databases directly -- connecting, querying, closing. But in a real application, database calls are triggered by HTTP requests from a client. Before writing any FastAPI code, let's understand the model it's built on.

## The Client-Server Model

A web API is a program that listens on a network address for incoming requests and sends back responses. The client (a browser, a mobile app, a test script) speaks the same language as the server: HTTP.

```
┌──────────────────────┐                    ┌────────────────────────┐
│  Client              │   HTTP Request      │  Server (FastAPI)      │
│                      │  ─────────────────▶ │                        │
│  - Browser           │                    │  Receives the request  │
│  - Swagger UI        │   HTTP Response     │  Calls your Python fn  │
│  - Test script       │  ◀───────────────── │  Returns the result    │
└──────────────────────┘                    └────────────────────────┘
```

Every request specifies two things:

- **Method** -- the type of action. `GET` reads data, `POST` creates data. That's all you need to know for this project.
- **Path** -- the URL path that identifies the resource, like `/products` or `/orders/42`.

## Endpoints

An **endpoint** is the combination of a method and a path. `GET /products` and `POST /products` are two different endpoints even though they share a path.

In FastAPI, each endpoint maps to exactly one Python function. When the server receives `GET /products`, it calls your function and returns what the function returns. The whole job of a web framework is to make that wiring easy.

## HTTP Status Codes

Every response carries a numeric status code:

| Code | Meaning |
|------|---------|
| `200` | OK -- request succeeded |
| `201` | Created -- a new resource was created |
| `404` | Not Found -- the resource doesn't exist |
| `422` | Unprocessable -- the request body failed validation |

You'll see these in Swagger UI and in test assertions. FastAPI sets the right code automatically based on what you return or what exception you raise -- you won't write status-code logic yourself.

## JSON: The Data Format

Requests and responses carry data as JSON -- the same format you've used throughout this course with MongoDB. A client sends a JSON body when creating a resource; the server responds with a JSON body representing the result.

```
POST /orders
Content-Type: application/json

{
  "customer_id": 7,
  "items": [
    { "product_id": 1, "quantity": 2 },
    { "product_id": 3, "quantity": 1 }
  ]
}
```

The server parses that JSON into Python objects, calls your function, and serializes the return value back to JSON for the response.

## Summary

| Concept | Meaning |
|---------|---------|
| HTTP method | The action type: `GET` reads, `POST` creates |
| Path | The URL segment that identifies a resource |
| Endpoint | A method + path pair, mapped to one Python function |
| Status code | Numeric result: 200 OK, 404 Not Found, etc. |
| JSON | The data format for both requests and responses |

**Navigation:**
- **Next**: [FastAPI Routes →](02-fastapi-routes.md)
- **Home**: [Web APIs Module](README.md)
