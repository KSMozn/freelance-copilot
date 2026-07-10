FROM node:22-alpine

WORKDIR /app

# npm ci honors package-lock.json exactly — the dev container runs the same
# dependency set CI and Dockerfile.prod verify (npm install could drift).
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev"]
