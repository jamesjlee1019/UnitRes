FROM node:24-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . .

# npm install first picks up any packages someone added since you last started
CMD ["sh", "-c", "npm install --no-audit --no-fund && npm run dev"]
