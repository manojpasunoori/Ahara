FROM node:24-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

FROM node:24-alpine AS runner
ENV NODE_ENV=production
WORKDIR /app
RUN addgroup -S ahara && adduser -S ahara -G ahara
COPY --from=builder --chown=ahara:ahara /app /app
USER ahara
EXPOSE 3000
CMD ["npm", "start"]