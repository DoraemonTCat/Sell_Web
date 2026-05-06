# ===========================================
# Frontend Dockerfile — React + Vite
# Node 20 Alpine for minimal image size
# ===========================================
FROM node:20-alpine

WORKDIR /app

# Install dependencies first (better Docker cache)
COPY package.json package-lock.json* ./
RUN npm install

# Copy application code
COPY . .

EXPOSE 5173

# Run Vite dev server accessible from Docker network
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
