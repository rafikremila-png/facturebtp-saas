# BTP Facture - SaaS Invoicing Platform

A complete SaaS invoicing platform for French construction companies (BTP).

## 🚀 Production Deployment on Render

### URLs
- **Backend API**: https://facturebtp-saas.onrender.com
- **Frontend App**: https://facturebtp-app.onrender.com
- **API Documentation**: https://facturebtp-saas.onrender.com/docs

---

## 📁 Project Structure

```
project-root/
├── backend/                    # FastAPI Backend
│   ├── server.py              # Main API server
│   ├── requirements.txt       # Python dependencies
│   ├── .env                   # Environment variables
│   └── app/
│       └── services/          # Business logic services
│
├── frontend/                   # React Frontend
│   ├── public/
│   │   ├── index.html
│   │   └── _redirects         # Render SPA routing
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── context/
│   │   └── lib/
│   ├── .env.production
│   └── package.json
│
├── render.yaml                # Render deployment config
└── README.md
```

---

## 🔧 Render Deployment Configuration

### Backend Service (Web Service)
| Setting | Value |
|---------|-------|
| **Name** | facturebtp-saas |
| **Runtime** | Python 3 |
| **Root Directory** | `backend` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn server:app --host 0.0.0.0 --port $PORT` |

### Frontend Service (Static Site)
| Setting | Value |
|---------|-------|
| **Name** | facturebtp-app |
| **Root Directory** | `frontend` |
| **Build Command** | `npm install --legacy-peer-deps && npm run build` |
| **Publish Directory** | `build` |

### Environment Variables (Backend)
```
MONGO_URL=mongodb+srv://...
JWT_SECRET=your-secure-secret
ENVIRONMENT=production
CORS_ORIGINS=https://facturebtp-app.onrender.com
FRONTEND_URL=https://facturebtp-app.onrender.com
STRIPE_API_KEY=sk_live_...
```

### Environment Variables (Frontend)
```
REACT_APP_BACKEND_URL=https://facturebtp-saas.onrender.com
```

---

## 🔄 React Router Fix

The `_redirects` file in `frontend/public/` ensures React Router works:
```
/* /index.html 200
```

---

## 🎯 Features

- Company & Client Management
- Quote & Invoice System
- PDF Generation
- Stripe Subscription Billing
- User Roles (admin, user)
- Admin Dashboard with Metrics

---

## 📊 Subscription Plans

| Plan | Monthly | Limits |
|------|---------|--------|
| Essentiel | 19€ | 30/month, 1 user |
| Pro | 29€ | Unlimited, 3 users |
| Business | 59€ | Unlimited, 5 users |
