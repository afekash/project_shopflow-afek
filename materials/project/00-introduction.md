# ShopFlow — Project Introduction

## The Business

ShopFlow is an online retailer that sells five product categories: **electronics, clothing, books, food, and home goods**.

Customers browse a product catalog, place orders, and receive a confirmation. Sellers manage inventory. The business tracks what was sold, at what price, to whom — and wants to use that history to improve the customer experience.

The company has grown from a handful of products and a few dozen daily orders to tens of thousands of products and hundreds of thousands of orders per month. The data problems they face have grown with them.

---

## Why You Are Here

ShopFlow's engineering team has built a web API that accepts customer requests and routes them to the right data operation. That API is already running — you can open it in a browser, see every endpoint, and call it.

But the API returns `501 Not Implemented` for every operation. Nothing is actually stored or retrieved yet. The data layer — the code that talks to databases — has been left for you to implement.

Your job over this project is to build that data layer, phase by phase, as the business demands it.

---

## How the Project Works

The API is structured around a single class called `DBAccess`. Every web request ends up calling one method on this class. You implement those methods. The API calls them. The tests verify them.

You will not touch the web layer. You will not write HTTP handlers, parse request bodies, or format JSON responses. That's all done for you. You write Python functions that read from and write to databases.

---

## The Story

ShopFlow is preparing to launch. The engineering team has three months before the first customers arrive, and a simple mandate: **make it work, make it correct, then make it fast**.

What "work" means will change as the business grows. Each phase of this project introduces a new set of business demands — things the system cannot currently do — and you will design and implement the solution.

The questions you will face are not "how do I write this query." The questions are:

- Where does this data belong?
- What guarantees does this operation need?
- What happens when the business has ten times as many products and orders?
- Is this storage choice still correct at that scale, or does it break?

Work through each phase in order. The problems in Phase 2 only exist because the system from Phase 1 is running.
