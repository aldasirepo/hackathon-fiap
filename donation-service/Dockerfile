# syntax=docker/dockerfile:1

# --- Build Stage ---
FROM golang:1.22-alpine AS builder

WORKDIR /app

RUN apk add --no-cache git

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o donation-service .

# --- Final Stage ---
FROM gcr.io/distroless/static-debian12

WORKDIR /app

COPY --from=builder /app/donation-service .

EXPOSE 8082
ENV PORT=8082

USER nonroot:nonroot

ENTRYPOINT ["/app/donation-service"]
