# PRD — AI-Guided Product Data Automation Tool (AWS MVP)

## 1. Overview

This project is a lightweight, cloud-based tool that automates the transformation of supplier product data into Shopify-ready listings.

It combines:
- deterministic data processing (normalisation + validation)
- AI-assisted content enhancement (description, tags, SEO)
- a simple web interface for non-technical users

---

## 2. Problem Statement

Supplier product data is often inconsistent, incomplete, and requires manual cleaning.

Challenges:
- inconsistent data structure
- missing required fields
- manual formatting is time-consuming
- product descriptions lack quality
- risk of upload errors

---

## 3. Target Users

- small e-commerce business owners
- admin/operations staff
- marketers preparing product listings

---

## 4. Goals

### Product Goals
- reduce manual effort
- standardise product data
- improve content quality using AI

### Technical Goals
- demonstrate automation workflow
- implement structured AI usage
- deploy on AWS

---

## 5. Core Concept

Input → Clean → Validate → AI Enhance → Review → Export

---

## 6. Core Features

### Data Input
- Upload CSV/JSON

### Normalisation
- standardise product fields

### Validation
- missing fields
- invalid formats

### AI Enhancement
- description
- tags
- SEO

### Review UI
- preview results
- show warnings

### Export
- Shopify CSV

---

## 7. User Flow

Upload → Process → Validate → AI → Review → Download

---

## 8. Non-Goals

- full inventory system
- complex UI
- multi-platform publishing

---

## 9. Tech Stack

- Python
- AWS Lambda
- API Gateway
- S3
- CloudFront
- LLM API

---

## 10. Success Criteria

- valid CSV output
- improved descriptions
- reduced manual work
- working AWS deployment

---

## 11. Principle

Code handles structure  
AI enhances content  
Validate everything
